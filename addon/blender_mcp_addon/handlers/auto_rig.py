"""
Auto rigging handler

Handles bone creation, weight painting, IK setup and related commands.
"""

import math
from typing import Any

import bpy

# Humanoid bone configuration
HUMANOID_BONES = {
    "root": {"head": [0, 0, 0], "tail": [0, 0, 0.1]},
    "spine": {"head": [0, 0, 0.1], "tail": [0, 0, 0.3], "parent": "root"},
    "spine.001": {"head": [0, 0, 0.3], "tail": [0, 0, 0.5], "parent": "spine"},
    "spine.002": {"head": [0, 0, 0.5], "tail": [0, 0, 0.7], "parent": "spine.001"},
    "neck": {"head": [0, 0, 0.7], "tail": [0, 0, 0.8], "parent": "spine.002"},
    "head": {"head": [0, 0, 0.8], "tail": [0, 0, 1.0], "parent": "neck"},
    # Left arm
    "shoulder.L": {"head": [0, 0, 0.65], "tail": [0.1, 0, 0.65], "parent": "spine.002"},
    "upper_arm.L": {"head": [0.1, 0, 0.65], "tail": [0.3, 0, 0.65], "parent": "shoulder.L"},
    "forearm.L": {"head": [0.3, 0, 0.65], "tail": [0.5, 0, 0.65], "parent": "upper_arm.L"},
    "hand.L": {"head": [0.5, 0, 0.65], "tail": [0.6, 0, 0.65], "parent": "forearm.L"},
    # Right arm
    "shoulder.R": {"head": [0, 0, 0.65], "tail": [-0.1, 0, 0.65], "parent": "spine.002"},
    "upper_arm.R": {"head": [-0.1, 0, 0.65], "tail": [-0.3, 0, 0.65], "parent": "shoulder.R"},
    "forearm.R": {"head": [-0.3, 0, 0.65], "tail": [-0.5, 0, 0.65], "parent": "upper_arm.R"},
    "hand.R": {"head": [-0.5, 0, 0.65], "tail": [-0.6, 0, 0.65], "parent": "forearm.R"},
    # Left leg
    "thigh.L": {"head": [0.1, 0, 0.1], "tail": [0.1, 0, -0.3], "parent": "root"},
    "shin.L": {"head": [0.1, 0, -0.3], "tail": [0.1, 0, -0.6], "parent": "thigh.L"},
    "foot.L": {"head": [0.1, 0, -0.6], "tail": [0.1, -0.1, -0.65], "parent": "shin.L"},
    "toe.L": {"head": [0.1, -0.1, -0.65], "tail": [0.1, -0.2, -0.65], "parent": "foot.L"},
    # Right leg
    "thigh.R": {"head": [-0.1, 0, 0.1], "tail": [-0.1, 0, -0.3], "parent": "root"},
    "shin.R": {"head": [-0.1, 0, -0.3], "tail": [-0.1, 0, -0.6], "parent": "thigh.R"},
    "foot.R": {"head": [-0.1, 0, -0.6], "tail": [-0.1, -0.1, -0.65], "parent": "shin.R"},
    "toe.R": {"head": [-0.1, -0.1, -0.65], "tail": [-0.1, -0.2, -0.65], "parent": "foot.R"},
}

# Simple bone configuration
SIMPLE_BONES = {
    "root": {"head": [0, 0, 0], "tail": [0, 0, 0.2]},
    "body": {"head": [0, 0, 0.2], "tail": [0, 0, 0.6], "parent": "root"},
    "head": {"head": [0, 0, 0.6], "tail": [0, 0, 0.9], "parent": "body"},
}

POSE_PRESETS = {
    "t_pose": {
        "upper_arm.L": [0, 0, 0],
        "upper_arm.R": [0, 0, 0],
        "forearm.L": [0, 0, 0],
        "forearm.R": [0, 0, 0],
    },
    "a_pose": {
        "upper_arm.L": [0, 0, 0.5],
        "upper_arm.R": [0, 0, -0.5],
        "forearm.L": [0, 0, 0],
        "forearm.R": [0, 0, 0],
    },
    "rest": {},
}


