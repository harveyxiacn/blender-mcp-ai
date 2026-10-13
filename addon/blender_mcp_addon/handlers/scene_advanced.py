"""
Advanced Scene Handler

Handles environment presets, procedural generation, sky setup and other commands.
"""

import math
import random
from typing import Any

import bpy

# Environment preset configuration
ENVIRONMENT_PRESETS = {
    "studio": {
        "world_color": [0.05, 0.05, 0.05],
        "lights": [
            {"type": "AREA", "location": [2, -2, 3], "power": 500, "color": [1, 1, 1]},
            {"type": "AREA", "location": [-2, -2, 2], "power": 200, "color": [0.9, 0.95, 1]},
            {"type": "AREA", "location": [0, 2, 2], "power": 100, "color": [1, 0.95, 0.9]},
        ],
    },
    "outdoor_day": {
        "world_color": [0.4, 0.6, 0.9],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 5,
                "color": [1, 0.98, 0.95],
                "rotation": [0.8, 0.2, 0],
            },
        ],
    },
    "outdoor_night": {
        "world_color": [0.01, 0.02, 0.05],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 0.1,
                "color": [0.7, 0.8, 1],
                "rotation": [0.6, 0.3, 0],
            },
        ],
    },
    "sunset": {
        "world_color": [0.3, 0.2, 0.15],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 3,
                "color": [1, 0.6, 0.3],
                "rotation": [0.2, 0, 0],
            },
        ],
    },
    "indoor": {
        "world_color": [0.02, 0.02, 0.02],
        "lights": [
            {"type": "AREA", "location": [0, 0, 2.5], "power": 300, "color": [1, 0.95, 0.9]},
        ],
    },
    "stadium": {
        "world_color": [0.1, 0.1, 0.15],
        "lights": [
            {"type": "AREA", "location": [10, 10, 15], "power": 2000, "color": [1, 1, 1]},
            {"type": "AREA", "location": [-10, 10, 15], "power": 2000, "color": [1, 1, 1]},
            {"type": "AREA", "location": [10, -10, 15], "power": 2000, "color": [1, 1, 1]},
            {"type": "AREA", "location": [-10, -10, 15], "power": 2000, "color": [1, 1, 1]},
        ],
    },
    "space": {
        "world_color": [0.0, 0.0, 0.0],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 10,
                "color": [1, 1, 1],
                "rotation": [0.5, 0, 0],
            },
        ],
    },
    "forest": {
        "world_color": [0.15, 0.25, 0.12],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 3,
                "color": [1, 0.95, 0.85],
                "rotation": [0.7, 0.3, 0],
            },
            {"type": "AREA", "location": [5, 5, 8], "power": 200, "color": [0.9, 1, 0.85]},
        ],
    },
    "underwater": {
        "world_color": [0.05, 0.15, 0.25],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 2,
                "color": [0.6, 0.8, 1],
                "rotation": [0.9, 0, 0],
            },
        ],
    },
    "desert": {
        "world_color": [0.6, 0.5, 0.35],
        "lights": [
            {
                "type": "SUN",
                "location": [0, 0, 10],
                "power": 8,
                "color": [1, 0.95, 0.85],
                "rotation": [0.6, 0.2, 0],
            },
        ],
    },
}

# Ground material presets
GROUND_MATERIALS = {
    "concrete": {"color": [0.5, 0.5, 0.5, 1], "roughness": 0.8},
    "grass": {"color": [0.2, 0.5, 0.1, 1], "roughness": 0.9},
    "wood": {"color": [0.5, 0.3, 0.15, 1], "roughness": 0.7},
    "marble": {"color": [0.9, 0.9, 0.9, 1], "roughness": 0.2},
    "sand": {"color": [0.8, 0.7, 0.5, 1], "roughness": 0.95},
    "water": {"color": [0.1, 0.3, 0.5, 1], "roughness": 0.1, "metallic": 0.5},
}


