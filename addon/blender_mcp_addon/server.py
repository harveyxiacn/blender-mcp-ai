"""
MCP Communication Server

A socket server running inside Blender that receives and processes MCP commands.
"""

import contextlib
import json
import socket
import threading
import traceback
from typing import Any

import bpy

from .executor import CommandExecutor


class MCPServer:
    """MCP Socket Server"""

    def __init__(self, host: str = "127.0.0.1", port: int = 9876) -> None:
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None
        self.running = False
        self.thread: threading.Thread | None = None
        self.executor = CommandExecutor()
        self.clients: list = []

    def start(self) -> bool:
        """Start the server"""
        if self.running:
            return True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.socket.settimeout(1.0)  # Allow periodic checking of stop signal

            self.running = True
            self.thread = threading.Thread(target=self._server_loop, daemon=True)
            self.thread.start()

            print(f"[MCP] Server started: {self.host}:{self.port}")
            return True

        except Exception as e:
            print(f"[MCP] Failed to start server: {e}")
            self.running = False
            return False

    def stop(self) -> None:
        """Stop the server"""
        self.running = False

        # Close all client connections
        for client in self.clients:
            with contextlib.suppress(Exception):
                client.close()
        self.clients.clear()

        # Close the server socket
        if self.socket:
            with contextlib.suppress(Exception):
                self.socket.close()
            self.socket = None

        # Wait for the thread to finish
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        print("[MCP] Server stopped")

    def _server_loop(self) -> None:
        """Server main loop"""
        while self.running and self.socket:
            try:
                client_socket, address = self.socket.accept()
                print(f"[MCP] Client connected: {address}")

                self.clients.append(client_socket)

                # Create a handler thread for each client
                client_thread = threading.Thread(
                    target=self._handle_client, args=(client_socket, address), daemon=True
                )
                client_thread.start()

            except TimeoutError:
                continue
            except Exception as e:
                if self.running:
                    print(f"[MCP] Error accepting connection: {e}")

    def _handle_client(self, client_socket: socket.socket, address) -> None:
        """Handle a client connection"""
        # Buffer raw bytes and decode only complete, newline-delimited lines.
        # recv() returns arbitrary chunks that may split a multi-byte UTF-8
        # character across two reads; decoding each chunk as it arrived raised
        # UnicodeDecodeError mid-message, which the handler below swallowed
        # into a silent disconnect before the code ever ran (issue #2).
        buffer = b""

        try:
            while self.running:
                try:
                    data = client_socket.recv(4096)
                    if not data:
                        break

                    buffer += data

                    # Process complete JSON messages (delimited by newlines)
                    while b"\n" in buffer:
                        raw_line, buffer = buffer.split(b"\n", 1)
                        if not raw_line.strip():
                            continue

                        # The line is complete, so its bytes hold whole UTF-8
                        # sequences; "replace" only guards a malformed client.
                        line = raw_line.decode("utf-8", errors="replace")
                        response = self._process_message(line)
                        response_json = json.dumps(response) + "\n"

                        # sendall, not send: send() may write only part of a
                        # large reply, which would desync the newline framing.
                        client_socket.sendall(response_json.encode("utf-8"))

                except TimeoutError:
                    continue
                except Exception as e:
                    print(f"[MCP] Error processing message: {e}")
                    traceback.print_exc()
                    # Report the fault instead of dropping the socket silently,
                    # so protocol-level errors are diagnosable from the client.
                    with contextlib.suppress(Exception):
                        error_json = (
                            json.dumps(
                                {
                                    "id": "unknown",
                                    "success": False,
                                    "error": {"code": "PROTOCOL_ERROR", "message": str(e)},
                                }
                            )
                            + "\n"
                        )
                        client_socket.sendall(error_json.encode("utf-8"))
                    break

        finally:
            with contextlib.suppress(Exception):
                client_socket.close()

            if client_socket in self.clients:
                self.clients.remove(client_socket)

            print(f"[MCP] Client disconnected: {address}")

    def _process_message(self, message: str) -> dict[str, Any]:
        """Process a received message"""
        try:
            request = json.loads(message)
            request_id = request.get("id", "unknown")
            msg_type = request.get("type")

            if msg_type == "command":
                category = request.get("category", "")
                action = request.get("action", "")
                params = request.get("params", {})

                # Execute Blender operations in the main thread
                result = self._execute_in_main_thread(category, action, params)

                return {"id": request_id, **result}

            else:
                return {
                    "id": request_id,
                    "success": False,
                    "error": {
                        "code": "UNKNOWN_MESSAGE_TYPE",
                        "message": f"Unknown message type: {msg_type}",
                    },
                }

        except json.JSONDecodeError as e:
            return {
                "id": "unknown",
                "success": False,
                "error": {"code": "INVALID_JSON", "message": f"Invalid JSON: {e}"},
            }
        except Exception as e:
            return {
                "id": "unknown",
                "success": False,
                "error": {"code": "INTERNAL_ERROR", "message": str(e)},
            }

    def _execute_in_main_thread(
        self, category: str, action: str, params: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a command in Blender's main thread"""

        done_event = threading.Event()
        result_container: dict[str, Any] = {"result": None}
        raw_timeout = params.get("timeout", 30.0)
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError):
            timeout = 30.0
        timeout = max(1.0, min(timeout, 3600.0))

        def execute() -> None:
            try:
                result_container["result"] = self.executor.execute(category, action, params)
            except Exception as e:
                result_container["result"] = {
                    "success": False,
                    "error": {"code": "EXECUTION_ERROR", "message": str(e)},
                }
            finally:
                done_event.set()

        bpy.app.timers.register(execute, first_interval=0)

        if not done_event.wait(timeout=timeout):
            return {
                "success": False,
                "error": {"code": "TIMEOUT", "message": "Command execution timed out"},
            }

        return result_container["result"]


# Global server instance
_server: MCPServer | None = None


def start_server(host: str = "127.0.0.1", port: int = 9876) -> bool:
    """Start the MCP server"""
    global _server

    if _server and _server.running:
        return True

    _server = MCPServer(host=host, port=port)
    return _server.start()


def stop_server() -> None:
    """Stop the MCP server"""
    global _server

    if _server:
        _server.stop()
        _server = None


def is_running() -> bool:
    """Check if the server is running"""
    return _server is not None and _server.running


def get_port() -> int:
    """Get the current port"""
    return _server.port if _server else 9876
