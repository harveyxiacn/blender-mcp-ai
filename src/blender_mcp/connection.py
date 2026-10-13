"""
Blender Connection Module

Manages socket communication with the Blender addon, supporting auto-reconnection and heartbeat detection.
"""

import asyncio
import contextlib
import json
import logging
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
HEARTBEAT_INTERVAL = 15.0
HEARTBEAT_TIMEOUT = 5.0
RECONNECT_BACKOFF_BASE = 1.0
RECONNECT_BACKOFF_MAX = 30.0
READ_BUFFER_SIZE = 65536


class BlenderConnectionError(Exception):
    """Blender connection error"""

    pass


class BlenderConnection:
    """Blender Socket Connection Manager

    Responsible for:
    - Establishing and maintaining the socket connection to the Blender addon
    - Sending commands and receiving responses
    - Heartbeat detection and auto-reconnection
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        auto_reconnect: bool = True,
        heartbeat_interval: float = HEARTBEAT_INTERVAL,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.max_retries = max_retries
        self.auto_reconnect = auto_reconnect
        self.heartbeat_interval = heartbeat_interval

        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._lock = asyncio.Lock()

        self._pending_requests: dict[str, asyncio.Future] = {}
        self._read_task: asyncio.Task | None = None
        self._heartbeat_task: asyncio.Task | None = None

        self._last_activity: float = 0.0
        self._reconnect_count: int = 0
        self._total_commands: int = 0
        self._failed_commands: int = 0

    @property
    def connected(self) -> bool:
        return self._connected and self._writer is not None

    @property
    def stats(self) -> dict[str, Any]:
        """Connection statistics"""
        return {
            "connected": self.connected,
            "host": self.host,
            "port": self.port,
            "reconnect_count": self._reconnect_count,
            "total_commands": self._total_commands,
            "failed_commands": self._failed_commands,
            "pending_requests": len(self._pending_requests),
            "last_activity": self._last_activity,
        }

    async def connect(self) -> None:
        """Establish connection"""
        async with self._lock:
            if self._connected:
                return

            for attempt in range(self.max_retries):
                try:
                    logger.info(
                        f"Connecting to Blender: {self.host}:{self.port} (attempt {attempt + 1}/{self.max_retries})"
                    )

                    self._reader, self._writer = await asyncio.wait_for(
                        asyncio.open_connection(self.host, self.port), timeout=5.0
                    )

                    self._connected = True
                    self._last_activity = time.monotonic()

                    self._read_task = asyncio.create_task(self._read_responses())

                    if self.heartbeat_interval > 0:
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                    logger.info("Blender connection established")
                    return

                except asyncio.TimeoutError:
                    logger.warning(f"Connection timed out (attempt {attempt + 1})")
                except ConnectionRefusedError:
                    logger.warning(f"Connection refused (attempt {attempt + 1})")
                except Exception as e:
                    logger.warning(f"Connection failed: {e} (attempt {attempt + 1})")

                if attempt < self.max_retries - 1:
                    backoff = min(RECONNECT_BACKOFF_BASE * (2**attempt), RECONNECT_BACKOFF_MAX)
                    await asyncio.sleep(backoff)

            raise BlenderConnectionError(
                f"Cannot connect to Blender ({self.host}:{self.port}). "
                "Please ensure Blender is running and the MCP addon is enabled."
            )

    async def disconnect(self) -> None:
        """Disconnect"""
        async with self._lock:
            await self._cleanup()
            logger.info("Blender connection disconnected")

    async def _cleanup(self) -> None:
        """Clean up connection resources (caller must hold _lock)"""
        self._connected = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._heartbeat_task
            self._heartbeat_task = None

        if self._read_task:
            self._read_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._read_task
            self._read_task = None

        if self._writer:
            self._writer.close()
            with contextlib.suppress(Exception):
                await self._writer.wait_closed()
            self._writer = None

        self._reader = None

        for future in self._pending_requests.values():
            if not future.done():
                future.set_exception(BlenderConnectionError("Connection closed"))
        self._pending_requests.clear()

    async def _reconnect(self) -> bool:
        """Attempt to reconnect (called without holding the lock)"""
        if not self.auto_reconnect:
            return False

        logger.info("Attempting auto-reconnect...")
        self._reconnect_count += 1

        async with self._lock:
            await self._cleanup()

        try:
            await self.connect()
            return True
        except BlenderConnectionError:
            logger.warning("Auto-reconnect failed")
            return False

    async def _heartbeat_loop(self) -> None:
        """Periodically send heartbeats to detect connection liveness"""
        while self._connected:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if not self._connected:
                    break

                idle = time.monotonic() - self._last_activity
                if idle < self.heartbeat_interval:
                    continue

                # Blender executes commands on its main thread, so a long render
                # or export blocks the addon from answering system.get_info until
                # it returns. While a command is still outstanding the link is
                # plainly alive: probing then would only time out and tear down a
                # perfectly healthy connection.
                if any(not rid.startswith("heartbeat-") for rid in self._pending_requests):
                    continue

                request_id = f"heartbeat-{uuid.uuid4().hex[:8]}"
                request = {
                    "id": request_id,
                    "type": "command",
                    "category": "system",
                    "action": "get_info",
                    "params": {},
                }

                future: asyncio.Future = asyncio.get_running_loop().create_future()
                self._pending_requests[request_id] = future

                message = json.dumps(request) + "\n"
                if self._writer is None:
                    break
                self._writer.write(message.encode("utf-8"))
                await self._writer.drain()

                await asyncio.wait_for(future, timeout=HEARTBEAT_TIMEOUT)
                self._last_activity = time.monotonic()
                logger.debug("Heartbeat OK")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Heartbeat failed: {e}")
                if self._connected:
                    asyncio.create_task(self._reconnect())
                break

    async def _read_responses(self) -> None:
        """Continuously read responses"""
        # Buffer raw bytes and decode only complete lines: read() can split a
        # multi-byte UTF-8 character across reads, and decoding each chunk as it
        # arrived turned that split into a replacement character and then a
        # dropped message. Same defect as the addon-side framing bug.
        buffer = b""

        while self._connected and self._reader:
            try:
                data = await self._reader.read(READ_BUFFER_SIZE)
                if not data:
                    logger.warning("Connection closed")
                    break

                buffer += data

                while b"\n" in buffer:
                    raw_line, buffer = buffer.split(b"\n", 1)
                    line = raw_line.decode("utf-8", errors="replace")
                    if line.strip():
                        try:
                            response = json.loads(line)
                            self._last_activity = time.monotonic()
                            await self._handle_response(response)
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parse error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading response: {e}")
                break

        self._connected = False
        if self._pending_requests:
            error = BlenderConnectionError("Connection closed")
            for future in list(self._pending_requests.values()):
                if not future.done():
                    future.set_exception(error)
            self._pending_requests.clear()

        if self.auto_reconnect:
            asyncio.create_task(self._reconnect())

    async def _handle_response(self, response: dict[str, Any]) -> None:
        """Handle a response message"""
        request_id = response.get("id")

        if request_id and request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if not future.done():
                future.set_result(response)
        else:
            logger.debug(f"Received unmatched response: {response}")

    async def send_command(
        self, category: str, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Send a command and wait for response, with auto-reconnect retry on failure

        Args:
            category: Command category
            action: Specific operation
            params: Operation parameters

        Returns:
            Response result
        """
        self._total_commands += 1

        for attempt in range(2):
            if not self.connected:
                await self.connect()

            request_id = str(uuid.uuid4())
            request = {
                "id": request_id,
                "type": "command",
                "category": category,
                "action": action,
                "params": params,
            }

            future: asyncio.Future = asyncio.get_running_loop().create_future()
            self._pending_requests[request_id] = future

            try:
                message = json.dumps(request) + "\n"
                if self._writer is None:
                    raise BlenderConnectionError("Connection unavailable")
                self._writer.write(message.encode("utf-8"))
                await self._writer.drain()

                logger.debug(f"Sending command: {category}.{action}")

                response = await asyncio.wait_for(future, timeout=self.timeout)
                self._last_activity = time.monotonic()

                return response

            except asyncio.TimeoutError:
                self._pending_requests.pop(request_id, None)
                self._failed_commands += 1
                raise BlenderConnectionError(f"Command timed out: {category}.{action}") from None
            except BlenderConnectionError:
                self._pending_requests.pop(request_id, None)
                self._failed_commands += 1
                raise
            except Exception as e:
                self._pending_requests.pop(request_id, None)
                if self._connected:
                    with contextlib.suppress(Exception):
                        await self.disconnect()

                if attempt == 0 and self.auto_reconnect:
                    logger.info(f"Command failed, attempting reconnect: {e}")
                    continue

                self._failed_commands += 1
                raise BlenderConnectionError(f"Command failed: {e}") from e

        self._failed_commands += 1
        raise BlenderConnectionError(f"Command ultimately failed: {category}.{action}")

    async def get_blender_info(self) -> dict[str, Any]:
        """Get Blender information"""
        result = await self.send_command("system", "get_info", {})
        return result.get("data", {})
