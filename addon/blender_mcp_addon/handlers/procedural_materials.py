"""
Procedural Materials Handler

Generates 50+ procedural material presets through the Blender node system.
"""

from typing import Any

import bpy

# ==================== Utility Functions ====================


def _get_or_create_material(name: str) -> bpy.types.Material:
    """Get or create material"""
    mat = bpy.data.materials.get(name)
    if mat:
        # Clear old nodes
        mat.node_tree.nodes.clear()
    else:
        mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    if not mat.node_tree.nodes:
        mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")
    return mat


def _get_output(mat: bpy.types.Material):
    """Get Material Output node"""
    for node in mat.node_tree.nodes:
        if node.type == "OUTPUT_MATERIAL":
            return node
    return mat.node_tree.nodes.new(type="ShaderNodeOutputMaterial")


def _add_principled(mat, location=(-300, 0)):
    """Add Principled BSDF node"""
    node = mat.node_tree.nodes.new(type="ShaderNodeBsdfPrincipled")
    node.location = location
    return node


def _add_noise(mat, scale=5.0, detail=2.0, location=(-800, 0)):
    """Add noise texture"""
    node = mat.node_tree.nodes.new(type="ShaderNodeTexNoise")
    node.inputs["Scale"].default_value = scale
    node.inputs["Detail"].default_value = detail
    node.location = location
    return node


def _add_voronoi(mat, scale=5.0, location=(-800, 0)):
    """Add Voronoi texture"""
    node = mat.node_tree.nodes.new(type="ShaderNodeTexVoronoi")
    node.inputs["Scale"].default_value = scale
    node.location = location
    return node


def _add_musgrave(mat, scale=5.0, detail=2.0, location=(-800, 0)):
    """Add Musgrave texture (merged into Noise in Blender 4.0+)"""
    try:
        node = mat.node_tree.nodes.new(type="ShaderNodeTexMusgrave")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
    except Exception:
        # Blender 4.0+ Musgrave merged into Noise
        node = mat.node_tree.nodes.new(type="ShaderNodeTexNoise")
        node.inputs["Scale"].default_value = scale
        node.inputs["Detail"].default_value = detail
    node.location = location
    return node


def _add_colorramp(mat, colors=None, positions=None, location=(-500, 0)):
    """Add ColorRamp node"""
    node = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
    node.location = location
    if colors and positions:
        ramp = node.color_ramp
        for i, (col, pos) in enumerate(zip(colors, positions, strict=False)):
            if i == 0:
                ramp.elements[0].position = pos
                ramp.elements[0].color = col if len(col) == 4 else (*col, 1.0)
            elif i == 1:
                ramp.elements[1].position = pos
                ramp.elements[1].color = col if len(col) == 4 else (*col, 1.0)
            else:
                elem = ramp.elements.new(pos)
                elem.color = col if len(col) == 4 else (*col, 1.0)
    return node


def _add_bump(mat, strength=0.5, location=(-300, -300)):
    """Add Bump node"""
    node = mat.node_tree.nodes.new(type="ShaderNodeBump")
    node.inputs["Strength"].default_value = strength
    node.location = location
    return node