def handle_environment_preset(params: dict[str, Any]) -> dict[str, Any]:
    """Apply environment preset"""
    preset = params.get("preset", "studio")
    intensity = params.get("intensity", 1.0)

    config = ENVIRONMENT_PRESETS.get(preset)
    if not config:
        return {
            "success": False,
            "error": {"code": "PRESET_NOT_FOUND", "message": f"Preset not found: {preset}"},
        }

    # Set world background color
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        color = config["world_color"]
        bg_node.inputs["Color"].default_value = [c * intensity for c in color] + [1]
        bg_node.inputs["Strength"].default_value = intensity

    # Delete existing environment lights
    for obj in list(bpy.data.objects):
        if obj.name.startswith("Env_Light_"):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Create lights
    for i, light_config in enumerate(config["lights"]):
        light_type = light_config["type"]

        if light_type == "SUN":
            bpy.ops.object.light_add(type="SUN", location=light_config["location"])
        else:
            bpy.ops.object.light_add(type="AREA", location=light_config["location"])

        light_obj = bpy.context.active_object
        light_obj.name = f"Env_Light_{i}"

        light = light_obj.data
        light.energy = light_config["power"] * intensity
        light.color = light_config["color"]

        if "rotation" in light_config:
            light_obj.rotation_euler = light_config["rotation"]

    return {"success": True, "data": {"preset": preset, "lights_created": len(config["lights"])}}


def handle_scatter(params: dict[str, Any]) -> dict[str, Any]:
    """Scatter objects"""
    source_name = params.get("source_object", "")
    target_name = params.get("target_surface", "")
    count = params.get("count", 100)
    seed = params.get("seed", 0)
    scale_min = params.get("scale_min", 0.8)
    scale_max = params.get("scale_max", 1.2)
    rotation_random = params.get("rotation_random", True)
    align_to_normal = params.get("align_to_normal", True)

    source_obj = bpy.data.objects.get(source_name)
    target_obj = bpy.data.objects.get(target_name)

    if not source_obj:
        return {
            "success": False,
            "error": {
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source object not found: {source_name}",
            },
        }

    if not target_obj or target_obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "TARGET_NOT_FOUND",
                "message": f"Target surface not found: {target_name}",
            },
        }

    random.seed(seed)

    # Get target mesh data
    mesh = target_obj.data
    mesh.calc_loop_triangles()

    instances_created = 0

    # Create instance collection
    collection_name = f"Scatter_{source_name}"
    if collection_name in bpy.data.collections:
        scatter_collection = bpy.data.collections[collection_name]
    else:
        scatter_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(scatter_collection)

    # Random sampling on triangles
    for i in range(count):
        if len(mesh.loop_triangles) == 0:
            break

        # Randomly select a triangle
        tri = random.choice(list(mesh.loop_triangles))

        # Random sampling on triangles
        u, v = random.random(), random.random()
        if u + v > 1:
            u, v = 1 - u, 1 - v

        v1 = mesh.vertices[tri.vertices[0]].co
        v2 = mesh.vertices[tri.vertices[1]].co
        v3 = mesh.vertices[tri.vertices[2]].co

        pos = v1 + u * (v2 - v1) + v * (v3 - v1)
        pos = target_obj.matrix_world @ pos

        # Create instance
        instance = source_obj.copy()
        instance.data = source_obj.data
        instance.name = f"{source_name}_instance_{i}"

        # Set location
        instance.location = pos

        # Random scale
        scale = random.uniform(scale_min, scale_max)
        instance.scale = [scale, scale, scale]

        # Random rotation
        if rotation_random:
            instance.rotation_euler[2] = random.uniform(0, 2 * math.pi)

        # Align to normal
        if align_to_normal:
            normal = tri.normal
            # Simplified normal alignment
            instance.rotation_euler[0] = math.asin(normal[1])
            instance.rotation_euler[1] = -math.asin(normal[0])

        scatter_collection.objects.link(instance)
        instances_created += 1

    return {
        "success": True,
        "data": {"instances_created": instances_created, "collection": collection_name},
    }