def handle_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Automatically create bone system"""
    character_name = params.get("character_name")
    rig_type = params.get("rig_type", "humanoid")
    auto_weight = params.get("auto_weight", True)
    params.get("symmetric", True)

    # Get character objects
    body = bpy.data.objects.get(f"{character_name}_Body")
    bpy.data.objects.get(f"{character_name}_Head")

    if not body:
        return {
            "success": False,
            "error": {
                "code": "BODY_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    # Calculate character dimensions
    all_parts = [obj for obj in bpy.data.objects if obj.name.startswith(f"{character_name}_")]
    if not all_parts:
        return {
            "success": False,
            "error": {"code": "NO_PARTS", "message": "Character parts not found"},
        }

    # Calculate bounding box
    min_z = min(obj.location.z - obj.dimensions.z / 2 for obj in all_parts)
    max_z = max(obj.location.z + obj.dimensions.z / 2 for obj in all_parts)
    height = max_z - min_z
    center_x = sum(obj.location.x for obj in all_parts) / len(all_parts)
    center_y = sum(obj.location.y for obj in all_parts) / len(all_parts)

    # Select bone configuration
    if rig_type == "humanoid":
        bone_config = HUMANOID_BONES
    elif rig_type == "simple":
        bone_config = SIMPLE_BONES
    else:
        bone_config = SIMPLE_BONES

    # Create armature
    armature_name = f"{character_name}_Armature"
    bpy.ops.object.armature_add(location=[center_x, center_y, min_z])
    armature_obj = bpy.context.active_object
    armature_obj.name = armature_name
    armature = armature_obj.data
    armature.name = armature_name

    # Enter edit mode
    bpy.ops.object.mode_set(mode="EDIT")

    # Delete default bone
    for bone in armature.edit_bones:
        armature.edit_bones.remove(bone)

    # Create bones
    created_bones = []
    scale_factor = height / 1.0  # Assuming config is based on unit height

    for bone_name, config in bone_config.items():
        bone = armature.edit_bones.new(bone_name)

        # Scale positions
        head_pos = [p * scale_factor for p in config["head"]]
        tail_pos = [p * scale_factor for p in config["tail"]]

        bone.head = head_pos
        bone.tail = tail_pos

        # Set parent bone
        parent_name = config.get("parent")
        if parent_name and parent_name in armature.edit_bones:
            bone.parent = armature.edit_bones[parent_name]
            if config.get("connect", False):
                bone.use_connect = True

        created_bones.append(bone_name)

    # Exit edit mode
    bpy.ops.object.mode_set(mode="OBJECT")

    # Automatic weight painting
    if auto_weight:
        for part in all_parts:
            if part.type == "MESH":
                # Add armature modifier
                modifier = part.modifiers.new(name="Armature", type="ARMATURE")
                modifier.object = armature_obj

                # Select objects for automatic weights
                bpy.ops.object.select_all(action="DESELECT")
                part.select_set(True)
                armature_obj.select_set(True)
                bpy.context.view_layer.objects.active = armature_obj

                try:
                    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
                except:
                    # If automatic weights fail, use armature deform
                    bpy.ops.object.parent_set(type="ARMATURE")

    return {
        "success": True,
        "data": {
            "armature_name": armature_name,
            "bones_created": len(created_bones),
            "bones": created_bones,
        },
    }


def handle_bone_add(params: dict[str, Any]) -> dict[str, Any]:
    """Manually add bone"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name")
    head = params.get("head")
    tail = params.get("tail")
    parent_bone = params.get("parent_bone")
    connect = params.get("connect", False)

    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Enter edit mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode="EDIT")

    armature = armature_obj.data

    # Create bone
    bone = armature.edit_bones.new(bone_name)
    bone.head = head
    bone.tail = tail

    # Set parent bone
    if parent_bone and parent_bone in armature.edit_bones:
        bone.parent = armature.edit_bones[parent_bone]
        bone.use_connect = connect

    # Exit edit mode
    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"bone_name": bone_name}}


def handle_ik_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Set up IK constraint"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name", "")
    chain_length = params.get("chain_length", 2)
    target_name = params.get("target_name", "")
    pole_target = params.get("pole_target", "")

    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Enter pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode="POSE")

    # Get bone
    pose_bone = armature_obj.pose.bones.get(bone_name)
    if not pose_bone:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    # Add IK constraint
    ik_constraint = pose_bone.constraints.new("IK")
    ik_constraint.chain_count = chain_length

    # Set target
    if target_name:
        target_obj = bpy.data.objects.get(target_name)
        if target_obj:
            ik_constraint.target = target_obj

    # Set pole vector
    if pole_target:
        pole_obj = bpy.data.objects.get(pole_target)
        if pole_obj:
            ik_constraint.pole_target = pole_obj
            ik_constraint.pole_angle = math.radians(90)

    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"bone_name": bone_name, "chain_length": chain_length}}


def handle_weight_paint(params: dict[str, Any]) -> dict[str, Any]:
    """Automatic weight painting"""
    object_name = params.get("object_name", "")
    armature_name = params.get("armature_name", "")
    method = params.get("method", "automatic")

    obj = bpy.data.objects.get(object_name)
    armature_obj = bpy.data.objects.get(armature_name)

    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {object_name}"},
        }

    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Select objects
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    armature_obj.select_set(True)
    bpy.context.view_layer.objects.active = armature_obj

    # Select binding type based on method
    if method == "automatic":
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    elif method == "envelope":
        bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
    else:
        bpy.ops.object.parent_set(type="ARMATURE")

    return {"success": True, "data": {"object_name": object_name, "method": method}}


def handle_pose_apply(params: dict[str, Any]) -> dict[str, Any]:
    """Apply preset pose"""
    armature_name = params.get("armature_name", "")
    pose_name = params.get("pose_name", "t_pose")

    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    pose_config = POSE_PRESETS.get(pose_name, {})

    # Enter pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode="POSE")

    # Reset all bones
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.rot_clear()
    bpy.ops.pose.loc_clear()
    bpy.ops.pose.scale_clear()

    # Apply pose
    for bone_name, rotation in pose_config.items():
        pose_bone = armature_obj.pose.bones.get(bone_name)
        if pose_bone:
            pose_bone.rotation_euler = rotation

    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"pose_name": pose_name}}


def handle_constraint_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add bone constraint"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name", "")
    constraint_type = params.get("constraint_type", "COPY_ROTATION")
    target_armature = params.get("target_armature", "")
    target_bone = params.get("target_bone")

    armature_obj = bpy.data.objects.get(armature_name)
    if not armature_obj or armature_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Enter pose mode
    bpy.context.view_layer.objects.active = armature_obj
    bpy.ops.object.mode_set(mode="POSE")

    pose_bone = armature_obj.pose.bones.get(bone_name)
    if not pose_bone:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    # Add constraint
    constraint = pose_bone.constraints.new(constraint_type)

    # Set target
    if target_armature:
        target_obj = bpy.data.objects.get(target_armature)
        if target_obj:
            constraint.target = target_obj
            if target_bone:
                constraint.subtarget = target_bone

    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"constraint_type": constraint_type}}