def _add_mapping(mat, scale=(1, 1, 1), location=(-1200, 0)):
    """Add Mapping + Texture Coordinate"""
    tc = mat.node_tree.nodes.new(type="ShaderNodeTexCoord")
    tc.location = (location[0] - 200, location[1])
    mapping = mat.node_tree.nodes.new(type="ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = scale
    mapping.location = location
    mat.node_tree.links.new(tc.outputs["Object"], mapping.inputs["Vector"])
    return mapping, tc


def _link(mat, from_node, from_socket, to_node, to_socket) -> None:
    """Connect nodes"""
    # Support string or index
    if isinstance(from_socket, str):
        out = from_node.outputs[from_socket]
    else:
        out = from_node.outputs[from_socket]
    inp = to_node.inputs[to_socket] if isinstance(to_socket, str) else to_node.inputs[to_socket]
    mat.node_tree.links.new(out, inp)


def _apply_to_object(mat, object_name) -> None:
    """Apply material to object"""
    obj = bpy.data.objects.get(object_name)
    if obj:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat


# ==================== Material Preset Data ====================

METAL_PRESETS = {
    "STEEL": {
        "base_color": (0.55, 0.56, 0.58),
        "metallic": 1.0,
        "roughness": 0.3,
        "noise_scale": 50,
        "bump_strength": 0.1,
    },
    "IRON": {
        "base_color": (0.42, 0.40, 0.38),
        "metallic": 1.0,
        "roughness": 0.5,
        "noise_scale": 30,
        "bump_strength": 0.15,
    },
    "GOLD": {
        "base_color": (1.0, 0.76, 0.33),
        "metallic": 1.0,
        "roughness": 0.15,
        "noise_scale": 80,
        "bump_strength": 0.05,
    },
    "SILVER": {
        "base_color": (0.8, 0.8, 0.82),
        "metallic": 1.0,
        "roughness": 0.1,
        "noise_scale": 80,
        "bump_strength": 0.05,
    },
    "BRONZE": {
        "base_color": (0.72, 0.45, 0.2),
        "metallic": 1.0,
        "roughness": 0.35,
        "noise_scale": 40,
        "bump_strength": 0.12,
    },
    "COPPER": {
        "base_color": (0.85, 0.45, 0.25),
        "metallic": 1.0,
        "roughness": 0.25,
        "noise_scale": 60,
        "bump_strength": 0.08,
    },
    "CHROME": {
        "base_color": (0.88, 0.88, 0.90),
        "metallic": 1.0,
        "roughness": 0.02,
        "noise_scale": 100,
        "bump_strength": 0.02,
    },
    "BRUSHED_METAL": {
        "base_color": (0.6, 0.6, 0.62),
        "metallic": 1.0,
        "roughness": 0.4,
        "noise_scale": 200,
        "bump_strength": 0.08,
        "anisotropic": True,
    },
    "RUSTY_METAL": {
        "base_color": (0.45, 0.25, 0.12),
        "metallic": 0.6,
        "roughness": 0.7,
        "noise_scale": 15,
        "bump_strength": 0.3,
    },
    "DAMASCUS": {
        "base_color": (0.5, 0.48, 0.45),
        "metallic": 1.0,
        "roughness": 0.25,
        "noise_scale": 8,
        "bump_strength": 0.1,
        "pattern": True,
    },
}

WOOD_PRESETS = {
    "OAK": {"base_color": (0.47, 0.30, 0.15), "roughness": 0.6, "grain_scale": 3, "ring_scale": 20},
    "PINE": {
        "base_color": (0.65, 0.45, 0.22),
        "roughness": 0.55,
        "grain_scale": 4,
        "ring_scale": 25,
    },
    "CHERRY": {
        "base_color": (0.55, 0.20, 0.10),
        "roughness": 0.4,
        "grain_scale": 3,
        "ring_scale": 18,
    },
    "WALNUT": {
        "base_color": (0.35, 0.20, 0.10),
        "roughness": 0.5,
        "grain_scale": 3,
        "ring_scale": 15,
    },
    "BIRCH": {
        "base_color": (0.75, 0.65, 0.45),
        "roughness": 0.45,
        "grain_scale": 5,
        "ring_scale": 30,
    },
    "BAMBOO": {
        "base_color": (0.70, 0.60, 0.30),
        "roughness": 0.35,
        "grain_scale": 8,
        "ring_scale": 40,
    },
    "PLYWOOD": {
        "base_color": (0.65, 0.50, 0.30),
        "roughness": 0.6,
        "grain_scale": 2,
        "ring_scale": 10,
    },
    "AGED_WOOD": {
        "base_color": (0.3, 0.22, 0.13),
        "roughness": 0.8,
        "grain_scale": 2,
        "ring_scale": 12,
    },
}

STONE_PRESETS = {
    "GRANITE": {
        "base_color": (0.5, 0.48, 0.45),
        "roughness": 0.6,
        "voronoi_scale": 20,
        "bump_strength": 0.15,
    },
    "MARBLE": {
        "base_color": (0.92, 0.90, 0.88),
        "roughness": 0.15,
        "voronoi_scale": 5,
        "bump_strength": 0.05,
        "vein_color": (0.3, 0.3, 0.32),
    },
    "LIMESTONE": {
        "base_color": (0.78, 0.72, 0.62),
        "roughness": 0.7,
        "voronoi_scale": 15,
        "bump_strength": 0.2,
    },
    "SLATE": {
        "base_color": (0.35, 0.35, 0.38),
        "roughness": 0.5,
        "voronoi_scale": 10,
        "bump_strength": 0.25,
    },
    "COBBLESTONE": {
        "base_color": (0.45, 0.42, 0.38),
        "roughness": 0.7,
        "voronoi_scale": 4,
        "bump_strength": 0.4,
    },
    "SANDSTONE": {
        "base_color": (0.75, 0.62, 0.42),
        "roughness": 0.8,
        "voronoi_scale": 25,
        "bump_strength": 0.15,
    },
    "BRICK": {
        "base_color": (0.6, 0.25, 0.15),
        "roughness": 0.75,
        "voronoi_scale": 3,
        "bump_strength": 0.3,
    },
    "TILE": {
        "base_color": (0.85, 0.82, 0.78),
        "roughness": 0.2,
        "voronoi_scale": 5,
        "bump_strength": 0.1,
    },
    "CONCRETE": {
        "base_color": (0.55, 0.53, 0.50),
        "roughness": 0.85,
        "voronoi_scale": 30,
        "bump_strength": 0.1,
    },
}

FABRIC_PRESETS = {
    "COTTON": {
        "base_color": (0.85, 0.82, 0.78),
        "roughness": 0.9,
        "sheen": 0.3,
        "noise_scale": 100,
    },
    "SILK": {"base_color": (0.8, 0.3, 0.3), "roughness": 0.2, "sheen": 0.8, "noise_scale": 200},
    "LEATHER": {"base_color": (0.35, 0.2, 0.1), "roughness": 0.6, "sheen": 0.1, "noise_scale": 50},
    "DENIM": {"base_color": (0.15, 0.25, 0.5), "roughness": 0.8, "sheen": 0.2, "noise_scale": 80},
    "VELVET": {"base_color": (0.3, 0.05, 0.1), "roughness": 0.95, "sheen": 1.0, "noise_scale": 150},
    "CANVAS": {
        "base_color": (0.7, 0.65, 0.55),
        "roughness": 0.85,
        "sheen": 0.15,
        "noise_scale": 60,
    },
    "WOOL": {"base_color": (0.8, 0.75, 0.65), "roughness": 0.95, "sheen": 0.4, "noise_scale": 40},
    "CHAIN_MAIL": {
        "base_color": (0.6, 0.58, 0.55),
        "roughness": 0.35,
        "metallic": 1.0,
        "noise_scale": 30,
    },
}

NATURE_PRESETS = {
    "GRASS": {"base_color": (0.15, 0.4, 0.08), "roughness": 0.8, "noise_scale": 20, "sss": 0.1},
    "DIRT": {
        "base_color": (0.35, 0.25, 0.15),
        "roughness": 0.9,
        "noise_scale": 15,
        "bump_strength": 0.3,
    },
    "SAND": {
        "base_color": (0.78, 0.7, 0.5),
        "roughness": 0.95,
        "noise_scale": 50,
        "bump_strength": 0.1,
    },
    "SNOW": {"base_color": (0.95, 0.95, 0.97), "roughness": 0.6, "noise_scale": 30, "sss": 0.3},
    "MUD": {
        "base_color": (0.25, 0.18, 0.10),
        "roughness": 0.7,
        "noise_scale": 10,
        "bump_strength": 0.4,
    },
    "GRAVEL": {
        "base_color": (0.45, 0.42, 0.38),
        "roughness": 0.85,
        "noise_scale": 8,
        "bump_strength": 0.5,
    },
    "MOSS": {
        "base_color": (0.12, 0.3, 0.08),
        "roughness": 0.9,
        "noise_scale": 25,
        "sss": 0.15,
        "bump_strength": 0.2,
    },
    "LAVA": {
        "base_color": (0.02, 0.02, 0.02),
        "roughness": 0.9,
        "emission_color": (1.0, 0.3, 0.02),
        "emission_strength": 8.0,
        "noise_scale": 5,
    },
    "WATER": {
        "base_color": (0.01, 0.05, 0.1),
        "roughness": 0.0,
        "transmission": 0.95,
        "ior": 1.33,
        "noise_scale": 10,
    },
    "ICE": {
        "base_color": (0.7, 0.85, 0.95),
        "roughness": 0.05,
        "transmission": 0.8,
        "ior": 1.31,
        "sss": 0.2,
    },
}

SKIN_PRESETS = {
    "SKIN_REALISTIC": {
        "base_color": (0.8, 0.58, 0.45),
        "roughness": 0.5,
        "sss": 0.5,
        "sss_color": (0.9, 0.3, 0.15),
    },
    "SKIN_STYLIZED": {"base_color": (0.9, 0.7, 0.55), "roughness": 0.6, "sss": 0.2},
    "SCALES": {
        "base_color": (0.2, 0.35, 0.15),
        "roughness": 0.3,
        "metallic": 0.1,
        "voronoi_scale": 15,
        "bump_strength": 0.3,
    },
    "CARTOON_SKIN": {"base_color": (0.95, 0.78, 0.65), "roughness": 0.7, "sss": 0.1},
}

EFFECT_PRESETS = {
    "GLASS": {"base_color": (0.95, 0.95, 0.95), "roughness": 0.0, "transmission": 1.0, "ior": 1.5},
    "CRYSTAL": {"base_color": (0.6, 0.8, 1.0), "roughness": 0.0, "transmission": 0.9, "ior": 2.0},
    "HOLOGRAM": {
        "base_color": (0.0, 0.5, 1.0),
        "roughness": 0.0,
        "emission_color": (0.0, 0.5, 1.0),
        "emission_strength": 3.0,
        "alpha": 0.3,
    },
    "ENERGY": {
        "base_color": (0.0, 0.0, 0.0),
        "roughness": 0.0,
        "emission_color": (0.2, 0.5, 1.0),
        "emission_strength": 10.0,
    },
    "PORTAL": {
        "base_color": (0.0, 0.0, 0.0),
        "roughness": 0.0,
        "emission_color": (0.5, 0.0, 1.0),
        "emission_strength": 15.0,
    },
    "EMISSION_GLOW": {
        "base_color": (1.0, 1.0, 1.0),
        "roughness": 0.0,
        "emission_color": (1.0, 0.8, 0.3),
        "emission_strength": 5.0,
    },
    "FORCE_FIELD": {
        "base_color": (0.0, 0.0, 0.0),
        "roughness": 0.0,
        "emission_color": (0.0, 1.0, 0.5),
        "emission_strength": 5.0,
        "alpha": 0.15,
    },
}

TOON_PRESETS = {
    "TOON_BASIC": {"base_color": (0.8, 0.3, 0.3), "shadow_color": (0.4, 0.15, 0.15), "steps": 2},
    "TOON_METAL": {
        "base_color": (0.7, 0.7, 0.75),
        "shadow_color": (0.3, 0.3, 0.35),
        "highlight_color": (1.0, 1.0, 1.0),
        "steps": 3,
    },
    "TOON_SKIN": {"base_color": (0.95, 0.75, 0.6), "shadow_color": (0.7, 0.45, 0.35), "steps": 2},
    "TOON_FABRIC": {"base_color": (0.3, 0.5, 0.8), "shadow_color": (0.15, 0.25, 0.45), "steps": 2},
    "ANIME_HAIR": {
        "base_color": (0.15, 0.15, 0.5),
        "shadow_color": (0.08, 0.08, 0.3),
        "highlight_color": (0.4, 0.4, 0.9),
        "steps": 3,
        "specular_band": True,
    },
    "GENSHIN_STYLE": {
        "base_color": (0.85, 0.6, 0.5),
        "shadow_color": (0.55, 0.35, 0.3),
        "rim_color": (1.0, 0.9, 0.8),
        "steps": 2,
        "rim": True,
    },
    "CEL_SHADE": {"base_color": (0.9, 0.9, 0.85), "shadow_color": (0.5, 0.5, 0.55), "steps": 2},
}


# ==================== Material Generator Functions ====================


def _create_metal(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create metal material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Base Color"].default_value = (*bc, 1.0)
    bsdf.inputs["Metallic"].default_value = preset_data.get("metallic", 1.0)
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # Add noise texture for micro-surface variation
    ns = preset_data.get("noise_scale", 50) * scale
    noise = _add_noise(mat, scale=ns, detail=4.0)
    bump = _add_bump(mat, strength=preset_data.get("bump_strength", 0.1))
    _link(mat, noise, "Fac", bump, "Height")
    _link(mat, bump, "Normal", bsdf, "Normal")

    # Roughness variation
    ramp = _add_colorramp(
        mat, colors=[(0.3, 0.3, 0.3), (0.6, 0.6, 0.6)], positions=[0.4, 0.6], location=(-500, 200)
    )
    noise2 = _add_noise(mat, scale=ns * 0.5, detail=2.0, location=(-800, 200))
    _link(mat, noise2, "Fac", ramp, "Fac")
    # Mix roughness variation
    math_node = mat.node_tree.nodes.new(type="ShaderNodeMath")
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = 0.3
    math_node.location = (-300, 200)
    _link(mat, ramp, "Color", math_node, 0)

    rough_mix = mat.node_tree.nodes.new(type="ShaderNodeMath")
    rough_mix.operation = "ADD"
    base_rough = roughness_override if roughness_override is not None else preset_data["roughness"]
    rough_mix.inputs[1].default_value = base_rough
    rough_mix.location = (-150, 200)
    _link(mat, math_node, "Value", rough_mix, 0)
    _link(mat, rough_mix, "Value", bsdf, "Roughness")


def _create_wood(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create wood material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    dark_color = tuple(c * 0.6 for c in bc)

    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # Wood grain: Wave Texture + Noise mix
    mapping, tc = _add_mapping(mat, scale=(scale, scale, scale))

    wave = mat.node_tree.nodes.new(type="ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = preset_data.get("ring_scale", 20)
    wave.inputs["Distortion"].default_value = 8.0
    wave.inputs["Detail"].default_value = 3.0
    wave.inputs["Detail Scale"].default_value = preset_data.get("grain_scale", 3)
    wave.wave_type = "RINGS"
    wave.location = (-800, 0)
    _link(mat, mapping, "Vector", wave, "Vector")

    ramp = _add_colorramp(mat, colors=[dark_color, bc], positions=[0.3, 0.7], location=(-500, 0))
    _link(mat, wave, "Fac", ramp, "Fac")
    _link(mat, ramp, "Color", bsdf, "Base Color")

    # Bump
    bump = _add_bump(mat, strength=0.1)
    _link(mat, wave, "Fac", bump, "Height")
    _link(mat, bump, "Normal", bsdf, "Normal")


def _create_stone(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create stone material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    vs = preset_data.get("voronoi_scale", 15) * scale
    voronoi = _add_voronoi(mat, scale=vs)
    noise = _add_noise(mat, scale=vs * 2, detail=4.0, location=(-800, 200))

    # Color variation
    dark_color = tuple(c * 0.7 for c in bc)
    ramp = _add_colorramp(mat, colors=[dark_color, bc], positions=[0.3, 0.7], location=(-500, 0))

    mix = mat.node_tree.nodes.new(type="ShaderNodeMath")
    mix.operation = "ADD"
    mix.location = (-650, 100)
    _link(mat, voronoi, "Distance", mix, 0)
    _link(mat, noise, "Fac", mix, 1)
    _link(mat, mix, "Value", ramp, "Fac")
    _link(mat, ramp, "Color", bsdf, "Base Color")

    # Bump
    bs = preset_data.get("bump_strength", 0.15)
    bump = _add_bump(mat, strength=bs)
    _link(mat, voronoi, "Distance", bump, "Height")
    _link(mat, bump, "Normal", bsdf, "Normal")


def _create_fabric(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create fabric material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Base Color"].default_value = (*bc, 1.0)
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # Sheen
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = preset_data.get("sheen", 0.3)
    elif "Sheen" in bsdf.inputs:
        bsdf.inputs["Sheen"].default_value = preset_data.get("sheen", 0.3)

    if preset_data.get("metallic"):
        bsdf.inputs["Metallic"].default_value = preset_data["metallic"]

    # Micro-surface texture
    ns = preset_data.get("noise_scale", 80) * scale
    noise = _add_noise(mat, scale=ns, detail=6.0)
    bump = _add_bump(mat, strength=0.05)
    _link(mat, noise, "Fac", bump, "Height")
    _link(mat, bump, "Normal", bsdf, "Normal")


def _create_nature(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create nature material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # SSS
    sss_val = preset_data.get("sss", 0)
    if sss_val > 0:
        if "Subsurface Weight" in bsdf.inputs:
            bsdf.inputs["Subsurface Weight"].default_value = sss_val
        elif "Subsurface" in bsdf.inputs:
            bsdf.inputs["Subsurface"].default_value = sss_val

    # Transmission
    if preset_data.get("transmission"):
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = preset_data["transmission"]
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = preset_data["transmission"]
        if preset_data.get("ior"):
            bsdf.inputs["IOR"].default_value = preset_data["ior"]

    # Emission
    if preset_data.get("emission_color"):
        ec = preset_data["emission_color"]
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*ec, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = preset_data.get(
                "emission_strength", 1.0
            )

    # Color + noise variation
    ns = preset_data.get("noise_scale", 20) * scale
    noise = _add_noise(mat, scale=ns, detail=4.0)
    dark_color = tuple(max(0, c * 0.7) for c in bc)
    ramp = _add_colorramp(mat, colors=[dark_color, bc], positions=[0.35, 0.65], location=(-500, 0))
    _link(mat, noise, "Fac", ramp, "Fac")
    _link(mat, ramp, "Color", bsdf, "Base Color")

    # Bump
    bs = preset_data.get("bump_strength", 0.1)
    if bs > 0:
        bump = _add_bump(mat, strength=bs)
        _link(mat, noise, "Fac", bump, "Height")
        _link(mat, bump, "Normal", bsdf, "Normal")


def _create_skin(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create skin material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Base Color"].default_value = (*bc, 1.0)
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # SSS
    sss_val = preset_data.get("sss", 0.3)
    if "Subsurface Weight" in bsdf.inputs:
        bsdf.inputs["Subsurface Weight"].default_value = sss_val
    elif "Subsurface" in bsdf.inputs:
        bsdf.inputs["Subsurface"].default_value = sss_val

    if preset_data.get("sss_color"):
        sc = preset_data["sss_color"]
        if "Subsurface Color" in bsdf.inputs:
            bsdf.inputs["Subsurface Color"].default_value = (*sc, 1.0)
        elif "Subsurface Radius" in bsdf.inputs:
            bsdf.inputs["Subsurface Radius"].default_value = sc

    # Voronoi for pores (if scales type)
    if preset_data.get("voronoi_scale"):
        vs = preset_data["voronoi_scale"] * scale
        voronoi = _add_voronoi(mat, scale=vs)
        bump = _add_bump(mat, strength=preset_data.get("bump_strength", 0.2))
        _link(mat, voronoi, "Distance", bump, "Height")
        _link(mat, bump, "Normal", bsdf, "Normal")
    else:
        # Skin micro-surface noise
        noise = _add_noise(mat, scale=80 * scale, detail=8.0)
        bump = _add_bump(mat, strength=0.03)
        _link(mat, noise, "Fac", bump, "Height")
        _link(mat, bump, "Normal", bsdf, "Normal")


def _create_effect(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create effect material"""
    output = _get_output(mat)
    bsdf = _add_principled(mat)
    _link(mat, bsdf, "BSDF", output, "Surface")

    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Base Color"].default_value = (*bc, 1.0)
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else preset_data["roughness"]
    )

    # Transmission
    if preset_data.get("transmission"):
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = preset_data["transmission"]
        elif "Transmission" in bsdf.inputs:
            bsdf.inputs["Transmission"].default_value = preset_data["transmission"]
        if preset_data.get("ior"):
            bsdf.inputs["IOR"].default_value = preset_data["ior"]

    # Emission
    if preset_data.get("emission_color"):
        ec = preset_data["emission_color"]
        if "Emission Color" in bsdf.inputs:
            bsdf.inputs["Emission Color"].default_value = (*ec, 1.0)
        elif "Emission" in bsdf.inputs:
            bsdf.inputs["Emission"].default_value = (*ec, 1.0)
        if "Emission Strength" in bsdf.inputs:
            bsdf.inputs["Emission Strength"].default_value = preset_data.get(
                "emission_strength", 1.0
            )

    # Alpha
    if preset_data.get("alpha") is not None:
        bsdf.inputs["Alpha"].default_value = preset_data["alpha"]
        mat.blend_method = "BLEND" if hasattr(mat, "blend_method") else "OPAQUE"

    # Dynamic noise effect
    if preset_data.get("emission_color"):
        noise = _add_noise(mat, scale=10 * scale, detail=6.0)
        ramp = _add_colorramp(
            mat,
            colors=[(0, 0, 0), preset_data["emission_color"]],
            positions=[0.3, 0.7],
            location=(-500, -200),
        )
        _link(mat, noise, "Fac", ramp, "Fac")


def _create_toon(mat, preset_data, scale, color_override, roughness_override) -> None:
    """Create cartoon/toon material"""
    output = _get_output(mat)

    # Toon material uses Shader to RGB + ColorRamp
    bsdf = _add_principled(mat)
    bc = color_override or preset_data["base_color"]
    bsdf.inputs["Base Color"].default_value = (*bc, 1.0)
    bsdf.inputs["Roughness"].default_value = (
        roughness_override if roughness_override is not None else 0.5
    )
    bsdf.inputs["Specular IOR Level"].default_value = (
        0.0 if "Specular IOR Level" in bsdf.inputs else 0.0
    )
    if "Specular" in bsdf.inputs:
        bsdf.inputs["Specular"].default_value = 0.0

    # Shader to RGB
    shader_to_rgb = mat.node_tree.nodes.new(type="ShaderNodeShaderToRGB")
    shader_to_rgb.location = (-100, 0)
    _link(mat, bsdf, "BSDF", shader_to_rgb, "Shader")

    # ColorRamp for cel shading steps
    steps = preset_data.get("steps", 2)
    shadow_color = preset_data.get("shadow_color", tuple(c * 0.5 for c in bc))
    preset_data.get("highlight_color", bc)

    ramp = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
    ramp.location = (100, 0)
    ramp.color_ramp.interpolation = "CONSTANT"

    # Set color stops
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*shadow_color, 1.0)
    ramp.color_ramp.elements[1].position = 0.5
    ramp.color_ramp.elements[1].color = (*bc, 1.0)

    if steps >= 3 and preset_data.get("highlight_color"):
        hc = preset_data["highlight_color"]
        elem = ramp.color_ramp.elements.new(0.85)
        elem.color = (*hc, 1.0)

    _link(mat, shader_to_rgb, "Color", ramp, "Fac")

    # Connect to Output
    _link(mat, ramp, "Color", output, "Surface")

    # Rim light
    if preset_data.get("rim"):
        fresnel = mat.node_tree.nodes.new(type="ShaderNodeFresnel")
        fresnel.inputs["IOR"].default_value = 1.1
        fresnel.location = (100, -200)

        rim_ramp = mat.node_tree.nodes.new(type="ShaderNodeValToRGB")
        rim_ramp.location = (300, -200)
        rim_ramp.color_ramp.elements[0].position = 0.6
        rim_ramp.color_ramp.elements[0].color = (0, 0, 0, 1)
        rim_color = preset_data.get("rim_color", (1, 1, 1))
        rim_ramp.color_ramp.elements[1].position = 0.8
        rim_ramp.color_ramp.elements[1].color = (*rim_color, 1.0)
        _link(mat, fresnel, "Fac", rim_ramp, "Fac")

        mix_rgb = mat.node_tree.nodes.new(type="ShaderNodeMix")
        mix_rgb.data_type = "RGBA"
        mix_rgb.location = (500, 0)
        _link(mat, ramp, "Color", mix_rgb, 6)  # A
        _link(mat, rim_ramp, "Color", mix_rgb, 7)  # B
        _link(mat, fresnel, "Fac", mix_rgb, "Factor")
        mix_rgb.blend_type = "ADD" if hasattr(mix_rgb, "blend_type") else "MIX"

        # Re-link to output
        for link in mat.node_tree.links:
            if link.to_node == output:
                mat.node_tree.links.remove(link)
        _link(mat, mix_rgb, 2, output, "Surface")


# ==================== Main Handler Functions ====================


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create procedural material"""
    preset = params.get("preset", "STEEL")
    material_name = params.get("material_name") or f"Proc_{preset}"
    object_name = params.get("object_name")
    color_override = params.get("color_override")
    scale = params.get("scale", 1.0)
    roughness_override = params.get("roughness_override")

    # Find preset data
    all_presets = {}
    all_presets.update({k: ("metal", v) for k, v in METAL_PRESETS.items()})
    all_presets.update({k: ("wood", v) for k, v in WOOD_PRESETS.items()})
    all_presets.update({k: ("stone", v) for k, v in STONE_PRESETS.items()})
    all_presets.update({k: ("fabric", v) for k, v in FABRIC_PRESETS.items()})
    all_presets.update({k: ("nature", v) for k, v in NATURE_PRESETS.items()})
    all_presets.update({k: ("skin", v) for k, v in SKIN_PRESETS.items()})
    all_presets.update({k: ("effect", v) for k, v in EFFECT_PRESETS.items()})
    all_presets.update({k: ("toon", v) for k, v in TOON_PRESETS.items()})

    preset_upper = preset.upper()
    if preset_upper not in all_presets:
        available = ", ".join(sorted(all_presets.keys()))
        return {
            "success": False,
            "error": {
                "code": "UNKNOWN_PRESET",
                "message": f"Unknown preset: {preset}. Available presets: {available}",
            },
        }

    category, preset_data = all_presets[preset_upper]

    try:
        mat = _get_or_create_material(material_name)

        color_tuple = tuple(color_override[:3]) if color_override else None

        creators = {
            "metal": _create_metal,
            "wood": _create_wood,
            "stone": _create_stone,
            "fabric": _create_fabric,
            "nature": _create_nature,
            "skin": _create_skin,
            "effect": _create_effect,
            "toon": _create_toon,
        }

        creator = creators.get(category)
        if creator:
            creator(mat, preset_data, scale, color_tuple, roughness_override)

        # Apply to object
        applied_to = ""
        if object_name:
            _apply_to_object(mat, object_name)
            applied_to = object_name

    except Exception as e:
        return {"success": False, "error": {"code": "CREATE_FAILED", "message": str(e)}}

    return {
        "success": True,
        "data": {
            "material_name": mat.name,
            "preset": preset,
            "category": category,
            "applied_to": applied_to,
        },
    }


def handle_wear(params: dict[str, Any]) -> dict[str, Any]:
    """Add wear effect"""
    object_name = params.get("object_name", "")
    material_name = params.get("material_name", "")
    wear_type = params.get("wear_type", "EDGE_WEAR")
    intensity = params.get("intensity", 0.5)
    wear_color = params.get("color")

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object not found or not a mesh: {object_name}",
            },
        }

    # Get material
    if material_name:
        mat = bpy.data.materials.get(material_name)
    elif obj.data.materials:
        mat = obj.data.materials[0]
    else:
        return {
            "success": False,
            "error": {"code": "NO_MATERIAL", "message": "Object has no material"},
        }

    if not mat or not mat.use_nodes:
        return {
            "success": False,
            "error": {
                "code": "INVALID_MATERIAL",
                "message": "Material is invalid or not using nodes",
            },
        }

    try:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Find Principled BSDF
        bsdf = None
        for node in nodes:
            if node.type == "BSDF_PRINCIPLED":
                bsdf = node
                break

        if not bsdf:
            return {
                "success": False,
                "error": {
                    "code": "NO_BSDF",
                    "message": "No Principled BSDF node found in material",
                },
            }

        # Default wear colors
        default_colors = {
            "EDGE_WEAR": (0.9, 0.9, 0.9),
            "SCRATCHES": (0.7, 0.7, 0.7),
            "RUST": (0.5, 0.25, 0.08),
            "DIRT": (0.2, 0.15, 0.1),
            "DUST": (0.6, 0.55, 0.48),
            "MOSS": (0.1, 0.3, 0.05),
            "PAINT_CHIP": (0.15, 0.15, 0.15),
        }
        wc = tuple(wear_color[:3]) if wear_color else default_colors.get(wear_type, (0.5, 0.5, 0.5))

        # Use Geometry node to get Pointiness (curvature)
        geo_node = nodes.new(type="ShaderNodeNewGeometry")
        geo_node.location = (bsdf.location.x - 600, bsdf.location.y - 400)

        # Noise for wear pattern variation
        noise = nodes.new(type="ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 15.0
        noise.inputs["Detail"].default_value = 4.0
        noise.location = (bsdf.location.x - 600, bsdf.location.y - 600)

        # ColorRamp to control wear mask
        ramp = nodes.new(type="ShaderNodeValToRGB")
        ramp.location = (bsdf.location.x - 400, bsdf.location.y - 400)
        # Adjust ramp based on intensity
        ramp.color_ramp.elements[0].position = 1.0 - intensity * 0.5
        ramp.color_ramp.elements[1].position = 1.0 - intensity * 0.3

        if wear_type in ("EDGE_WEAR", "SCRATCHES", "PAINT_CHIP"):
            # Edge-based: use Pointiness
            _link(mat, geo_node, "Pointiness", ramp, "Fac")
        else:
            # Surface-based: use noise
            mix_math = nodes.new(type="ShaderNodeMath")
            mix_math.operation = "ADD"
            mix_math.location = (bsdf.location.x - 500, bsdf.location.y - 500)
            _link(mat, geo_node, "Pointiness", mix_math, 0)
            _link(mat, noise, "Fac", mix_math, 1)
            _link(mat, mix_math, "Value", ramp, "Fac")

        # Mix wear color with base color
        # Find current base color connection
        base_input = bsdf.inputs["Base Color"]
        old_link = None
        old_color = base_input.default_value[:]
        for link in links:
            if link.to_socket == base_input:
                old_link = link
                break

        mix_node = nodes.new(type="ShaderNodeMix")
        mix_node.data_type = "RGBA"
        mix_node.location = (bsdf.location.x - 200, bsdf.location.y - 200)
        _link(mat, ramp, "Color", mix_node, "Factor")

        if old_link:
            # Reconnect old link to mix A
            from_socket = old_link.from_socket
            links.remove(old_link)
            links.new(from_socket, mix_node.inputs[6])
        else:
            mix_node.inputs[6].default_value = old_color

        mix_node.inputs[7].default_value = (*wc, 1.0)
        _link(mat, mix_node, 2, bsdf, "Base Color")

        # Adjust roughness for wear areas
        if wear_type in ("RUST", "DIRT", "DUST", "MOSS"):
            rough_mix = nodes.new(type="ShaderNodeMath")
            rough_mix.operation = "MAXIMUM"
            rough_mix.inputs[1].default_value = 0.8
            rough_mix.location = (bsdf.location.x - 200, bsdf.location.y - 500)
            _link(mat, ramp, "Color", rough_mix, 0)

    except Exception as e:
        return {"success": False, "error": {"code": "WEAR_FAILED", "message": str(e)}}

    return {"success": True, "data": {"wear_type": wear_type, "intensity": intensity}}
