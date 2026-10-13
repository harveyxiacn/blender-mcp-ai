"""
Physics Simulation Handler

Handles cloth, rigid body, particle system and other physics simulation commands.
Enhanced version - supports more presets and automatic pinning functionality.
"""

from typing import Any

import bpy

from .compat import select_only

# Enhanced cloth preset configuration
CLOTH_PRESETS = {
    # Basic fabrics
    "cotton": {
        "description": "Cotton - everyday clothing",
        "mass": 0.3,
        "air_damping": 1.0,
        "tension_stiffness": 15,
        "compression_stiffness": 15,
        "shear_stiffness": 15,
        "bending_stiffness": 0.5,
        "damping": 0.01,
        "collision_distance": 0.015,
    },
    "silk": {
        "description": "Silk - light and flowing",
        "mass": 0.15,
        "air_damping": 1.0,
        "tension_stiffness": 5,
        "compression_stiffness": 5,
        "shear_stiffness": 5,
        "bending_stiffness": 0.05,
        "damping": 0.005,
        "collision_distance": 0.01,
    },
    "leather": {
        "description": "Leather - thick and stiff",
        "mass": 0.4,
        "air_damping": 1.0,
        "tension_stiffness": 80,
        "compression_stiffness": 80,
        "shear_stiffness": 80,
        "bending_stiffness": 15,
        "damping": 0.1,
        "collision_distance": 0.02,
    },
    "denim": {
        "description": "Denim - medium stiffness",
        "mass": 0.4,
        "air_damping": 1.0,
        "tension_stiffness": 40,
        "compression_stiffness": 40,
        "shear_stiffness": 40,
        "bending_stiffness": 10,
        "damping": 0.05,
        "collision_distance": 0.015,
    },
    "rubber": {
        "description": "Rubber - elastic material",
        "mass": 0.3,
        "air_damping": 1.0,
        "tension_stiffness": 15,
        "compression_stiffness": 15,
        "shear_stiffness": 15,
        "bending_stiffness": 25,
        "damping": 0.02,
        "collision_distance": 0.01,
    },
    # Additional presets
    "linen": {
        "description": "Linen - natural texture",
        "mass": 0.28,
        "air_damping": 1.0,
        "tension_stiffness": 18,
        "compression_stiffness": 18,
        "shear_stiffness": 18,
        "bending_stiffness": 0.8,
        "damping": 0.015,
        "collision_distance": 0.015,
    },
    "velvet": {
        "description": "Velvet - heavy and soft",
        "mass": 0.35,
        "air_damping": 1.2,
        "tension_stiffness": 12,
        "compression_stiffness": 12,
        "shear_stiffness": 12,
        "bending_stiffness": 0.3,
        "damping": 0.02,
        "collision_distance": 0.018,
    },
    "chiffon": {
        "description": "Chiffon - ultra-light and sheer",
        "mass": 0.08,
        "air_damping": 0.8,
        "tension_stiffness": 3,
        "compression_stiffness": 3,
        "shear_stiffness": 3,
        "bending_stiffness": 0.02,
        "damping": 0.003,
        "collision_distance": 0.008,
    },
    "wool": {
        "description": "Wool - warm and thick",
        "mass": 0.38,
        "air_damping": 1.3,
        "tension_stiffness": 25,
        "compression_stiffness": 25,
        "shear_stiffness": 25,
        "bending_stiffness": 2.0,
        "damping": 0.04,
        "collision_distance": 0.02,
    },
    "satin": {
        "description": "Satin - smooth and shiny",
        "mass": 0.2,
        "air_damping": 0.9,
        "tension_stiffness": 8,
        "compression_stiffness": 8,
        "shear_stiffness": 8,
        "bending_stiffness": 0.1,
        "damping": 0.008,
        "collision_distance": 0.012,
    },
    # Special materials
    "chainmail": {
        "description": "Chainmail - metal weave",
        "mass": 1.5,
        "air_damping": 0.5,
        "tension_stiffness": 200,
        "compression_stiffness": 200,
        "shear_stiffness": 50,
        "bending_stiffness": 5,
        "damping": 0.15,
        "collision_distance": 0.025,
    },
    "cape_heavy": {
        "description": "Heavy cape - hero cape",
        "mass": 0.5,
        "air_damping": 1.5,
        "tension_stiffness": 30,
        "compression_stiffness": 30,
        "shear_stiffness": 30,
        "bending_stiffness": 3,
        "damping": 0.05,
        "collision_distance": 0.02,
    },
    "cape_light": {
        "description": "Light cape - flowing cape",
        "mass": 0.18,
        "air_damping": 0.7,
        "tension_stiffness": 8,
        "compression_stiffness": 8,
        "shear_stiffness": 8,
        "bending_stiffness": 0.15,
        "damping": 0.01,
        "collision_distance": 0.012,
    },
    "flag": {
        "description": "Flag - fluttering in the wind",
        "mass": 0.12,
        "air_damping": 0.5,
        "tension_stiffness": 20,
        "compression_stiffness": 20,
        "shear_stiffness": 20,
        "bending_stiffness": 0.08,
        "damping": 0.005,
        "collision_distance": 0.01,
    },
    "paper": {
        "description": "Paper - thin and light",
        "mass": 0.05,
        "air_damping": 0.6,
        "tension_stiffness": 50,
        "compression_stiffness": 50,
        "shear_stiffness": 50,
        "bending_stiffness": 0.5,
        "damping": 0.002,
        "collision_distance": 0.005,
    },
    # Chinese traditional / Xianxia style
    "hanfu_outer": {
        "description": "Hanfu outer robe - flowing and elegant",
        "mass": 0.22,
        "air_damping": 0.9,
        "tension_stiffness": 10,
        "compression_stiffness": 10,
        "shear_stiffness": 10,
        "bending_stiffness": 0.15,
        "damping": 0.01,
        "collision_distance": 0.012,
    },
    "hanfu_inner": {
        "description": "Hanfu inner garment - close-fitting and soft",
        "mass": 0.18,
        "air_damping": 1.0,
        "tension_stiffness": 8,
        "compression_stiffness": 8,
        "shear_stiffness": 8,
        "bending_stiffness": 0.1,
        "damping": 0.008,
        "collision_distance": 0.01,
    },
    "ribbon": {
        "description": "Ribbon/sash - light and flowing",
        "mass": 0.06,
        "air_damping": 0.5,
        "tension_stiffness": 5,
        "compression_stiffness": 5,
        "shear_stiffness": 5,
        "bending_stiffness": 0.03,
        "damping": 0.003,
        "collision_distance": 0.008,
    },
}


