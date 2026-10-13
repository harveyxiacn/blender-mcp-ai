"""
Rigging Handler

Handles armature and rigging-related commands.
"""

from typing import Any

import bpy

from .compat import select_only


def handle_armature_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create armature"""
    name = params.get("name", "Armature")
    location = params.get("location", [0, 0, 0])

    # Create armature data
    arm_data = bpy.data.armatures.new(name=name)

    # Create armature object
    arm_obj = bpy.data.objects.new(name=name, object_data=arm_data)
    arm_obj.location = location

    # Link to the scene master collection (always part of the active view layer)
    bpy.context.scene.collection.objects.link(arm_obj)

    return {"success": True, "data": {"armature_name": arm_obj.name}}


def handle_bone_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add bone"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name")
    head = params.get("head", [0, 0, 0])
    tail = params.get("tail", [0, 0, 1])
    parent = params.get("parent", "")
    use_connect = params.get("use_connect", False)

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Switch to edit mode (select_only ensures armature is in the view layer)
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")

    # Create bone
    arm = obj.data
    bone = arm.edit_bones.new(bone_name)
    bone.head = head
    bone.tail = tail

    # Set parent bone
    if parent:
        parent_bone = arm.edit_bones.get(parent)
        if parent_bone:
            bone.parent = parent_bone
            bone.use_connect = use_connect

    # Return to object mode
    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"bone_name": bone_name}}


def handle_generate_rig(params: dict[str, Any]) -> dict[str, Any]:
    """Generate character rig"""
    target_mesh = params.get("target_mesh", "")
    rig_type = params.get("rig_type", "HUMAN")
    auto_weights = params.get("auto_weights", True)

    mesh_obj = bpy.data.objects.get(target_mesh)
    if not mesh_obj or mesh_obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {target_mesh}"},
        }

    # Create base armature
    bpy.ops.object.armature_add(location=mesh_obj.location)
    arm_obj = bpy.context.active_object
    arm_obj.name = f"{target_mesh}_Rig"

    # Add bones based on rig type
    bpy.ops.object.mode_set(mode="EDIT")
    arm = arm_obj.data

    # Delete default bone
    for bone in arm.edit_bones:
        arm.edit_bones.remove(bone)

    # Add basic bone structure (simplified version)
    if rig_type == "HUMAN":
        # Spine
        root = arm.edit_bones.new("root")
        root.head = (0, 0, 0)
        root.tail = (0, 0, 0.2)

        spine = arm.edit_bones.new("spine")
        spine.head = (0, 0, 0.2)
        spine.tail = (0, 0, 0.5)
        spine.parent = root

        chest = arm.edit_bones.new("chest")
        chest.head = (0, 0, 0.5)
        chest.tail = (0, 0, 0.8)
        chest.parent = spine

        neck = arm.edit_bones.new("neck")
        neck.head = (0, 0, 0.8)
        neck.tail = (0, 0, 0.9)
        neck.parent = chest

        head = arm.edit_bones.new("head")
        head.head = (0, 0, 0.9)
        head.tail = (0, 0, 1.1)
        head.parent = neck

        # Arms
        for side in ["L", "R"]:
            sign = 1 if side == "L" else -1

            shoulder = arm.edit_bones.new(f"shoulder.{side}")
            shoulder.head = (sign * 0.1, 0, 0.75)
            shoulder.tail = (sign * 0.2, 0, 0.75)
            shoulder.parent = chest

            upper_arm = arm.edit_bones.new(f"upper_arm.{side}")
            upper_arm.head = (sign * 0.2, 0, 0.75)
            upper_arm.tail = (sign * 0.45, 0, 0.55)
            upper_arm.parent = shoulder

            forearm = arm.edit_bones.new(f"forearm.{side}")
            forearm.head = (sign * 0.45, 0, 0.55)
            forearm.tail = (sign * 0.65, 0, 0.35)
            forearm.parent = upper_arm
            forearm.use_connect = True

            hand = arm.edit_bones.new(f"hand.{side}")
            hand.head = (sign * 0.65, 0, 0.35)
            hand.tail = (sign * 0.75, 0, 0.3)
            hand.parent = forearm
            hand.use_connect = True

        # Legs
        for side in ["L", "R"]:
            sign = 1 if side == "L" else -1

            thigh = arm.edit_bones.new(f"thigh.{side}")
            thigh.head = (sign * 0.1, 0, 0.2)
            thigh.tail = (sign * 0.12, 0.02, -0.2)
            thigh.parent = root

            shin = arm.edit_bones.new(f"shin.{side}")
            shin.head = (sign * 0.12, 0.02, -0.2)
            shin.tail = (sign * 0.12, 0, -0.6)
            shin.parent = thigh
            shin.use_connect = True

            foot = arm.edit_bones.new(f"foot.{side}")
            foot.head = (sign * 0.12, 0, -0.6)
            foot.tail = (sign * 0.12, -0.15, -0.65)
            foot.parent = shin
            foot.use_connect = True

    bpy.ops.object.mode_set(mode="OBJECT")

    # Bind mesh to armature
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    if auto_weights:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    else:
        bpy.ops.object.parent_set(type="ARMATURE")

    return {"success": True, "data": {"armature_name": arm_obj.name}}


def handle_ik_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Set up IK"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name", "")
    target = params.get("target", "")
    chain_length = params.get("chain_length", 2)
    pole_target = params.get("pole_target", "")

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Switch to pose mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="POSE")

    # Get pose bone
    pose_bone = obj.pose.bones.get(bone_name)
    if not pose_bone:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    # Add IK constraint
    ik = pose_bone.constraints.new(type="IK")
    ik.chain_count = chain_length

    # Set target
    target_obj = bpy.data.objects.get(target)
    if target_obj:
        ik.target = target_obj

    # Set pole target
    if pole_target:
        pole_obj = bpy.data.objects.get(pole_target)
        if pole_obj:
            ik.pole_target = pole_obj

    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {}}


def handle_pose_set(params: dict[str, Any]) -> dict[str, Any]:
    """Set pose"""
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name", "")
    location = params.get("location")
    rotation = params.get("rotation")
    rotation_mode = params.get("rotation_mode", "XYZ")

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Switch to pose mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="POSE")

    # Get pose bone
    pose_bone = obj.pose.bones.get(bone_name)
    if not pose_bone:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    # Set rotation mode
    pose_bone.rotation_mode = rotation_mode

    # Set location
    if location:
        pose_bone.location = location

    # Set rotation
    if rotation:
        pose_bone.rotation_euler = rotation

    bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {}}


def handle_weight_paint(params: dict[str, Any]) -> dict[str, Any]:
    """Automatic weight painting"""
    mesh_name = params.get("mesh_name", "")
    armature_name = params.get("armature_name", "")
    params.get("auto_normalize", True)

    mesh_obj = bpy.data.objects.get(mesh_name)
    arm_obj = bpy.data.objects.get(armature_name)

    if not mesh_obj or mesh_obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {mesh_name}"},
        }

    if not arm_obj or arm_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Select mesh and armature
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    # Auto weights
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")

    return {"success": True, "data": {}}


def handle_armature_bind(params: dict[str, Any]) -> dict[str, Any]:
    """Bind mesh to armature

    Args:
        params:
            - mesh_name: Mesh object name
            - armature_name: Armature object name
            - bind_type: Bind type
                - AUTO: Auto weights (recommended)
                - ENVELOPE: Envelope weights
                - EMPTY: Bind only, no weights
            - preserve_volume: Whether to preserve volume (prevents excessive deformation at joints)
    """
    mesh_name = params.get("mesh_name", "")
    armature_name = params.get("armature_name", "")
    bind_type = params.get("bind_type", "AUTO")
    preserve_volume = params.get("preserve_volume", True)

    mesh_obj = bpy.data.objects.get(mesh_name)
    arm_obj = bpy.data.objects.get(armature_name)

    if not mesh_obj or mesh_obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {mesh_name}"},
        }

    if not arm_obj or arm_obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Ensure in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Select mesh and armature (mesh selected first, armature as active object)
    bpy.ops.object.select_all(action="DESELECT")
    mesh_obj.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    # Execute bind based on bind type
    try:
        if bind_type == "AUTO":
            bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        elif bind_type == "ENVELOPE":
            bpy.ops.object.parent_set(type="ARMATURE_ENVELOPE")
        elif bind_type == "EMPTY":
            bpy.ops.object.parent_set(type="ARMATURE")
        else:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_BIND_TYPE",
                    "message": f"Unsupported bind type: {bind_type}",
                },
            }

        # Set armature modifier's preserve volume option
        if preserve_volume:
            for mod in mesh_obj.modifiers:
                if mod.type == "ARMATURE" and mod.object == arm_obj:
                    mod.use_deform_preserve_volume = True
                    break

        return {
            "success": True,
            "data": {
                "mesh_name": mesh_obj.name,
                "armature_name": arm_obj.name,
                "bind_type": bind_type,
                "preserve_volume": preserve_volume,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "BIND_ERROR", "message": str(e)}}


def handle_vertex_group_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create vertex group

    Args:
        params:
            - object_name: Object name
            - group_name: Vertex group name
            - vertex_indices: Vertex index list (optional)
            - weight: Weight value (0.0-1.0)
    """
    object_name = params.get("object_name", "")
    group_name = params.get("group_name")
    vertex_indices = params.get("vertex_indices", [])
    weight = params.get("weight", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Mesh object not found: {object_name}",
            },
        }

    # Create vertex group
    vg = obj.vertex_groups.new(name=group_name)

    # If vertices specified, add them to the group
    if vertex_indices:
        vg.add(vertex_indices, weight, "REPLACE")

    return {
        "success": True,
        "data": {"object_name": obj.name, "group_name": vg.name, "group_index": vg.index},
    }


