"""
Hair System Handler

Handles hair creation and editing commands.
"""

from typing import Any

import bpy


def handle_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add hair system"""
    object_name = params.get("object_name", "")
    name = params.get("name", "Hair")
    hair_length = params.get("hair_length", 0.1)
    hair_count = params.get("hair_count", 1000)
    segments = params.get("segments", 5)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Mesh object not found: {object_name}",
            },
        }

    try:
        # Select object
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Add particle system
        bpy.ops.object.particle_system_add()

        ps = obj.particle_systems[-1]
        ps.name = name

        settings = ps.settings
        settings.type = "HAIR"
        settings.hair_length = hair_length
        settings.count = hair_count
        settings.hair_step = segments

        return {
            "success": True,
            "data": {"object_name": obj.name, "system_name": ps.name, "hair_count": hair_count},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_ADD_ERROR", "message": str(e)}}


def handle_settings(params: dict[str, Any]) -> dict[str, Any]:
    """Set hair properties"""
    object_name = params.get("object_name", "")
    system_name = params.get("system_name", "")
    hair_length = params.get("hair_length")
    root_radius = params.get("root_radius")
    tip_radius = params.get("tip_radius")
    random_length = params.get("random_length")
    random_rotation = params.get("random_rotation")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Get particle system
        ps = None
        if system_name:
            ps = obj.particle_systems.get(system_name)
        elif len(obj.particle_systems) > 0:
            ps = obj.particle_systems[-1]

        if not ps:
            return {
                "success": False,
                "error": {"code": "NO_PARTICLE_SYSTEM", "message": "No particle system found"},
            }

        settings = ps.settings

        if hair_length is not None:
            settings.hair_length = hair_length
        if root_radius is not None:
            settings.root_radius = root_radius
        if tip_radius is not None:
            settings.tip_radius = tip_radius
        if random_length is not None:
            settings.length_random = random_length
        if random_rotation is not None:
            settings.phase_factor_random = random_rotation

        return {"success": True, "data": {"system_name": ps.name}}
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_SETTINGS_ERROR", "message": str(e)}}


def handle_dynamics(params: dict[str, Any]) -> dict[str, Any]:
    """Set hair dynamics"""
    object_name = params.get("object_name", "")
    enable = params.get("enable", True)
    stiffness = params.get("stiffness", 0.5)
    damping = params.get("damping", 0.1)
    gravity = params.get("gravity", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Get particle system
        if len(obj.particle_systems) == 0:
            return {
                "success": False,
                "error": {"code": "NO_PARTICLE_SYSTEM", "message": "No particle system found"},
            }

        ps = obj.particle_systems[-1]
        settings = ps.settings

        # Enable/disable dynamics
        settings.use_hair_dynamics = enable

        if enable:
            # Set dynamics parameters
            cloth = settings.cloth
            cloth.settings.quality = 5
            cloth.settings.mass = 0.3
            cloth.settings.bending_stiffness = stiffness * 100
            cloth.settings.air_damping = damping * 10

            # Gravity
            settings.effector_weights.gravity = gravity

        return {"success": True, "data": {"dynamics_enabled": enable}}
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_DYNAMICS_ERROR", "message": str(e)}}


def handle_material(params: dict[str, Any]) -> dict[str, Any]:
    """Set hair material"""
    object_name = params.get("object_name", "")
    color = params.get("color", [0.1, 0.05, 0.02, 1.0])
    roughness = params.get("roughness", 0.4)
    use_hair_bsdf = params.get("use_hair_bsdf", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Create hair material
        mat = bpy.data.materials.new(name=f"{object_name}_Hair_Material")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create output node
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

        if use_hair_bsdf:
            # Use Principled Hair BSDF
            hair_bsdf = nodes.new("ShaderNodeBsdfHairPrincipled")
            hair_bsdf.location = (0, 0)
            hair_bsdf.inputs["Color"].default_value = (
                color[:4] if len(color) >= 4 else color + [1.0]
            )
            hair_bsdf.inputs["Roughness"].default_value = roughness

            links.new(hair_bsdf.outputs["BSDF"], output.inputs["Surface"])
        else:
            # Use Principled BSDF
            bsdf = nodes.new("ShaderNodeBsdfPrincipled")
            bsdf.location = (0, 0)
            bsdf.inputs["Base Color"].default_value = (
                color[:4] if len(color) >= 4 else color + [1.0]
            )
            bsdf.inputs["Roughness"].default_value = roughness

            links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Assign material to particle system
        obj.data.materials.append(mat)

        if len(obj.particle_systems) > 0:
            ps = obj.particle_systems[-1]
            # Blender 5.0: material_slot requires the material slot name string
            ps.settings.material_slot = mat.name

        return {"success": True, "data": {"material_name": mat.name}}
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_MATERIAL_ERROR", "message": str(e)}}


def handle_children(params: dict[str, Any]) -> dict[str, Any]:
    """Set hair children"""
    object_name = params.get("object_name", "")
    child_type = params.get("child_type", "INTERPOLATED")
    child_count = params.get("child_count", 10)
    clump = params.get("clump", 0.0)
    roughness = params.get("roughness", 0.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        if len(obj.particle_systems) == 0:
            return {
                "success": False,
                "error": {"code": "NO_PARTICLE_SYSTEM", "message": "No particle system found"},
            }

        ps = obj.particle_systems[-1]
        settings = ps.settings

        settings.child_type = child_type

        if child_type != "NONE":
            settings.rendered_child_count = child_count
            settings.child_length = 1.0
            settings.clump_factor = clump
            settings.roughness_1 = roughness

        return {"success": True, "data": {"child_type": child_type, "child_count": child_count}}
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_CHILDREN_ERROR", "message": str(e)}}


def handle_groom(params: dict[str, Any]) -> dict[str, Any]:
    """Hair grooming operations"""
    object_name = params.get("object_name", "")
    action = params.get("action", "COMB")
    strength = params.get("strength", 0.5)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Select object
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Enter particle edit mode
        bpy.ops.object.mode_set(mode="PARTICLE_EDIT")

        # Set tool
        tool_settings = bpy.context.tool_settings.particle_edit

        action_map = {
            "COMB": "COMB",
            "CUT": "CUT",
            "LENGTH": "LENGTH",
            "PUFF": "PUFF",
            "SMOOTH": "SMOOTH",
        }

        if action in action_map:
            tool_settings.tool = action_map[action]
            tool_settings.brush.strength = strength

        # Return to object mode
        bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "success": True,
            "data": {
                "action": action,
                "strength": strength,
                "note": "Groom tool configured. Use Blender UI for manual grooming.",
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_GROOM_ERROR", "message": str(e)}}
