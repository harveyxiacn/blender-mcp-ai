"""
Blender MCP Addon - Plugin Entry Point

Enables MCP communication service in Blender, receiving and executing commands from the MCP server.
"""

bl_info = {
    "name": "Blender MCP",
    "author": "Harvey Xia",
    "version": (0, 3, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > MCP",
    "description": "Enable AI assistants to control Blender through MCP protocol",
    "category": "Interface",
    "doc_url": "https://github.com/harveyxiacn/blender-mcp-ai",
    "tracker_url": "https://github.com/harveyxiacn/blender-mcp-ai/issues",
}

import importlib
import sys
from pathlib import Path

import bpy
from bpy.props import BoolProperty, IntProperty, StringProperty

# Module imports
from . import operators, panels, server


# Hot reload support
def get_addon_modules():
    """Get all modules that need to be reloaded"""
    addon_package = __name__
    modules_to_reload = []

    for name, module in list(sys.modules.items()):
        if name.startswith(addon_package):
            modules_to_reload.append((name, module))

    # Sort by module depth to ensure submodules are reloaded first
    modules_to_reload.sort(key=lambda x: x[0].count("."), reverse=True)
    return modules_to_reload


def hot_reload():
    """Perform hot reload - reload all addon modules"""
    import shutil

    # Get preferences
    prefs = bpy.context.preferences.addons.get(__name__)
    if not prefs or not prefs.preferences.dev_source_path:
        return False, "Development source directory not set"

    source_path = Path(prefs.preferences.dev_source_path)
    if not source_path.exists():
        return False, f"Source directory does not exist: {source_path}"

    # Check if it is a valid addon directory
    if not (source_path / "__init__.py").exists():
        return False, f"Directory is not a valid Python package: {source_path}"

    # Get current addon installation directory
    addon_path = Path(__file__).parent

    # Stop the server
    was_running = server.is_running()
    if was_running:
        server.stop_server()

    # Items to exclude
    exclude = {"__pycache__", ".git", ".gitignore", "*.pyc", "*.pyo"}

    def should_exclude(name) -> bool:
        if name in exclude:
            return True
        return any(pattern.startswith("*") and name.endswith(pattern[1:]) for pattern in exclude)

    try:
        # Copy files
        for item in source_path.iterdir():
            if should_exclude(item.name):
                continue

            dest = addon_path / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*exclude))
            else:
                shutil.copy2(item, dest)

        # Reload modules
        modules = get_addon_modules()
        for name, module in modules:
            if module is not None:
                try:
                    importlib.reload(module)
                except Exception as e:
                    print(f"[MCP] Failed to reload module {name}: {e}")

        # Restart the server
        if was_running:
            port = prefs.preferences.port if prefs else 9876
            server.start_server(port=port)

        return True, "Hot reload complete"

    except Exception as e:
        return False, f"Hot reload failed: {e}"


class BlenderMCPPreferences(bpy.types.AddonPreferences):
    """Addon preferences"""

    bl_idname = __name__

    port: IntProperty(
        name="Server Port",
        description="MCP communication server port",
        default=9876,
        min=1024,
        max=65535,
    )

    auto_start: BoolProperty(
        name="Auto Start",
        description="Automatically start MCP service when Blender launches",
        default=True,
    )

    log_level: StringProperty(name="Log Level", description="Log verbosity level", default="INFO")

    dev_source_path: StringProperty(
        name="Dev Source Directory",
        description="Source directory path for hot reload (addon/blender_mcp_addon)",
        default="",
        subtype="DIR_PATH",
    )

    def draw(self, context) -> None:
        layout = self.layout

        # Basic settings
        box = layout.box()
        box.label(text="Basic Settings", icon="PREFERENCES")
        box.prop(self, "port")
        box.prop(self, "auto_start")
        box.prop(self, "log_level")

        # Developer settings
        layout.separator()
        box = layout.box()
        box.label(text="Developer Settings", icon="TOOL_SETTINGS")
        box.prop(self, "dev_source_path")

        if self.dev_source_path:
            row = box.row()
            row.operator("mcp.hot_reload", text="Hot Reload", icon="FILE_REFRESH")


# All classes to register
classes = [
    BlenderMCPPreferences,
]


def register() -> None:
    """Register the addon"""
    # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)

    # Register submodules
    operators.register()
    panels.register()

    # Auto-start service
    prefs = bpy.context.preferences.addons.get(__name__)
    if prefs and prefs.preferences.auto_start:
        # Delayed start to ensure Blender is fully initialized
        bpy.app.timers.register(lambda: _delayed_start(), first_interval=1.0)


def unregister() -> None:
    """Unregister the addon"""
    # Stop the server
    server.stop_server()

    # Unregister submodules
    panels.unregister()
    operators.unregister()

    # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def _delayed_start() -> None:
    """Delayed service startup"""
    try:
        prefs = bpy.context.preferences.addons.get(__name__)
        if prefs:
            port = prefs.preferences.port
            server.start_server(port=port)
    except Exception as e:
        print(f"[MCP] Failed to auto-start service: {e}")
    return None  # Do not repeat


if __name__ == "__main__":
    register()
