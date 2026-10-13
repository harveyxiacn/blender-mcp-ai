"""
Blender MCP - Model Context Protocol server for Blender.

This package provides an MCP server that enables AI assistants to control
Blender through natural language commands.
"""

__version__ = "0.4.0"
__author__ = "Harvey Xia"

from blender_mcp.server import BlenderMCPServer

__all__ = ["BlenderMCPServer", "__version__"]