# Pin point mode configuration
PIN_MODES = {
    "top": {"description": "Pin at top", "threshold_ratio": 0.9},
    "top_edge": {"description": "Pin at top edge", "threshold_ratio": 0.95},
    "shoulder": {"description": "Pin at shoulders (clothing)", "z_range": (0.85, 0.95)},
    "waist": {"description": "Pin at waist", "z_range": (0.45, 0.55)},
    "collar": {"description": "Pin at collar", "z_range": (0.90, 1.0), "y_threshold": 0.3},
    "armhole": {"description": "Pin at armhole", "x_threshold": 0.8},
    "hem": {"description": "Pin at hem", "threshold_ratio": 0.1},
    "custom": {"description": "Custom pinning"},
}


def handle_cloth_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add cloth simulation (enhanced version)"""
    object_name = params.get("object_name", "")
    preset = params.get("preset", "cotton")
    pin_group = params.get("pin_group")
    pin_mode = params.get("pin_mode")  # Automatic pin mode
    collision_quality = params.get("collision_quality", 2)
    self_collision = params.get("self_collision", False)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {object_name}"},
        }

    # Select object (Blender 5.x safe)
    select_only(obj)

    # Add cloth modifier
    cloth_mod = obj.modifiers.new(name="Cloth", type="CLOTH")
    if cloth_mod is None:
        return {
            "success": False,
            "error": {
                "code": "MODIFIER_FAILED",
                "message": f"Failed to add Cloth modifier to {object_name}",
            },
        }
    cloth = cloth_mod.settings

    # Apply preset
    preset_config = CLOTH_PRESETS.get(preset, CLOTH_PRESETS["cotton"])
    cloth.mass = preset_config["mass"]
    cloth.air_damping = preset_config["air_damping"]
    cloth.tension_stiffness = preset_config["tension_stiffness"]
    cloth.compression_stiffness = preset_config["compression_stiffness"]
    cloth.shear_stiffness = preset_config["shear_stiffness"]
    cloth.bending_stiffness = preset_config["bending_stiffness"]

    # Extra settings
    if "damping" in preset_config:
        cloth.bending_damping = preset_config["damping"]

    # Collision settings
    # In Blender 5.0+, collision_settings moved from ClothSettings to the modifier itself
    if hasattr(cloth, "collision_settings"):
        collision_settings = cloth.collision_settings
    elif hasattr(cloth_mod, "collision_settings"):
        collision_settings = cloth_mod.collision_settings
    else:
        collision_settings = None

    if collision_settings is not None:
        collision_settings.collision_quality = collision_quality
        if "collision_distance" in preset_config:
            collision_settings.distance_min = preset_config["collision_distance"]

        # Self collision
        if self_collision:
            collision_settings.use_self_collision = True
            collision_settings.self_distance_min = preset_config.get("collision_distance", 0.015)
    elif self_collision:
        # Couldn't find collision_settings, but self_collision was requested
        pass  # silently skip if collision_settings unavailable

    # Automatic pin points
    created_pin_group = None
    if pin_mode and pin_mode != "custom":
        created_pin_group = _create_auto_pin_group(obj, pin_mode)
        if created_pin_group:
            cloth.vertex_group_mass = created_pin_group
    elif pin_group and pin_group in obj.vertex_groups:
        cloth.vertex_group_mass = pin_group

    return {
        "success": True,
        "data": {
            "preset": preset,
            "description": preset_config.get("description", ""),
            "pin_group": created_pin_group or pin_group,
            "self_collision": self_collision,
        },
    }


def _create_auto_pin_group(obj: bpy.types.Object, pin_mode: str) -> str | None:
    """Create automatic pin vertex group"""
    mode_config = PIN_MODES.get(pin_mode)
    if not mode_config:
        return None

    # Calculate mesh bounds
    verts = obj.data.vertices
    if len(verts) == 0:
        return None

    min_z = min(v.co.z for v in verts)
    max_z = max(v.co.z for v in verts)
    height = max_z - min_z

    min_x = min(v.co.x for v in verts)
    max_x = max(v.co.x for v in verts)
    width = max_x - min_x

    min_y = min(v.co.y for v in verts)
    max_y = max(v.co.y for v in verts)
    depth = max_y - min_y

    # Create vertex group
    group_name = f"Pin_{pin_mode}"
    if group_name in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups[group_name])
    pin_group = obj.vertex_groups.new(name=group_name)

    # Select vertices by mode
    for v in verts:
        weight = 0.0
        normalized_z = (v.co.z - min_z) / height if height > 0 else 0
        normalized_x = (v.co.x - min_x) / width if width > 0 else 0
        normalized_y = (v.co.y - min_y) / depth if depth > 0 else 0

        if pin_mode == "top":
            threshold = mode_config.get("threshold_ratio", 0.9)
            if normalized_z >= threshold:
                weight = (normalized_z - threshold) / (1 - threshold)

        elif pin_mode == "top_edge":
            threshold = mode_config.get("threshold_ratio", 0.95)
            if normalized_z >= threshold:
                weight = 1.0

        elif pin_mode == "shoulder":
            z_range = mode_config.get("z_range", (0.85, 0.95))
            if z_range[0] <= normalized_z <= z_range[1]:
                # Shoulder position, both sides
                if abs(normalized_x - 0.5) > 0.3:
                    weight = 1.0 - abs(normalized_z - (z_range[0] + z_range[1]) / 2) / 0.1

        elif pin_mode == "waist":
            z_range = mode_config.get("z_range", (0.45, 0.55))
            if z_range[0] <= normalized_z <= z_range[1]:
                weight = 1.0 - abs(normalized_z - (z_range[0] + z_range[1]) / 2) / 0.05

        elif pin_mode == "collar":
            z_range = mode_config.get("z_range", (0.90, 1.0))
            y_threshold = mode_config.get("y_threshold", 0.3)
            if z_range[0] <= normalized_z <= z_range[1]:
                # Collar position, front
                if normalized_y < y_threshold:
                    weight = 1.0

        elif pin_mode == "hem":
            threshold = mode_config.get("threshold_ratio", 0.1)
            if normalized_z <= threshold:
                weight = (threshold - normalized_z) / threshold

        if weight > 0:
            pin_group.add([v.index], min(1.0, max(0.0, weight)), "REPLACE")

    return group_name


def handle_cloth_list_presets(params: dict[str, Any]) -> dict[str, Any]:
    """List all cloth presets"""
    presets_info = {}
    for name, config in CLOTH_PRESETS.items():
        presets_info[name] = {
            "description": config.get("description", name),
            "mass": config["mass"],
            "stiffness": config["tension_stiffness"],
        }

    return {"success": True, "data": {"presets": presets_info, "count": len(presets_info)}}


def handle_cloth_configure(params: dict[str, Any]) -> dict[str, Any]:
    """Configure cloth simulation parameters"""
    object_name = params.get("object_name", "")

    # Configurable parameters
    mass = params.get("mass")
    air_damping = params.get("air_damping")
    tension_stiffness = params.get("tension_stiffness")
    compression_stiffness = params.get("compression_stiffness")
    shear_stiffness = params.get("shear_stiffness")
    bending_stiffness = params.get("bending_stiffness")
    gravity = params.get("gravity")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Find cloth modifier
    cloth_mod = None
    for mod in obj.modifiers:
        if mod.type == "CLOTH":
            cloth_mod = mod
            break

    if not cloth_mod:
        return {
            "success": False,
            "error": {"code": "NO_CLOTH_MOD", "message": "Object has no cloth modifier"},
        }

    cloth = cloth_mod.settings

    # Apply parameters
    if mass is not None:
        cloth.mass = mass
    if air_damping is not None:
        cloth.air_damping = air_damping
    if tension_stiffness is not None:
        cloth.tension_stiffness = tension_stiffness
    if compression_stiffness is not None:
        cloth.compression_stiffness = compression_stiffness
    if shear_stiffness is not None:
        cloth.shear_stiffness = shear_stiffness
    if bending_stiffness is not None:
        cloth.bending_stiffness = bending_stiffness
    if gravity is not None:
        cloth.effector_weights.gravity = gravity

    return {"success": True, "data": {"configured": True}}


def handle_rigid_body_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add rigid body"""
    object_name = params.get("object_name", "")
    body_type = params.get("body_type", "ACTIVE")
    shape = params.get("shape", "CONVEX_HULL")
    mass = params.get("mass", 1.0)
    friction = params.get("friction", 0.5)
    bounciness = params.get("bounciness", 0.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Ensure rigid body world exists
    if not bpy.context.scene.rigidbody_world:
        bpy.ops.rigidbody.world_add()

    # Select object (Blender 5.x safe)
    select_only(obj)

    # Add rigid body
    bpy.ops.rigidbody.object_add()

    # Set properties
    obj.rigid_body.type = body_type
    obj.rigid_body.collision_shape = shape
    obj.rigid_body.mass = mass
    obj.rigid_body.friction = friction
    obj.rigid_body.restitution = bounciness

    return {"success": True, "data": {"body_type": body_type, "shape": shape}}


def handle_collision_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add collision body"""
    object_name = params.get("object_name", "")
    damping = params.get("damping", 0.0)
    thickness = params.get("thickness", 0.02)
    friction = params.get("friction", 0.0)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {object_name}"},
        }

    # Reuse an existing collision modifier if present, otherwise create one.
    # COLLISION settings are only populated after the object is in the view
    # layer and the depsgraph updates, so select it first.
    select_only(obj)
    collision_mod = next((m for m in obj.modifiers if m.type == "COLLISION"), None)
    if collision_mod is None:
        collision_mod = obj.modifiers.new(name="Collision", type="COLLISION")
    if collision_mod is None:
        return {
            "success": False,
            "error": {
                "code": "MODIFIER_FAILED",
                "message": f"Failed to add Collision modifier to {object_name}",
            },
        }

    # settings may be None until the depsgraph evaluates the new modifier
    collision = collision_mod.settings
    if collision is None:
        bpy.context.view_layer.update()
        collision = collision_mod.settings
    if collision is None:
        return {
            "success": True,
            "data": {"note": "Collision modifier added; settings will populate on next update"},
        }

    collision.damping = damping
    collision.thickness_outer = thickness
    collision.friction_factor = friction

    return {"success": True, "data": {}}


def handle_particles_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create particle system"""
    object_name = params.get("object_name", "")
    particle_type = params.get("particle_type", "EMITTER")
    count = params.get("count", 1000)
    lifetime = params.get("lifetime", 50.0)
    emit_from = params.get("emit_from", "FACE")
    velocity_normal = params.get("velocity_normal", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {object_name}"},
        }

    # Add particle system
    obj.modifiers.new(name="ParticleSystem", type="PARTICLE_SYSTEM")
    particle_system = obj.particle_systems[-1]
    settings = particle_system.settings

    # Set properties
    settings.type = particle_type
    settings.count = count
    settings.lifetime = lifetime
    settings.emit_from = emit_from
    settings.normal_factor = velocity_normal

    return {"success": True, "data": {"particle_system": particle_system.name, "count": count}}


def handle_force_field_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add force field"""
    force_type = params.get("force_type", "WIND")
    location = params.get("location", [0, 0, 0])
    strength = params.get("strength", 1.0)
    flow = params.get("flow", 0.0)

    # Create empty object as force field
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    force_obj = bpy.context.active_object
    force_obj.name = f"ForceField_{force_type}"

    # Add force field
    bpy.ops.object.forcefield_toggle()
    force_obj.field.type = force_type
    force_obj.field.strength = strength
    force_obj.field.flow = flow

    return {"success": True, "data": {"force_field_name": force_obj.name, "force_type": force_type}}


def handle_soft_body_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add soft body"""
    object_name = params.get("object_name", "")
    mass = params.get("mass", 1.0)
    friction = params.get("friction", 0.5)
    goal_strength = params.get("goal_strength", 0.7)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "MESH_NOT_FOUND", "message": f"Mesh not found: {object_name}"},
        }

    # Add soft body modifier
    soft_body_mod = obj.modifiers.new(name="Softbody", type="SOFT_BODY")
    soft_body = soft_body_mod.settings

    soft_body.mass = mass
    soft_body.friction = friction
    soft_body.goal_default = goal_strength

    return {"success": True, "data": {}}
