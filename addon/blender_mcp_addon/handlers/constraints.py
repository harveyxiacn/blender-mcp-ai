"""
Constraint system handler

Handles Blender object and bone constraint commands.
"""

from typing import Any

import bpy


def _get_constraint_target(obj: bpy.types.Object, is_bone: bool = False, bone_name: str = None):
    """Get constraint target (object or bone)"""
    if is_bone and bone_name and obj.type == "ARMATURE" and bone_name in obj.pose.bones:
        return obj.pose.bones[bone_name]
    return obj


def handle_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add constraint"""
    object_name = params.get("object_name", "")
    constraint_type = params.get("constraint_type")
    name = params.get("name")
    target = params.get("target", "")
    subtarget = params.get("subtarget")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        constraint = obj.constraints.new(type=constraint_type)

        if name:
            constraint.name = name

        if target:
            target_obj = bpy.data.objects.get(target)
            if target_obj:
                constraint.target = target_obj
                if subtarget:
                    constraint.subtarget = subtarget

        return {
            "success": True,
            "data": {"constraint_name": constraint.name, "constraint_type": constraint_type},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CONSTRAINT_ADD_ERROR", "message": str(e)}}


def handle_remove(params: dict[str, Any]) -> dict[str, Any]:
    """Remove constraint"""
    object_name = params.get("object_name", "")
    constraint_name = params.get("constraint_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        constraint = obj.constraints.get(constraint_name)
        if constraint:
            obj.constraints.remove(constraint)
            return {"success": True, "data": {"removed": constraint_name}}
        else:
            return {
                "success": False,
                "error": {
                    "code": "CONSTRAINT_NOT_FOUND",
                    "message": f"Constraint not found: {constraint_name}",
                },
            }

    except Exception as e:
        return {"success": False, "error": {"code": "CONSTRAINT_REMOVE_ERROR", "message": str(e)}}


def handle_copy_location(params: dict[str, Any]) -> dict[str, Any]:
    """Copy location constraint"""
    object_name = params.get("object_name", "")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    use_x = params.get("use_x", True)
    use_y = params.get("use_y", True)
    use_z = params.get("use_z", True)
    influence = params.get("influence", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    target_obj = bpy.data.objects.get(target)
    if not target_obj:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    try:
        constraint = obj.constraints.new(type="COPY_LOCATION")
        constraint.target = target_obj

        if subtarget:
            constraint.subtarget = subtarget

        constraint.use_x = use_x
        constraint.use_y = use_y
        constraint.use_z = use_z
        constraint.influence = influence

        return {"success": True, "data": {"constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "COPY_LOCATION_ERROR", "message": str(e)}}


def handle_copy_rotation(params: dict[str, Any]) -> dict[str, Any]:
    """Copy rotation constraint"""
    object_name = params.get("object_name", "")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    use_x = params.get("use_x", True)
    use_y = params.get("use_y", True)
    use_z = params.get("use_z", True)
    influence = params.get("influence", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    target_obj = bpy.data.objects.get(target)
    if not target_obj:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    try:
        constraint = obj.constraints.new(type="COPY_ROTATION")
        constraint.target = target_obj

        if subtarget:
            constraint.subtarget = subtarget

        constraint.use_x = use_x
        constraint.use_y = use_y
        constraint.use_z = use_z
        constraint.influence = influence

        return {"success": True, "data": {"constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "COPY_ROTATION_ERROR", "message": str(e)}}


def handle_copy_scale(params: dict[str, Any]) -> dict[str, Any]:
    """Copy scale constraint"""
    object_name = params.get("object_name", "")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    use_x = params.get("use_x", True)
    use_y = params.get("use_y", True)
    use_z = params.get("use_z", True)
    influence = params.get("influence", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    target_obj = bpy.data.objects.get(target)
    if not target_obj:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    try:
        constraint = obj.constraints.new(type="COPY_SCALE")
        constraint.target = target_obj

        if subtarget:
            constraint.subtarget = subtarget

        constraint.use_x = use_x
        constraint.use_y = use_y
        constraint.use_z = use_z
        constraint.influence = influence

        return {"success": True, "data": {"constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "COPY_SCALE_ERROR", "message": str(e)}}


def handle_track_to(params: dict[str, Any]) -> dict[str, Any]:
    """Track to constraint"""
    object_name = params.get("object_name", "")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    track_axis = params.get("track_axis", "TRACK_NEGATIVE_Z")
    up_axis = params.get("up_axis", "UP_Y")
    influence = params.get("influence", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    target_obj = bpy.data.objects.get(target)
    if not target_obj:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    try:
        constraint = obj.constraints.new(type="TRACK_TO")
        constraint.target = target_obj

        if subtarget:
            constraint.subtarget = subtarget

        constraint.track_axis = track_axis
        constraint.up_axis = up_axis
        constraint.influence = influence

        return {"success": True, "data": {"constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "TRACK_TO_ERROR", "message": str(e)}}


def handle_limit(params: dict[str, Any]) -> dict[str, Any]:
    """Limit constraint"""
    object_name = params.get("object_name", "")
    limit_type = params.get("limit_type", "LOCATION")
    min_x = params.get("min_x")
    max_x = params.get("max_x")
    min_y = params.get("min_y")
    max_y = params.get("max_y")
    min_z = params.get("min_z")
    max_z = params.get("max_z")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        type_map = {
            "LOCATION": "LIMIT_LOCATION",
            "ROTATION": "LIMIT_ROTATION",
            "SCALE": "LIMIT_SCALE",
        }

        constraint_type = type_map.get(limit_type, "LIMIT_LOCATION")
        constraint = obj.constraints.new(type=constraint_type)

        if min_x is not None:
            constraint.use_min_x = True
            constraint.min_x = min_x
        if max_x is not None:
            constraint.use_max_x = True
            constraint.max_x = max_x
        if min_y is not None:
            constraint.use_min_y = True
            constraint.min_y = min_y
        if max_y is not None:
            constraint.use_max_y = True
            constraint.max_y = max_y
        if min_z is not None:
            constraint.use_min_z = True
            constraint.min_z = min_z
        if max_z is not None:
            constraint.use_max_z = True
            constraint.max_z = max_z

        return {
            "success": True,
            "data": {"constraint_name": constraint.name, "limit_type": limit_type},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "LIMIT_ERROR", "message": str(e)}}


def handle_ik(params: dict[str, Any]) -> dict[str, Any]:
    """IK constraint"""
    object_name = params.get("object_name", "")
    bone_name = params.get("bone_name")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    pole_target = params.get("pole_target", "")
    pole_subtarget = params.get("pole_subtarget")
    chain_count = params.get("chain_count", 2)
    influence = params.get("influence", 1.0)

    armature = bpy.data.objects.get(object_name)
    if not armature or armature.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {object_name}",
            },
        }

    if bone_name not in armature.pose.bones:
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    try:
        pose_bone = armature.pose.bones[bone_name]
        constraint = pose_bone.constraints.new(type="IK")

        if target:
            target_obj = bpy.data.objects.get(target)
            if target_obj:
                constraint.target = target_obj
                if subtarget:
                    constraint.subtarget = subtarget

        if pole_target:
            pole_obj = bpy.data.objects.get(pole_target)
            if pole_obj:
                constraint.pole_target = pole_obj
                if pole_subtarget:
                    constraint.pole_subtarget = pole_subtarget

        constraint.chain_count = chain_count
        constraint.influence = influence

        return {"success": True, "data": {"bone": bone_name, "constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "IK_ERROR", "message": str(e)}}


def handle_parent(params: dict[str, Any]) -> dict[str, Any]:
    """Parent constraint"""
    object_name = params.get("object_name", "")
    target = params.get("target", "")
    subtarget = params.get("subtarget")
    influence = params.get("influence", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    target_obj = bpy.data.objects.get(target)
    if not target_obj:
        return {
            "success": False,
            "error": {"code": "TARGET_NOT_FOUND", "message": f"Target not found: {target}"},
        }

    try:
        constraint = obj.constraints.new(type="CHILD_OF")
        constraint.target = target_obj

        if subtarget:
            constraint.subtarget = subtarget

        constraint.influence = influence

        return {"success": True, "data": {"constraint_name": constraint.name}}

    except Exception as e:
        return {"success": False, "error": {"code": "PARENT_ERROR", "message": str(e)}}


def handle_list(params: dict[str, Any]) -> dict[str, Any]:
    """List constraints"""
    object_name = params.get("object_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        constraints = []

        for c in obj.constraints:
            constraint_info = {
                "name": c.name,
                "type": c.type,
                "enabled": c.enabled,
                "influence": c.influence,
            }

            if hasattr(c, "target") and c.target:
                constraint_info["target"] = c.target.name
                if hasattr(c, "subtarget") and c.subtarget:
                    constraint_info["subtarget"] = c.subtarget

            constraints.append(constraint_info)

        return {
            "success": True,
            "data": {
                "object_name": object_name,
                "constraints": constraints,
                "count": len(constraints),
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "LIST_ERROR", "message": str(e)}}
