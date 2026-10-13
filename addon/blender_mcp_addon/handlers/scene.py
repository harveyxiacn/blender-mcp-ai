"""
Scene Handler

Handles scene-related commands.
"""

from typing import Any

import bpy


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create scene"""
    name = params.get("name", "Scene")
    copy_from = params.get("copy_from", "")

    if copy_from:
        # Copy from existing scene
        source = bpy.data.scenes.get(copy_from)
        if not source:
            return {
                "success": False,
                "error": {
                    "code": "SCENE_NOT_FOUND",
                    "message": f"Source scene not found: {copy_from}",
                },
            }
        scene = source.copy()
        scene.name = name
    else:
        # Create new scene
        scene = bpy.data.scenes.new(name)

    return {"success": True, "data": {"scene_name": scene.name}}


def handle_list(params: dict[str, Any]) -> dict[str, Any]:
    """List scenes"""
    scenes = []
    active_scene = bpy.context.scene

    for scene in bpy.data.scenes:
        scenes.append(
            {
                "name": scene.name,
                "objects_count": len(scene.objects),
                "is_active": scene == active_scene,
            }
        )

    return {"success": True, "data": {"scenes": scenes, "total": len(scenes)}}


def handle_get_info(params: dict[str, Any]) -> dict[str, Any]:
    """Get scene info"""
    scene_name = params.get("scene_name", "")

    if scene_name:
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            return {
                "success": False,
                "error": {"code": "SCENE_NOT_FOUND", "message": f"Scene not found: {scene_name}"},
            }
    else:
        scene = bpy.context.scene

    return {
        "success": True,
        "data": {
            "name": scene.name,
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
            "fps": scene.render.fps,
            "objects_count": len(scene.objects),
            "unit_system": scene.unit_settings.system,
            "unit_scale": scene.unit_settings.scale_length,
        },
    }


def handle_switch(params: dict[str, Any]) -> dict[str, Any]:
    """Switch scene"""
    scene_name = params.get("scene_name", "")

    scene = bpy.data.scenes.get(scene_name)
    if not scene:
        return {
            "success": False,
            "error": {"code": "SCENE_NOT_FOUND", "message": f"Scene not found: {scene_name}"},
        }

    bpy.context.window.scene = scene

    return {"success": True, "data": {"scene_name": scene.name}}


def handle_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete scene"""
    scene_name = params.get("scene_name", "")

    if len(bpy.data.scenes) <= 1:
        return {
            "success": False,
            "error": {
                "code": "CANNOT_DELETE_LAST_SCENE",
                "message": "Cannot delete the last scene",
            },
        }

    scene = bpy.data.scenes.get(scene_name)
    if not scene:
        return {
            "success": False,
            "error": {"code": "SCENE_NOT_FOUND", "message": f"Scene not found: {scene_name}"},
        }

    bpy.data.scenes.remove(scene)

    return {"success": True, "data": {}}


def handle_set_settings(params: dict[str, Any]) -> dict[str, Any]:
    """Set scene settings"""
    scene_name = params.get("scene_name", "")
    settings = params.get("settings", {})

    if scene_name:
        scene = bpy.data.scenes.get(scene_name)
        if not scene:
            return {
                "success": False,
                "error": {"code": "SCENE_NOT_FOUND", "message": f"Scene not found: {scene_name}"},
            }
    else:
        scene = bpy.context.scene

    # Apply settings
    if "frame_start" in settings:
        scene.frame_start = settings["frame_start"]
    if "frame_end" in settings:
        scene.frame_end = settings["frame_end"]
    if "fps" in settings:
        scene.render.fps = settings["fps"]
    if "unit_system" in settings:
        scene.unit_settings.system = settings["unit_system"]
    if "unit_scale" in settings:
        scene.unit_settings.scale_length = settings["unit_scale"]

    return {"success": True, "data": {"scene_name": scene.name}}


def handle_set_frame_range(params: dict[str, Any]) -> dict[str, Any]:
    """Set frame range"""
    start = params.get("start", 1)
    end = params.get("end", 250)

    scene = bpy.context.scene
    scene.frame_start = start
    scene.frame_end = end

    return {
        "success": True,
        "data": {"frame_start": scene.frame_start, "frame_end": scene.frame_end},
    }
