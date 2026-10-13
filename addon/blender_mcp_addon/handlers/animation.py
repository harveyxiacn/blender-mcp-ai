"""
Animation handler

Handles animation-related commands.
"""

from typing import Any

import bpy


def handle_keyframe_insert(params: dict[str, Any]) -> dict[str, Any]:
    """Insert keyframe"""
    object_name = params.get("object_name", "")
    data_path = params.get("data_path")
    frame = params.get("frame")
    value = params.get("value")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # If a frame is specified, jump to that frame
    if frame is not None:
        bpy.context.scene.frame_set(frame)
    else:
        frame = bpy.context.scene.frame_current

    # If a value is specified, set the property value
    if value is not None:
        try:
            # Parse data path
            if "[" in data_path:
                # Handle index, e.g. location[0]
                base_path, index = data_path.rsplit("[", 1)
                index = int(index.rstrip("]"))
                current = getattr(obj, base_path)
                current[index] = value
            else:
                setattr(obj, data_path, value)
        except Exception as e:
            return {
                "success": False,
                "error": {
                    "code": "SET_VALUE_ERROR",
                    "message": f"Failed to set property value: {e}",
                },
            }

    # Insert keyframe
    try:
        obj.keyframe_insert(data_path=data_path, frame=frame)
    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "KEYFRAME_INSERT_ERROR",
                "message": f"Failed to insert keyframe: {e}",
            },
        }

    return {"success": True, "data": {"frame": frame}}


def handle_keyframe_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete keyframe"""
    object_name = params.get("object_name", "")
    data_path = params.get("data_path")
    frame = params.get("frame")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if frame is not None:
        bpy.context.scene.frame_set(frame)

    try:
        obj.keyframe_delete(data_path=data_path)
    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": "KEYFRAME_DELETE_ERROR",
                "message": f"Failed to delete keyframe: {e}",
            },
        }

    return {"success": True, "data": {}}


def handle_set_interpolation(params: dict[str, Any]) -> dict[str, Any]:
    """Set interpolation type"""
    object_name = params.get("object_name", "")
    interpolation = params.get("interpolation", "BEZIER")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if not obj.animation_data or not obj.animation_data.action:
        return {
            "success": False,
            "error": {"code": "NO_ANIMATION", "message": "Object has no animation data"},
        }

    # Set interpolation type for all keyframes
    # In Blender 5.0+, Action.fcurves was removed in favor of the layered action system
    action = obj.animation_data.action
    if hasattr(action, "fcurves"):
        try:
            fcurves = action.fcurves
            for fcurve in fcurves:
                for keyframe in fcurve.keyframe_points:
                    keyframe.interpolation = interpolation
        except (AttributeError, TypeError):
            return {
                "success": False,
                "error": {
                    "code": "FCURVES_ACCESS_ERROR",
                    "message": (
                        "Failed to access fcurves on the action. "
                        "This may require a legacy action type in Blender 5.0+."
                    ),
                },
            }
    else:
        return {
            "success": False,
            "error": {
                "code": "UNSUPPORTED_ACTION_TYPE",
                "message": (
                    "Action.fcurves is not available. "
                    "This feature requires a legacy action type. "
                    "Blender 5.0+ uses a layered action system that is not yet supported."
                ),
            },
        }

    return {"success": True, "data": {}}


def handle_timeline_set_range(params: dict[str, Any]) -> dict[str, Any]:
    """Set timeline range"""
    scene = bpy.context.scene

    if "frame_start" in params:
        scene.frame_start = params["frame_start"]

    if "frame_end" in params:
        scene.frame_end = params["frame_end"]

    if "frame_current" in params:
        scene.frame_set(params["frame_current"])

    return {
        "success": True,
        "data": {
            "frame_start": scene.frame_start,
            "frame_end": scene.frame_end,
            "frame_current": scene.frame_current,
        },
    }


def handle_goto_frame(params: dict[str, Any]) -> dict[str, Any]:
    """Go to frame"""
    frame = params.get("frame", 1)

    bpy.context.scene.frame_set(frame)

    return {"success": True, "data": {"frame_current": bpy.context.scene.frame_current}}


def handle_bake(params: dict[str, Any]) -> dict[str, Any]:
    """Bake animation"""
    object_name = params.get("object_name", "")
    frame_start = params.get("frame_start")
    frame_end = params.get("frame_end")
    step = params.get("step", 1)
    params.get("bake_location", True)
    params.get("bake_rotation", True)
    params.get("bake_scale", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    scene = bpy.context.scene
    start = frame_start if frame_start is not None else scene.frame_start
    end = frame_end if frame_end is not None else scene.frame_end

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Bake animation
    bpy.ops.nla.bake(
        frame_start=start,
        frame_end=end,
        step=step,
        only_selected=True,
        visual_keying=True,
        clear_constraints=False,
        clear_parents=False,
        use_current_action=True,
        bake_types={"POSE"} if obj.type == "ARMATURE" else {"OBJECT"},
    )

    return {"success": True, "data": {}}


def handle_action_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create animation action

    Args:
        params:
            - armature_name: Armature name
            - action_name: Action name
            - fake_user: Whether to set fake user (prevent cleanup)
    """
    armature_name = params.get("armature_name", "")
    action_name = params.get("action_name", "Action")
    fake_user = params.get("fake_user", True)

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Create action
    action = bpy.data.actions.new(name=action_name)
    action.use_fake_user = fake_user

    # Assign to armature
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    return {"success": True, "data": {"action_name": action.name, "armature_name": obj.name}}