def handle_vertex_group_assign(params: dict[str, Any]) -> dict[str, Any]:
    """Assign vertices to vertex group

    Args:
        params:
            - object_name: Object name
            - group_name: Vertex group name
            - vertex_indices: Vertex index list
            - weight: Weight value (0.0-1.0)
            - mode: Assign mode (REPLACE, ADD, SUBTRACT)
    """
    object_name = params.get("object_name", "")
    group_name = params.get("group_name", "")
    vertex_indices = params.get("vertex_indices", [])
    weight = params.get("weight", 1.0)
    mode = params.get("mode", "REPLACE")

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Mesh object not found: {object_name}",
            },
        }

    vg = obj.vertex_groups.get(group_name)
    if not vg:
        return {
            "success": False,
            "error": {
                "code": "GROUP_NOT_FOUND",
                "message": f"Vertex group not found: {group_name}",
            },
        }

    # Assign vertices
    vg.add(vertex_indices, weight, mode)

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "group_name": vg.name,
            "assigned_count": len(vertex_indices),
        },
    }


def handle_bone_constraint_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add constraint to bone

    Args:
        params:
            - armature_name: Armature name
            - bone_name: Bone name
            - constraint_type: Constraint type (IK, COPY_ROTATION, COPY_LOCATION, LIMIT_ROTATION, etc.)
            - settings: Constraint settings
    """
    armature_name = params.get("armature_name", "")
    bone_name = params.get("bone_name", "")
    constraint_type = params.get("constraint_type")
    settings = params.get("settings", {})

    obj = bpy.data.objects.get(armature_name)
    if not obj or obj.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    # Switch to pose mode
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="POSE")

    pose_bone = obj.pose.bones.get(bone_name)
    if not pose_bone:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {
            "success": False,
            "error": {"code": "BONE_NOT_FOUND", "message": f"Bone not found: {bone_name}"},
        }

    # Add constraint
    try:
        constraint = pose_bone.constraints.new(type=constraint_type)

        # Apply settings
        for key, value in settings.items():
            if hasattr(constraint, key):
                # Handle object references
                if key in ["target", "pole_target"] and isinstance(value, str):
                    target_obj = bpy.data.objects.get(value)
                    if target_obj:
                        setattr(constraint, key, target_obj)
                else:
                    setattr(constraint, key, value)

        bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "success": True,
            "data": {
                "armature_name": obj.name,
                "bone_name": bone_name,
                "constraint_name": constraint.name,
                "constraint_type": constraint_type,
            },
        }
    except Exception as e:
        bpy.ops.object.mode_set(mode="OBJECT")
        return {"success": False, "error": {"code": "CONSTRAINT_ERROR", "message": str(e)}}
