"""
Character handler

Handles character-related commands, including advanced character creation, facial system, clothing system, etc.
"""

from typing import Any

import bpy


def get_principled_bsdf(nodes):
    """Get Principled BSDF node, compatible with different Blender versions"""
    # First try to find by name
    bsdf = nodes.get("Principled BSDF")
    if bsdf:
        return bsdf
    # Then try to find by type
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            return node
    return None


import bmesh

# ==================== Face Shape Key Configuration ====================
FACE_SHAPE_KEYS = {
    # Eye related
    "eye_size": {"min": 0.5, "max": 1.5, "default": 1.0},
    "eye_distance": {"min": 0.8, "max": 1.2, "default": 1.0},
    "eye_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "eye_tilt": {"min": -0.3, "max": 0.3, "default": 0.0},
    "eye_depth": {"min": 0.8, "max": 1.2, "default": 1.0},
    # Nose related
    "nose_length": {"min": 0.5, "max": 1.5, "default": 1.0},
    "nose_width": {"min": 0.7, "max": 1.3, "default": 1.0},
    "nose_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "nose_tip": {"min": 0.8, "max": 1.2, "default": 1.0},
    # Mouth related
    "mouth_width": {"min": 0.7, "max": 1.3, "default": 1.0},
    "mouth_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "lip_thickness_upper": {"min": 0.5, "max": 1.5, "default": 1.0},
    "lip_thickness_lower": {"min": 0.5, "max": 1.5, "default": 1.0},
    # Jaw and face shape
    "jaw_width": {"min": 0.7, "max": 1.3, "default": 1.0},
    "jaw_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "chin_length": {"min": 0.8, "max": 1.2, "default": 1.0},
    "cheekbone_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "cheekbone_width": {"min": 0.8, "max": 1.2, "default": 1.0},
    # Forehead
    "forehead_height": {"min": 0.8, "max": 1.2, "default": 1.0},
    "forehead_width": {"min": 0.8, "max": 1.2, "default": 1.0},
    # Ears
    "ear_size": {"min": 0.7, "max": 1.3, "default": 1.0},
    "ear_position": {"min": 0.8, "max": 1.2, "default": 1.0},
}


