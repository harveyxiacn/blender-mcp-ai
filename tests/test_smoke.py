"""Basic smoke tests for Blender MCP AI core modules."""

from unittest.mock import patch

from blender_mcp.server import BlenderMCPServer
from blender_mcp.tools_config import get_enabled_modules


def test_enabled_modules_not_empty() -> None:
    """Configured profile should always load at least one module."""
    enabled = get_enabled_modules()
    assert enabled


def test_run_http_uses_streamable_http_transport() -> None:
    """run_http should start FastMCP using streamable HTTP transport."""
    server = BlenderMCPServer()
    with patch.object(server.mcp, "run", return_value=None) as mocked_run:
        server.run_http(9123)

    mocked_run.assert_called_once_with(transport="streamable-http")