def handle_array_generate(params: dict[str, Any]) -> dict[str, Any]:
    """Array generation"""
    object_name = params.get("object_name", "")
    count_x = params.get("count_x", 1)
    count_y = params.get("count_y", 1)
    count_z = params.get("count_z", 1)
    offset_x = params.get("offset_x", 2.0)
    offset_y = params.get("offset_y", 2.0)
    offset_z = params.get("offset_z", 2.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Create collection
    collection_name = f"Array_{object_name}"
    if collection_name in bpy.data.collections:
        array_collection = bpy.data.collections[collection_name]
    else:
        array_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(array_collection)

    base_loc = obj.location.copy()
    instances_created = 0

    for x in range(count_x):
        for y in range(count_y):
            for z in range(count_z):
                if x == 0 and y == 0 and z == 0:
                    continue  # Skip original object position

                instance = obj.copy()
                instance.data = obj.data
                instance.name = f"{object_name}_array_{x}_{y}_{z}"

                instance.location = [
                    base_loc[0] + x * offset_x,
                    base_loc[1] + y * offset_y,
                    base_loc[2] + z * offset_z,
                ]

                array_collection.objects.link(instance)
                instances_created += 1

    return {
        "success": True,
        "data": {"instances_created": instances_created, "collection": collection_name},
    }


def handle_ground_plane(params: dict[str, Any]) -> dict[str, Any]:
    """Create ground plane"""
    size = params.get("size", 100.0)
    material_preset = params.get("material_preset", "concrete")
    location = params.get("location", [0, 0, 0])

    # Create plane
    bpy.ops.mesh.primitive_plane_add(size=size, location=location)
    ground = bpy.context.active_object
    ground.name = "Ground"

    # Apply material
    mat_config = GROUND_MATERIALS.get(material_preset, GROUND_MATERIALS["concrete"])

    mat = bpy.data.materials.new(name=f"Ground_{material_preset}")
    mat.use_nodes = True

    # Find Principled BSDF node (compatible across Blender versions)
    bsdf = None
    for node in mat.node_tree.nodes:
        if node.type == "BSDF_PRINCIPLED":
            bsdf = node
            break

    if bsdf:
        bsdf.inputs["Base Color"].default_value = mat_config["color"]
        bsdf.inputs["Roughness"].default_value = mat_config.get("roughness", 0.5)
        if "metallic" in mat_config:
            bsdf.inputs["Metallic"].default_value = mat_config["metallic"]

    ground.data.materials.append(mat)

    return {"success": True, "data": {"ground_name": ground.name, "material": material_preset}}


def handle_sky_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Set up sky"""
    sky_type = params.get("sky_type", "hosek_wilkie")
    sun_elevation = params.get("sun_elevation", 45.0)
    sun_rotation = params.get("sun_rotation", 0.0)
    turbidity = params.get("turbidity", 2.0)

    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create sky texture node
    sky_node = nodes.new("ShaderNodeTexSky")
    sky_node.sky_type = "NISHITA" if sky_type == "nishita" else "HOSEK_WILKIE"
    sky_node.sun_elevation = math.radians(sun_elevation)
    sky_node.sun_rotation = math.radians(sun_rotation)
    if hasattr(sky_node, "turbidity"):
        sky_node.turbidity = turbidity

    # Create background node
    bg_node = nodes.new("ShaderNodeBackground")
    bg_node.inputs["Strength"].default_value = 1.0

    # Create output node
    output_node = nodes.new("ShaderNodeOutputWorld")

    # Connect nodes
    links.new(sky_node.outputs["Color"], bg_node.inputs["Color"])
    links.new(bg_node.outputs["Background"], output_node.inputs["Surface"])

    return {"success": True, "data": {"sky_type": sky_type}}


def handle_fog_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add fog effect"""
    density = params.get("density", 0.1)
    color = params.get("color", [0.8, 0.9, 1.0])
    height = params.get("height", 0.0)
    params.get("falloff", 1.0)

    # Create volume cube
    bpy.ops.mesh.primitive_cube_add(size=100, location=[0, 0, height + 25])
    fog_volume = bpy.context.active_object
    fog_volume.name = "Fog_Volume"
    fog_volume.scale = [1, 1, 0.5]

    # Create volume material
    mat = bpy.data.materials.new(name="Fog_Material")
    mat.use_nodes = True

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    nodes.clear()

    # Volume scatter node
    scatter_node = nodes.new("ShaderNodeVolumeScatter")
    scatter_node.inputs["Color"].default_value = color + [1]
    scatter_node.inputs["Density"].default_value = density

    # Output node
    output_node = nodes.new("ShaderNodeOutputMaterial")

    links.new(scatter_node.outputs["Volume"], output_node.inputs["Volume"])

    fog_volume.data.materials.append(mat)

    return {"success": True, "data": {"fog_volume": fog_volume.name}}