# ==================== Clothing Template Configuration ====================
CLOTHING_TEMPLATES = {
    "SHIRT": {
        "description": "Basic top",
        "scale": (1.08, 1.06, 0.35),
        "offset": (0, 0, 0.65),
        "vertex_groups": ["torso_upper", "arms"],
        "cloth_preset": "cotton",
    },
    "T_SHIRT": {
        "description": "T-shirt",
        "scale": (1.06, 1.04, 0.30),
        "offset": (0, 0, 0.68),
        "vertex_groups": ["torso_upper"],
        "cloth_preset": "cotton",
    },
    "PANTS": {
        "description": "Trousers",
        "scale": (1.04, 1.04, 0.50),
        "offset": (0, 0, 0.25),
        "vertex_groups": ["legs"],
        "cloth_preset": "denim",
    },
    "SHORTS": {
        "description": "Shorts",
        "scale": (1.05, 1.05, 0.25),
        "offset": (0, 0, 0.35),
        "vertex_groups": ["legs_upper"],
        "cloth_preset": "cotton",
    },
    "JACKET": {
        "description": "Jacket",
        "scale": (1.12, 1.10, 0.40),
        "offset": (0, 0, 0.60),
        "vertex_groups": ["torso_upper", "arms"],
        "cloth_preset": "leather",
    },
    "COAT": {
        "description": "Coat",
        "scale": (1.15, 1.12, 0.70),
        "offset": (0, 0, 0.45),
        "vertex_groups": ["torso", "arms"],
        "cloth_preset": "leather",
    },
    "DRESS": {
        "description": "Dress",
        "scale": (1.06, 1.04, 0.65),
        "offset": (0, 0, 0.50),
        "vertex_groups": ["torso", "legs_upper"],
        "cloth_preset": "silk",
    },
    "SKIRT": {
        "description": "Skirt",
        "scale": (1.08, 1.06, 0.35),
        "offset": (0, 0, 0.30),
        "vertex_groups": ["legs_upper"],
        "cloth_preset": "silk",
    },
    "ROBE": {
        "description": "Robe (ancient/fantasy style)",
        "scale": (1.10, 1.08, 0.85),
        "offset": (0, 0, 0.40),
        "vertex_groups": ["torso", "arms", "legs"],
        "cloth_preset": "silk",
    },
    "HANFU_TOP": {
        "description": "Hanfu upper garment",
        "scale": (1.12, 1.08, 0.45),
        "offset": (0, 0, 0.58),
        "vertex_groups": ["torso_upper", "arms"],
        "cloth_preset": "silk",
    },
    "HANFU_BOTTOM": {
        "description": "Hanfu lower garment",
        "scale": (1.10, 1.08, 0.60),
        "offset": (0, 0, 0.25),
        "vertex_groups": ["legs"],
        "cloth_preset": "silk",
    },
    "ARMOR_CHEST": {
        "description": "Chest armor",
        "scale": (1.15, 1.12, 0.35),
        "offset": (0, 0, 0.65),
        "vertex_groups": ["torso_upper"],
        "cloth_preset": "leather",
    },
    "ARMOR_FULL": {
        "description": "Full body armor",
        "scale": (1.18, 1.15, 0.90),
        "offset": (0, 0, 0.45),
        "vertex_groups": ["torso", "arms", "legs"],
        "cloth_preset": "leather",
    },
    "CAPE": {
        "description": "Cape",
        "scale": (1.20, 0.15, 0.80),
        "offset": (0, -0.15, 0.55),
        "vertex_groups": ["back"],
        "cloth_preset": "silk",
    },
    "SHOES": {
        "description": "Shoes",
        "scale": (1.05, 1.15, 0.08),
        "offset": (0, 0, 0.04),
        "vertex_groups": ["feet"],
        "cloth_preset": "leather",
    },
    "BOOTS": {
        "description": "Boots",
        "scale": (1.06, 1.12, 0.25),
        "offset": (0, 0, 0.12),
        "vertex_groups": ["feet", "lower_legs"],
        "cloth_preset": "leather",
    },
    "GLOVES": {
        "description": "Gloves",
        "scale": (1.03, 1.03, 0.15),
        "offset": (0, 0, 0),
        "vertex_groups": ["hands"],
        "cloth_preset": "leather",
    },
    "HAT": {
        "description": "Hat",
        "scale": (1.10, 1.10, 0.15),
        "offset": (0, 0, 0.95),
        "vertex_groups": ["head"],
        "cloth_preset": "cotton",
    },
    "HELMET": {
        "description": "Helmet",
        "scale": (1.12, 1.12, 0.20),
        "offset": (0, 0, 0.93),
        "vertex_groups": ["head"],
        "cloth_preset": "leather",
    },
}


# ==================== Cloth Preset Configuration ====================
CLOTH_PRESETS = {
    "cotton": {
        "mass": 0.3,
        "air_damping": 1.0,
        "tension_stiffness": 15,
        "compression_stiffness": 15,
        "shear_stiffness": 15,
        "bending_stiffness": 0.5,
    },
    "silk": {
        "mass": 0.15,
        "air_damping": 1.0,
        "tension_stiffness": 5,
        "compression_stiffness": 5,
        "shear_stiffness": 5,
        "bending_stiffness": 0.05,
    },
    "leather": {
        "mass": 0.4,
        "air_damping": 1.0,
        "tension_stiffness": 80,
        "compression_stiffness": 80,
        "shear_stiffness": 80,
        "bending_stiffness": 15,
    },
    "denim": {
        "mass": 0.4,
        "air_damping": 1.0,
        "tension_stiffness": 40,
        "compression_stiffness": 40,
        "shear_stiffness": 40,
        "bending_stiffness": 10,
    },
}


