"""
Camera handler

Handles camera-related commands.
"""

from typing import Any

import bpy
import mathutils


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create camera"""
    name = params.get("name", "Camera")
    location = params.get("location", [0, -10, 5])
    rotation = params.get("rotation", [1.1, 0, 0])
    lens = params.get("lens", 50.0)
    sensor_width = params.get("sensor_width", 36.0)
    set_active = params.get("set_active", True)

    # Create camera data
    cam_data = bpy.data.cameras.new(name=name)
    cam_data.lens = lens
    cam_data.sensor_width = sensor_width

    # Create camera object
    cam_obj = bpy.data.objects.new(name=name, object_data=cam_data)
    cam_obj.location = location
    cam_obj.rotation_euler = rotation

    # Link to scene
    bpy.context.collection.objects.link(cam_obj)

    # Set as active camera
    if set_active:
        bpy.context.scene.camera = cam_obj

    return {"success": True, "data": {"camera_name": cam_obj.name}}


def handle_set_properties(params: dict[str, Any]) -> dict[str, Any]:
    """Set camera properties"""
    camera_name = params.get("camera_name", "")
    properties = params.get("properties", {})

    if not camera_name:
        return {
            "success": False,
            "error": {"code": "MISSING_PARAM", "message": "camera_name parameter is required"},
        }

    obj = bpy.data.objects.get(camera_name)
    if not obj or obj.type != "CAMERA":
        return {
            "success": False,
            "error": {"code": "CAMERA_NOT_FOUND", "message": f"Camera not found: {camera_name}"},
        }

    cam = obj.data

    if "lens" in properties:
        cam.lens = properties["lens"]

    if "sensor_width" in properties:
        cam.sensor_width = properties["sensor_width"]

    if "clip_start" in properties:
        cam.clip_start = properties["clip_start"]

    if "clip_end" in properties:
        cam.clip_end = properties["clip_end"]

    if "dof_focus_object" in properties:
        focus_obj = bpy.data.objects.get(properties["dof_focus_object"])
        if focus_obj:
            cam.dof.use_dof = True
            cam.dof.focus_object = focus_obj

    if "dof_focus_distance" in properties:
        cam.dof.use_dof = True
        cam.dof.focus_distance = properties["dof_focus_distance"]

    if "dof_aperture_fstop" in properties:
        cam.dof.use_dof = True
        cam.dof.aperture_fstop = properties["dof_aperture_fstop"]

    return {"success": True, "data": {}}


def handle_look_at(params: dict[str, Any]) -> dict[str, Any]:
    """Point camera at target"""
    camera_name = params.get("camera_name", "")
    target = params.get("target", "")
    use_constraint = params.get("use_constraint", False)

    if not camera_name:
        return {
            "success": False,
            "error": {"code": "MISSING_PARAM", "message": "camera_name parameter is required"},
        }

    obj = bpy.data.objects.get(camera_name)
    if not obj or obj.type != "CAMERA":
        return {
            "success": False,
            "error": {"code": "CAMERA_NOT_FOUND", "message": f"Camera not found: {camera_name}"},
        }

    # Determine target location
    if isinstance(target, str):
        target_obj = bpy.data.objects.get(target)
        if not target_obj:
            return {
                "success": False,
                "error": {
                    "code": "TARGET_NOT_FOUND",
                    "message": f"Target object not found: {target}",
                },
            }
        target_location = target_obj.location
    else:
        target_location = mathutils.Vector(target)
        target_obj = None

    if use_constraint and target_obj:
        # Use constraint
        constraint = obj.constraints.new(type="TRACK_TO")
        constraint.target = target_obj
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"
    else:
        # Set rotation directly
        direction = target_location - obj.location
        rot_quat = direction.to_track_quat("-Z", "Y")
        obj.rotation_euler = rot_quat.to_euler()

    return {"success": True, "data": {}}


def handle_set_active(params: dict[str, Any]) -> dict[str, Any]:
    """Set active camera"""
    # Support camera_name or name parameter
    camera_name = params.get("camera_name") or params.get("name")

    if not camera_name:
        return {
            "success": False,
            "error": {
                "code": "MISSING_PARAM",
                "message": "Must specify camera_name or name parameter",
            },
        }

    obj = bpy.data.objects.get(camera_name)
    if not obj or obj.type != "CAMERA":
        return {
            "success": False,
            "error": {"code": "CAMERA_NOT_FOUND", "message": f"Camera not found: {camera_name}"},
        }

    bpy.context.scene.camera = obj

    return {"success": True, "data": {"camera_name": camera_name}}
