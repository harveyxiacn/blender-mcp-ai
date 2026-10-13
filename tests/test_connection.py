"""Tests for BlenderConnection."""

import asyncio
import contextlib
import json

import pytest

from blender_mcp.connection import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    BlenderConnection,
    BlenderConnectionError,
)


class TestBlenderConnectionInit:
    def test_defaults(self) -> None:
        conn = BlenderConnection()
        assert conn.host == DEFAULT_HOST
        assert conn.port == DEFAULT_PORT
        assert conn.auto_reconnect is True
        assert not conn.connected

    def test_custom_params(self) -> None:
        conn = BlenderConnection(host="10.0.0.1", port=1234, auto_reconnect=False)
        assert conn.host == "10.0.0.1"
        assert conn.port == 1234
        assert conn.auto_reconnect is False

    def test_stats_initial(self) -> None:
        conn = BlenderConnection()
        stats = conn.stats
        assert stats["connected"] is False
        assert stats["total_commands"] == 0
        assert stats["failed_commands"] == 0
        assert stats["reconnect_count"] == 0


class TestBlenderConnectionConnect:
    @pytest.mark.asyncio
    async def test_connect_refused(self) -> None:
        conn = BlenderConnection(port=19999, max_retries=1, auto_reconnect=False)
        with pytest.raises(BlenderConnectionError, match="Cannot connect"):
            await conn.connect()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self) -> None:
        conn = BlenderConnection()
        conn._connected = True
        await conn.connect()

    @pytest.mark.asyncio
    async def test_disconnect_when_not_connected(self) -> None:
        conn = BlenderConnection()
        await conn.disconnect()


class TestBlenderConnectionSendCommand:
    @pytest.mark.asyncio
    async def test_send_without_connection_raises(self) -> None:
        conn = BlenderConnection(port=19999, max_retries=1, auto_reconnect=False)
        with pytest.raises(BlenderConnectionError):
            await conn.send_command("scene", "list", {})

    @pytest.mark.asyncio
    async def test_stats_increment_on_send(self) -> None:
        conn = BlenderConnection(port=19999, max_retries=1, auto_reconnect=False)
        with contextlib.suppress(BlenderConnectionError):
            await conn.send_command("scene", "list", {})
        assert conn.stats["total_commands"] == 1


class TestHandleResponse:
    @pytest.mark.asyncio
    async def test_matching_response(self) -> None:
        conn = BlenderConnection()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        conn._pending_requests["test-id"] = future

        await conn._handle_response({"id": "test-id", "success": True, "data": {}})

        assert future.done()
        assert future.result() == {"id": "test-id", "success": True, "data": {}}

    @pytest.mark.asyncio
    async def test_unmatched_response(self) -> None:
        conn = BlenderConnection()
        await conn._handle_response({"id": "unknown-id", "success": True})


class _RecordingWriter:
    """Minimal stand-in for a StreamWriter that records what was written."""

    def __init__(self) -> None:
        self.writes: list[bytes] = []

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    async def drain(self) -> None:
        return None


class _ChunkReader:
    """Stand-in for a StreamReader returning preset chunks, then EOF."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = list(chunks)

    async def read(self, _n: int) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""


class TestHeartbeat:
    @pytest.mark.asyncio
    async def test_does_not_probe_while_a_command_is_pending(self) -> None:
        """A long render blocks the addon's reply - that is not a dead link."""
        conn = BlenderConnection(heartbeat_interval=0.01, auto_reconnect=False)
        conn._connected = True
        conn._writer = _RecordingWriter()
        conn._last_activity = 0.0  # make the "idle" branch reachable

        loop = asyncio.get_running_loop()
        conn._pending_requests["a-real-command"] = loop.create_future()

        task = asyncio.create_task(conn._heartbeat_loop())
        await asyncio.sleep(0.05)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        assert conn._writer.writes == []

    @pytest.mark.asyncio
    async def test_probes_when_idle(self) -> None:
        conn = BlenderConnection(heartbeat_interval=0.01, auto_reconnect=False)
        conn._connected = True
        conn._writer = _RecordingWriter()
        conn._last_activity = 0.0

        task = asyncio.create_task(conn._heartbeat_loop())
        await asyncio.sleep(0.05)
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

        assert conn._writer.writes, "expected a heartbeat probe"
        assert b"heartbeat-" in conn._writer.writes[0]


class TestReadResponsesFraming:
    @pytest.mark.asyncio
    async def test_reassembles_a_multibyte_char_split_across_reads(self) -> None:
        """Mirror of the addon framing bug: read() can split a UTF-8 char."""
        note = "中文"
        payload = (
            json.dumps(
                {"id": "split-1", "success": True, "data": {"note": note}},
                ensure_ascii=False,
            ).encode("utf-8")
            + b"\n"
        )
        # Cut in the middle of the first multi-byte character.
        cut = payload.index("中".encode()) + 1
        assert payload[cut - 1] > 127, "the cut must land inside a multi-byte char"

        conn = BlenderConnection(auto_reconnect=False)
        conn._connected = True
        conn._reader = _ChunkReader([payload[:cut], payload[cut:]])

        future = asyncio.get_running_loop().create_future()
        conn._pending_requests["split-1"] = future

        task = asyncio.create_task(conn._read_responses())
        try:
            response = await asyncio.wait_for(future, timeout=2)
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        assert response["data"]["note"] == note