def handle_create_humanoid(params: dict[str, Any]) -> dict[str, Any]:
    """Create humanoid character (enhanced version)"""
    name = params.get("name", "Character")
    height = params.get("height", 1.8)
    body_type = params.get("body_type", "AVERAGE")
    gender = params.get("gender", "NEUTRAL")
    subdivisions = params.get("subdivisions", 2)
    create_face_rig = params.get("create_face_rig", True)

    # Body type parameters - finer control
    body_params = {
        "SLIM": {"width": 0.8, "depth": 0.7, "shoulder": 0.9, "hip": 0.85},
        "AVERAGE": {"width": 1.0, "depth": 1.0, "shoulder": 1.0, "hip": 1.0},
        "MUSCULAR": {"width": 1.2, "depth": 1.1, "shoulder": 1.25, "hip": 0.95},
        "HEAVY": {"width": 1.3, "depth": 1.3, "shoulder": 1.1, "hip": 1.2},
    }

    # Gender difference parameters
    gender_params = {
        "MALE": {"shoulder_ratio": 1.1, "hip_ratio": 0.9, "chest": 1.0},
        "FEMALE": {"shoulder_ratio": 0.9, "hip_ratio": 1.1, "chest": 1.15},
        "NEUTRAL": {"shoulder_ratio": 1.0, "hip_ratio": 1.0, "chest": 1.0},
    }

    bp = body_params.get(body_type, body_params["AVERAGE"])
    gp = gender_params.get(gender, gender_params["NEUTRAL"])
    scale = height / 1.8

    try:
        # Create more detailed body base mesh
        body = _create_detailed_body_mesh(name, height, bp, gp, scale, subdivisions)

        # Create facial shape key basis
        if create_face_rig:
            _create_face_shape_keys(body)

        # Create basic vertex groups (for clothing binding)
        _create_body_vertex_groups(body)

        return {
            "success": True,
            "data": {
                "character_name": body.name,
                "height": height,
                "body_type": body_type,
                "gender": gender,
                "has_face_rig": create_face_rig,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "CHARACTER_CREATE_ERROR", "message": str(e)}}


def _create_detailed_body_mesh(
    name: str, height: float, bp: dict, gp: dict, scale: float, subdivisions: int
) -> bpy.types.Object:
    """Create detailed body mesh"""
    # Create torso
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height * 0.55))
    body = bpy.context.active_object
    body.name = name

    # Set torso dimensions
    torso_width = 0.35 * bp["width"] * gp["shoulder_ratio"] * scale
    torso_depth = 0.2 * bp["depth"] * scale
    torso_height = height * 0.35
    body.scale = (torso_width, torso_depth, torso_height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # Enter edit mode for detail adjustments
    bpy.ops.object.mode_set(mode="EDIT")
    bm = bmesh.from_edit_mesh(body.data)

    # Adjust vertex positions for more natural torso shape
    for v in bm.verts:
        # Narrow the waist
        if abs(v.co.z - height * 0.45) < height * 0.1:
            v.co.x *= 0.85
            v.co.y *= 0.9
        # Expand chest
        if v.co.z > height * 0.5:
            v.co.x *= gp["chest"]
        # Expand hips
        if v.co.z < height * 0.4:
            v.co.x *= gp["hip_ratio"]

    bmesh.update_edit_mesh(body.data)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Add modifiers
    if subdivisions > 0:
        mod = body.modifiers.new(name="Subdivision", type="SUBSURF")
        mod.levels = min(subdivisions, 2)  # Viewport subdivision
        mod.render_levels = subdivisions

    # Add smooth modifier
    mod_smooth = body.modifiers.new(name="Smooth", type="SMOOTH")
    mod_smooth.factor = 0.5
    mod_smooth.iterations = 2

    return body


def _create_face_shape_keys(obj: bpy.types.Object) -> None:
    """Create facial shape keys"""
    # Ensure object has mesh data
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)

    # Create shape key for each facial parameter
    for key_name, config in FACE_SHAPE_KEYS.items():
        sk = obj.shape_key_add(name=key_name, from_mix=False)
        sk.value = config["default"]
        sk.slider_min = config["min"]
        sk.slider_max = config["max"]


def _create_body_vertex_groups(obj: bpy.types.Object) -> None:
    """Create body vertex groups (for clothing and rigging)"""
    vertex_group_names = [
        "head",
        "neck",
        "torso",
        "torso_upper",
        "torso_lower",
        "arms",
        "arm_L",
        "arm_R",
        "forearm_L",
        "forearm_R",
        "hands",
        "hand_L",
        "hand_R",
        "legs",
        "legs_upper",
        "thigh_L",
        "thigh_R",
        "lower_legs",
        "shin_L",
        "shin_R",
        "feet",
        "foot_L",
        "foot_R",
        "back",
        "spine",
    ]

    for name in vertex_group_names:
        if name not in obj.vertex_groups:
            obj.vertex_groups.new(name=name)