def handle_action_create_from_poses(params: dict[str, Any]) -> dict[str, Any]:
    """Create animation action from poses

    Batch create animation keyframe sequences.

    Args:
        params:
            - armature_name: Armature name
            - action_name: Action name
            - keyframes: List of keyframe data
                [
                    {
                        "frame": int,           # Frame number
                        "bone": str,            # Bone name
                        "location": [x,y,z],    # Location (optional)
                        "rotation": [x,y,z],    # Euler rotation (optional)
                        "rotation_quaternion": [w,x,y,z],  # Quaternion rotation (optional)
                        "scale": [x,y,z]        # Scale (optional)
                    },
                    ...
                ]
            - fake_user: Whether to set fake user
    """
    armature_name = params.get("armature_name", "")
    action_name = params.get("action_name", "Action")
    keyframes = params.get("keyframes", [])
    fake_user = params.get("fake_user", True)

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Create action
    action = bpy.data.actions.new(name=action_name)
    action.use_fake_user = fake_user

    # Assign to armature
    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    # Switch to pose mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="POSE")

    keyframe_count = 0
    bones_animated = set()

    try:
        for kf_data in keyframes:
            frame = kf_data.get("frame", 1)
            bone_name = kf_data.get("bone")

            if not bone_name:
                continue

            pose_bone = obj.pose.bones.get(bone_name)
            if not pose_bone:
                continue

            bones_animated.add(bone_name)

            # Set location
            if "location" in kf_data:
                pose_bone.location = kf_data["location"]
                pose_bone.keyframe_insert(data_path="location", frame=frame)
                keyframe_count += 1

            # Set rotation (Euler angles)
            if "rotation" in kf_data:
                pose_bone.rotation_mode = "XYZ"
                pose_bone.rotation_euler = kf_data["rotation"]
                pose_bone.keyframe_insert(data_path="rotation_euler", frame=frame)
                keyframe_count += 1

            # Set rotation (quaternion)
            if "rotation_quaternion" in kf_data:
                pose_bone.rotation_mode = "QUATERNION"
                pose_bone.rotation_quaternion = kf_data["rotation_quaternion"]
                pose_bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
                keyframe_count += 1

            # Set scale
            if "scale" in kf_data:
                pose_bone.scale = kf_data["scale"]
                pose_bone.keyframe_insert(data_path="scale", frame=frame)
                keyframe_count += 1

        bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "success": True,
            "data": {
                "action_name": action.name,
                "armature_name": obj.name,
                "keyframe_count": keyframe_count,
                "bones_animated": list(bones_animated),
            },
        }

    except Exception as e:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"success": False, "error": {"code": "KEYFRAME_ERROR", "message": str(e)}}


def handle_action_list(params: dict[str, Any]) -> dict[str, Any]:
    """List all actions

    Args:
        params:
            - armature_name: Optional, only list actions for a specific armature
    """
    params.get("armature_name")

    actions = []
    for action in bpy.data.actions:
        action_info = {
            "name": action.name,
            "frame_start": action.frame_range[0],
            "frame_end": action.frame_range[1],
            "fake_user": action.use_fake_user,
            "users": action.users,
        }
        actions.append(action_info)

    return {"success": True, "data": {"actions": actions, "total": len(actions)}}


def handle_action_assign(params: dict[str, Any]) -> dict[str, Any]:
    """Assign action to armature

    Args:
        params:
            - armature_name: Armature name
            - action_name: Action name
    """
    armature_name = params.get("armature_name", "")
    action_name = params.get("action_name", "")

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    action = bpy.data.actions.get(action_name)
    if not action:
        return {
            "success": False,
            "error": {"code": "ACTION_NOT_FOUND", "message": f"Action not found: {action_name}"},
        }

    if not obj.animation_data:
        obj.animation_data_create()
    obj.animation_data.action = action

    return {"success": True, "data": {"armature_name": obj.name, "action_name": action.name}}


def handle_nla_push_action(params: dict[str, Any]) -> dict[str, Any]:
    """Push action to NLA track

    Args:
        params:
            - armature_name: Armature name
            - action_name: Action name (optional, defaults to current action)
            - track_name: NLA track name
            - start_frame: Start frame
    """
    armature_name = params.get("armature_name", "")
    action_name = params.get("action_name", "")
    track_name = params.get("track_name", "NLATrack")
    start_frame = params.get("start_frame", 1)

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    if not obj.animation_data:
        return {
            "success": False,
            "error": {"code": "NO_ANIMATION_DATA", "message": "Armature has no animation data"},
        }

    # Get action
    if action_name:
        action = bpy.data.actions.get(action_name)
        if not action:
            return {
                "success": False,
                "error": {
                    "code": "ACTION_NOT_FOUND",
                    "message": f"Action not found: {action_name}",
                },
            }
    else:
        action = obj.animation_data.action
        if not action:
            return {
                "success": False,
                "error": {"code": "NO_ACTION", "message": "Armature has no current action"},
            }

    # Create NLA track
    track = obj.animation_data.nla_tracks.new()
    track.name = track_name

    # Create NLA strip
    strip = track.strips.new(action.name, start_frame, action)

    return {
        "success": True,
        "data": {
            "armature_name": obj.name,
            "action_name": action.name,
            "track_name": track.name,
            "strip_name": strip.name,
        },
    }