def handle_add_face_features(params: dict[str, Any]) -> dict[str, Any]:
    """Add facial features (enhanced - using shape keys)"""
    character_name = params.get("character_name", "")

    # Supported facial parameters
    face_params = {
        "eye_size": params.get("eye_size", 1.0),
        "eye_distance": params.get("eye_distance", 1.0),
        "eye_height": params.get("eye_height", 1.0),
        "eye_tilt": params.get("eye_tilt", 0.0),
        "eye_depth": params.get("eye_depth", 1.0),
        "nose_length": params.get("nose_length", 1.0),
        "nose_width": params.get("nose_width", 1.0),
        "nose_height": params.get("nose_height", 1.0),
        "nose_tip": params.get("nose_tip", 1.0),
        "mouth_width": params.get("mouth_width", 1.0),
        "mouth_height": params.get("mouth_height", 1.0),
        "lip_thickness_upper": params.get("lip_thickness_upper", 1.0),
        "lip_thickness_lower": params.get("lip_thickness_lower", 1.0),
        "jaw_width": params.get("jaw_width", 1.0),
        "jaw_height": params.get("jaw_height", 1.0),
        "chin_length": params.get("chin_length", 1.0),
        "cheekbone_height": params.get("cheekbone_height", 1.0),
        "cheekbone_width": params.get("cheekbone_width", 1.0),
        "forehead_height": params.get("forehead_height", 1.0),
        "forehead_width": params.get("forehead_width", 1.0),
        "ear_size": params.get("ear_size", 1.0),
        "ear_position": params.get("ear_position", 1.0),
    }

    obj = bpy.data.objects.get(character_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    try:
        # Ensure shape keys exist
        if not obj.data.shape_keys:
            _create_face_shape_keys(obj)

        # Apply facial parameters to shape keys
        applied_params = []
        for key_name, value in face_params.items():
            if value != FACE_SHAPE_KEYS.get(key_name, {}).get("default", 1.0):
                sk = obj.data.shape_keys.key_blocks.get(key_name)
                if sk:
                    # Normalize value to 0-1 range
                    config = FACE_SHAPE_KEYS.get(key_name, {"min": 0.5, "max": 1.5})
                    normalized = (value - config["min"]) / (config["max"] - config["min"])
                    sk.value = max(0, min(1, normalized))
                    applied_params.append(key_name)

        # Also store original parameters as custom properties
        for key, value in face_params.items():
            obj[f"face_{key}"] = value

        return {
            "success": True,
            "data": {
                "character_name": character_name,
                "applied_params": applied_params,
                "total_params": len(face_params),
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "FACE_FEATURES_ERROR", "message": str(e)}}


def handle_set_face_expression(params: dict[str, Any]) -> dict[str, Any]:
    """Set facial expression"""
    character_name = params.get("character_name", "")
    expression = params.get("expression", "neutral")
    intensity = params.get("intensity", 1.0)

    # Expression presets
    EXPRESSIONS = {
        "neutral": {},
        "smile": {
            "mouth_width": 1.15,
            "lip_thickness_upper": 0.9,
            "cheekbone_height": 1.1,
            "eye_size": 0.95,
        },
        "sad": {
            "mouth_width": 0.9,
            "eye_tilt": -0.1,
            "lip_thickness_lower": 1.1,
            "cheekbone_height": 0.95,
        },
        "angry": {"eye_tilt": 0.15, "nose_width": 1.1, "jaw_width": 1.05, "forehead_height": 0.95},
        "surprised": {
            "eye_size": 1.3,
            "mouth_height": 1.3,
            "forehead_height": 1.1,
            "eye_height": 1.1,
        },
        "fear": {"eye_size": 1.25, "eye_distance": 1.05, "mouth_height": 1.15, "jaw_height": 1.1},
        "disgust": {
            "nose_tip": 1.15,
            "lip_thickness_upper": 1.15,
            "eye_size": 0.9,
            "cheekbone_height": 1.05,
        },
        "contempt": {
            "mouth_width": 0.95,
            "lip_thickness_upper": 0.9,
            "eye_tilt": 0.05,
            "chin_length": 1.05,
        },
    }

    obj = bpy.data.objects.get(character_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    expr_config = EXPRESSIONS.get(expression)
    if expr_config is None:
        return {
            "success": False,
            "error": {
                "code": "EXPRESSION_NOT_FOUND",
                "message": f"Expression not found: {expression}, available: {list(EXPRESSIONS.keys())}",
            },
        }

    try:
        if not obj.data.shape_keys:
            _create_face_shape_keys(obj)

        # Apply expression
        for key_name, target_value in expr_config.items():
            sk = obj.data.shape_keys.key_blocks.get(key_name)
            if sk:
                # Interpolate by intensity
                default_val = FACE_SHAPE_KEYS.get(key_name, {}).get("default", 1.0)
                final_value = default_val + (target_value - default_val) * intensity
                config = FACE_SHAPE_KEYS.get(key_name, {"min": 0.5, "max": 1.5})
                normalized = (final_value - config["min"]) / (config["max"] - config["min"])
                sk.value = max(0, min(1, normalized))

        return {"success": True, "data": {"expression": expression, "intensity": intensity}}
    except Exception as e:
        return {"success": False, "error": {"code": "EXPRESSION_ERROR", "message": str(e)}}


def handle_add_hair(params: dict[str, Any]) -> dict[str, Any]:
    """Add hair (enhanced - supports multiple hairstyle presets)"""
    character_name = params.get("character_name", "")
    hair_style = params.get("hair_style", "SHORT")
    hair_color = params.get("hair_color", [0.1, 0.08, 0.05])
    use_particles = params.get("use_particles", True)
    hair_density = params.get("hair_density", 1.0)  # Density multiplier
    hair_thickness = params.get("hair_thickness", 1.0)  # Thickness multiplier
    use_dynamics = params.get("use_dynamics", False)  # Enable dynamics

    # Enhanced hairstyle configuration
    HAIR_STYLES = {
        "BALD": {"length": 0.0, "count": 0, "segments": 3, "children": 0, "clump": 0.0},
        "BUZZ": {"length": 0.005, "count": 8000, "segments": 3, "children": 5, "clump": 0.1},
        "SHORT": {"length": 0.05, "count": 5000, "segments": 5, "children": 10, "clump": 0.3},
        "MEDIUM": {"length": 0.15, "count": 4000, "segments": 8, "children": 15, "clump": 0.4},
        "LONG": {"length": 0.35, "count": 3000, "segments": 12, "children": 20, "clump": 0.5},
        "VERY_LONG": {"length": 0.60, "count": 2500, "segments": 16, "children": 25, "clump": 0.6},
        "PONYTAIL": {"length": 0.40, "count": 3500, "segments": 12, "children": 15, "clump": 0.7},
        "BUN": {"length": 0.25, "count": 4000, "segments": 10, "children": 12, "clump": 0.8},
        "BRAIDS": {"length": 0.45, "count": 3000, "segments": 14, "children": 10, "clump": 0.85},
        "MOHAWK": {"length": 0.15, "count": 2000, "segments": 8, "children": 15, "clump": 0.6},
        "AFRO": {"length": 0.20, "count": 8000, "segments": 6, "children": 30, "clump": 0.2},
        "CURLY": {"length": 0.18, "count": 5000, "segments": 10, "children": 20, "clump": 0.4},
        "WAVY": {"length": 0.25, "count": 4000, "segments": 10, "children": 18, "clump": 0.35},
        # Ancient/fantasy hairstyles
        "ANCIENT_MALE": {
            "length": 0.50,
            "count": 3000,
            "segments": 14,
            "children": 20,
            "clump": 0.65,
        },
        "ANCIENT_FEMALE": {
            "length": 0.55,
            "count": 3500,
            "segments": 16,
            "children": 22,
            "clump": 0.6,
        },
        "TOPKNOT": {"length": 0.30, "count": 4000, "segments": 10, "children": 15, "clump": 0.75},
    }

    obj = bpy.data.objects.get(character_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    style_config = HAIR_STYLES.get(hair_style, HAIR_STYLES["SHORT"])

    if style_config["count"] == 0:
        return {"success": True, "data": {"hair_style": "BALD", "message": "No hair needed"}}

    try:
        if use_particles:
            # Select object
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            # Create particle system
            bpy.ops.object.particle_system_add()

            ps = obj.particle_systems[-1]
            ps.name = f"Hair_{hair_style}"

            settings = ps.settings
            settings.type = "HAIR"

            # Apply hairstyle configuration
            settings.hair_length = style_config["length"]
            settings.count = int(style_config["count"] * hair_density)
            settings.hair_step = style_config["segments"]

            # Set root and tip radius
            settings.root_radius = 0.01 * hair_thickness
            settings.tip_radius = 0.002 * hair_thickness

            # Child settings
            if style_config["children"] > 0:
                settings.child_type = "INTERPOLATED"
                settings.rendered_child_count = style_config["children"]
                settings.child_length = 1.0
                settings.clump_factor = style_config["clump"]
                settings.roughness_1 = 0.02
                settings.roughness_2 = 0.02

            # Dynamics settings
            if use_dynamics:
                settings.use_hair_dynamics = True
                cloth = settings.cloth
                cloth.settings.quality = 5
                cloth.settings.mass = 0.3
                cloth.settings.bending_stiffness = 0.5
                cloth.settings.air_damping = 1.0

            # Create hair material (using Principled Hair BSDF)
            hair_mat = bpy.data.materials.new(name=f"{character_name}_Hair_{hair_style}")
            hair_mat.use_nodes = True
            nodes = hair_mat.node_tree.nodes
            links = hair_mat.node_tree.links

            # Clear default nodes
            nodes.clear()

            # Create Principled Hair BSDF
            output = nodes.new("ShaderNodeOutputMaterial")
            output.location = (300, 0)

            try:
                hair_bsdf = nodes.new("ShaderNodeBsdfHairPrincipled")
                hair_bsdf.location = (0, 0)
                hair_bsdf.inputs["Color"].default_value = (
                    hair_color[:3] + [1.0] if len(hair_color) >= 3 else hair_color + [1.0]
                )
                hair_bsdf.inputs["Roughness"].default_value = 0.3
                links.new(hair_bsdf.outputs["BSDF"], output.inputs["Surface"])
            except:
                # Fall back to Principled BSDF
                bsdf = nodes.new("ShaderNodeBsdfPrincipled")
                bsdf.location = (0, 0)
                bsdf.inputs["Base Color"].default_value = (
                    hair_color[:3] + [1.0] if len(hair_color) >= 3 else hair_color + [1.0]
                )
                links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

            # Apply material
            obj.data.materials.append(hair_mat)
            try:
                settings.material_slot = hair_mat.name
            except:
                settings.material = len(obj.material_slots) - 1

        return {
            "success": True,
            "data": {
                "hair_style": hair_style,
                "particle_count": int(style_config["count"] * hair_density),
                "hair_length": style_config["length"],
                "dynamics_enabled": use_dynamics,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "HAIR_ADD_ERROR", "message": str(e)}}


def handle_add_clothing(params: dict[str, Any]) -> dict[str, Any]:
    """Add clothing (enhanced - supports multiple clothing types and cloth simulation)"""
    character_name = params.get("character_name", "")
    clothing_type = params.get("clothing_type", "SHIRT")
    color = params.get("color", [0.5, 0.5, 0.5])
    secondary_color = params.get("secondary_color")  # Optional secondary color
    use_cloth_simulation = params.get("use_cloth_simulation", False)
    metallic = params.get("metallic", 0.0)
    roughness = params.get("roughness", 0.8)
    pattern = params.get("pattern")  # Optional: SOLID, STRIPES, PLAID, FLORAL

    obj = bpy.data.objects.get(character_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    template = CLOTHING_TEMPLATES.get(clothing_type)
    if not template:
        available = list(CLOTHING_TEMPLATES.keys())
        return {
            "success": False,
            "error": {
                "code": "CLOTHING_TYPE_NOT_FOUND",
                "message": f"Clothing type not found: {clothing_type}, available: {available}",
            },
        }

    try:
        # Create clothing mesh
        clothing = _create_clothing_mesh(obj, clothing_type, template)

        if clothing is None:
            return {
                "success": False,
                "error": {
                    "code": "CLOTHING_CREATE_ERROR",
                    "message": "Failed to create clothing mesh",
                },
            }

        # Create clothing material
        cloth_mat = _create_clothing_material(
            f"{character_name}_{clothing_type}",
            color,
            secondary_color,
            metallic,
            roughness,
            pattern,
        )

        # Apply material
        if clothing.data.materials:
            clothing.data.materials[0] = cloth_mat
        else:
            clothing.data.materials.append(cloth_mat)

        # Add cloth simulation
        if use_cloth_simulation:
            _add_cloth_simulation(clothing, template["cloth_preset"])

        # Set as child of character
        clothing.parent = obj

        return {
            "success": True,
            "data": {
                "clothing_name": clothing.name,
                "clothing_type": clothing_type,
                "description": template["description"],
                "cloth_simulation": use_cloth_simulation,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "CLOTHING_ERROR", "message": str(e)}}


def _create_clothing_mesh(
    character: bpy.types.Object, clothing_type: str, template: dict
) -> bpy.types.Object:
    """Create clothing mesh"""
    # Copy character mesh as base
    clothing = character.copy()
    clothing.data = character.data.copy()
    clothing.name = f"{character.name}_{clothing_type}"

    # Clear shape keys (if any)
    if clothing.data.shape_keys:
        clothing.shape_key_clear()

    # Apply scaling
    scale = template["scale"]
    offset = template["offset"]

    clothing.scale = (scale[0], scale[1], scale[2])
    clothing.location = (
        character.location[0] + offset[0],
        character.location[1] + offset[1],
        character.location[2] + offset[2],
    )

    # Link to scene
    bpy.context.collection.objects.link(clothing)

    # Apply transforms
    bpy.ops.object.select_all(action="DESELECT")
    clothing.select_set(True)
    bpy.context.view_layer.objects.active = clothing
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Add appropriate subdivision
    subsurf = clothing.modifiers.new(name="Subdivision", type="SUBSURF")
    subsurf.levels = 1
    subsurf.render_levels = 2

    # Add smooth
    smooth = clothing.modifiers.new(name="Smooth", type="SMOOTH")
    smooth.factor = 0.3
    smooth.iterations = 2

    return clothing


def _create_clothing_material(
    name: str,
    color: list[float],
    secondary_color: list[float] = None,
    metallic: float = 0.0,
    roughness: float = 0.8,
    pattern: str = None,
) -> bpy.types.Material:
    """Create clothing material"""
    mat = bpy.data.materials.new(name=f"{name}_Material")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes

    # Get default nodes
    principled = get_principled_bsdf(nodes)
    nodes.get("Material Output")

    if principled:
        # Set base color
        color_rgba = color[:3] + [1.0] if len(color) >= 3 else color + [1.0]
        principled.inputs["Base Color"].default_value = color_rgba
        principled.inputs["Metallic"].default_value = metallic
        principled.inputs["Roughness"].default_value = roughness

        # If secondary color and pattern, create blend
        if secondary_color and pattern and pattern != "SOLID":
            _add_pattern_to_material(mat, color, secondary_color, pattern)

    return mat


def _add_pattern_to_material(
    mat: bpy.types.Material, primary_color: list[float], secondary_color: list[float], pattern: str
) -> None:
    """Add pattern to material"""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    principled = get_principled_bsdf(nodes)

    # Create texture coordinates
    tex_coord = nodes.new("ShaderNodeTexCoord")
    tex_coord.location = (-800, 0)

    # Create mapping node
    mapping = nodes.new("ShaderNodeMapping")
    mapping.location = (-600, 0)
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])

    if pattern == "STRIPES":
        # Stripe pattern
        wave = nodes.new("ShaderNodeTexWave")
        wave.location = (-400, 0)
        wave.wave_type = "BANDS"
        wave.bands_direction = "X"
        wave.inputs["Scale"].default_value = 10.0
        links.new(mapping.outputs["Vector"], wave.inputs["Vector"])

        # Color blend
        mix = nodes.new("ShaderNodeMixRGB")
        mix.location = (-200, 0)
        mix.inputs["Color1"].default_value = (
            primary_color[:3] + [1.0] if len(primary_color) >= 3 else primary_color + [1.0]
        )
        mix.inputs["Color2"].default_value = (
            secondary_color[:3] + [1.0] if len(secondary_color) >= 3 else secondary_color + [1.0]
        )
        links.new(wave.outputs["Fac"], mix.inputs["Fac"])
        links.new(mix.outputs["Color"], principled.inputs["Base Color"])

    elif pattern == "PLAID":
        # Plaid pattern
        checker = nodes.new("ShaderNodeTexChecker")
        checker.location = (-400, 0)
        checker.inputs["Scale"].default_value = 8.0
        links.new(mapping.outputs["Vector"], checker.inputs["Vector"])

        mix = nodes.new("ShaderNodeMixRGB")
        mix.location = (-200, 0)
        mix.inputs["Color1"].default_value = (
            primary_color[:3] + [1.0] if len(primary_color) >= 3 else primary_color + [1.0]
        )
        mix.inputs["Color2"].default_value = (
            secondary_color[:3] + [1.0] if len(secondary_color) >= 3 else secondary_color + [1.0]
        )
        links.new(checker.outputs["Fac"], mix.inputs["Fac"])
        links.new(mix.outputs["Color"], principled.inputs["Base Color"])


def _add_cloth_simulation(clothing: bpy.types.Object, preset: str) -> None:
    """Add cloth simulation to clothing"""
    # Add cloth modifier
    cloth_mod = clothing.modifiers.new(name="Cloth", type="CLOTH")
    cloth = cloth_mod.settings

    # Apply preset
    preset_config = CLOTH_PRESETS.get(preset, CLOTH_PRESETS["cotton"])
    cloth.mass = preset_config["mass"]
    cloth.air_damping = preset_config["air_damping"]
    cloth.tension_stiffness = preset_config["tension_stiffness"]
    cloth.compression_stiffness = preset_config["compression_stiffness"]
    cloth.shear_stiffness = preset_config["shear_stiffness"]
    cloth.bending_stiffness = preset_config["bending_stiffness"]

    # Set collision
    cloth.collision_settings.collision_quality = 3
    cloth.collision_settings.distance_min = 0.001

    # Create pin vertex group
    if "Pin" not in clothing.vertex_groups:
        pin_group = clothing.vertex_groups.new(name="Pin")
        # Select top vertices as pin points
        clothing_height = max(v.co.z for v in clothing.data.vertices)
        for v in clothing.data.vertices:
            if v.co.z > clothing_height * 0.9:
                pin_group.add([v.index], 1.0, "REPLACE")

        cloth.vertex_group_mass = "Pin"


def handle_create_outfit(params: dict[str, Any]) -> dict[str, Any]:
    """Create complete outfit"""
    character_name = params.get("character_name", "")
    outfit_style = params.get("outfit_style", "CASUAL")
    color_scheme = params.get("color_scheme", "DEFAULT")
    use_cloth_simulation = params.get("use_cloth_simulation", False)

    # Outfit configuration
    OUTFIT_STYLES = {
        "CASUAL": ["T_SHIRT", "PANTS", "SHOES"],
        "FORMAL": ["SHIRT", "PANTS", "SHOES"],
        "WARRIOR": ["ARMOR_CHEST", "PANTS", "BOOTS", "GLOVES"],
        "MAGE": ["ROBE", "BOOTS", "GLOVES", "HAT"],
        "HANFU": ["HANFU_TOP", "HANFU_BOTTOM", "SHOES"],
        "ANCIENT_WARRIOR": ["ARMOR_FULL", "BOOTS", "HELMET"],
        "NOBLE": ["JACKET", "PANTS", "BOOTS", "CAPE"],
        "DANCER": ["DRESS", "SHOES"],
    }

    # Color schemes
    COLOR_SCHEMES = {
        "DEFAULT": {"primary": [0.5, 0.5, 0.5], "secondary": [0.3, 0.3, 0.3]},
        "RED": {"primary": [0.8, 0.2, 0.2], "secondary": [0.5, 0.1, 0.1]},
        "BLUE": {"primary": [0.2, 0.3, 0.8], "secondary": [0.1, 0.2, 0.5]},
        "GREEN": {"primary": [0.2, 0.6, 0.3], "secondary": [0.1, 0.4, 0.2]},
        "WHITE": {"primary": [0.9, 0.9, 0.9], "secondary": [0.7, 0.7, 0.7]},
        "BLACK": {"primary": [0.1, 0.1, 0.1], "secondary": [0.2, 0.2, 0.2]},
        "GOLD": {"primary": [0.8, 0.6, 0.2], "secondary": [0.6, 0.4, 0.1]},
        "PURPLE": {"primary": [0.5, 0.2, 0.6], "secondary": [0.3, 0.1, 0.4]},
    }

    obj = bpy.data.objects.get(character_name)
    if not obj:
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Character not found: {character_name}",
            },
        }

    outfit_items = OUTFIT_STYLES.get(outfit_style, OUTFIT_STYLES["CASUAL"])
    colors = COLOR_SCHEMES.get(color_scheme, COLOR_SCHEMES["DEFAULT"])

    created_items = []

    try:
        for i, item_type in enumerate(outfit_items):
            # Alternate between primary and secondary colors
            item_color = colors["primary"] if i % 2 == 0 else colors["secondary"]

            result = handle_add_clothing(
                {
                    "character_name": character_name,
                    "clothing_type": item_type,
                    "color": item_color,
                    "use_cloth_simulation": use_cloth_simulation,
                }
            )

            if result.get("success"):
                created_items.append(result["data"]["clothing_name"])

        return {
            "success": True,
            "data": {
                "outfit_style": outfit_style,
                "color_scheme": color_scheme,
                "items_created": created_items,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "OUTFIT_CREATE_ERROR", "message": str(e)}}
