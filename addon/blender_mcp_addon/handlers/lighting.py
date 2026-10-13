"""
Lighting Handler

Handles lighting related commands.
"""

from typing import Any

import bpy


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create light"""
    light_type = params.get("type", "POINT")
    name = params.get("name")
    location = params.get("location", [0, 0, 5])
    rotation = params.get("rotation", [0, 0, 0])
    color = params.get("color", [1, 1, 1])
    energy = params.get("energy", 1000.0)
    radius = params.get("radius", 0.25)

    # Create light data. An empty name lets Blender apply its canonical
    # default ("AREA" would otherwise become the datablock's name).
    light_data = bpy.data.lights.new(name=name or "", type=light_type)
    light_data.color = color
    light_data.energy = energy

    # Set specific properties
    if light_type in ["POINT", "SPOT"]:
        light_data.shadow_soft_size = radius
    elif light_type == "AREA":
        light_data.size = radius * 4

    # Create light object
    light_obj = bpy.data.objects.new(name=name or "", object_data=light_data)
    light_obj.location = location
    light_obj.rotation_euler = rotation

    # Link to scene
    bpy.context.collection.objects.link(light_obj)

    return {"success": True, "data": {"light_name": light_obj.name}}


def handle_set_properties(params: dict[str, Any]) -> dict[str, Any]:
    """Set light properties"""
    light_name = params.get("light_name", "")
    properties = params.get("properties", {})

    if not light_name:
        return {
            "success": False,
            "error": {"code": "MISSING_PARAM", "message": "light_name parameter is required"},
        }

    obj = bpy.data.objects.get(light_name)
    if not obj or obj.type != "LIGHT":
        return {
            "success": False,
            "error": {"code": "LIGHT_NOT_FOUND", "message": f"Light not found: {light_name}"},
        }

    light = obj.data

    if "color" in properties:
        light.color = properties["color"]

    if "energy" in properties:
        light.energy = properties["energy"]

    if "radius" in properties:
        if light.type in ["POINT", "SPOT"]:
            light.shadow_soft_size = properties["radius"]
        elif light.type == "AREA":
            light.size = properties["radius"] * 4

    if "spot_size" in properties and light.type == "SPOT":
        light.spot_size = properties["spot_size"]

    if "spot_blend" in properties and light.type == "SPOT":
        light.spot_blend = properties["spot_blend"]

    if "shadow_soft_size" in properties:
        light.shadow_soft_size = properties["shadow_soft_size"]

    if "use_shadow" in properties:
        light.use_shadow = properties["use_shadow"]

    return {"success": True, "data": {}}


def handle_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete light"""
    light_name = params.get("light_name", "")

    if not light_name:
        return {
            "success": False,
            "error": {"code": "MISSING_PARAM", "message": "light_name parameter is required"},
        }

    obj = bpy.data.objects.get(light_name)
    if not obj or obj.type != "LIGHT":
        return {
            "success": False,
            "error": {"code": "LIGHT_NOT_FOUND", "message": f"Light not found: {light_name}"},
        }

    light_data = obj.data
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.lights.remove(light_data)

    return {"success": True, "data": {}}


def handle_set_energy(params: dict[str, Any]) -> dict[str, Any]:
    """Set light energy"""
    name = params.get("name", "")
    energy = params.get("energy", 1000.0)

    obj = bpy.data.objects.get(name)
    if not obj or obj.type != "LIGHT":
        return {
            "success": False,
            "error": {"code": "LIGHT_NOT_FOUND", "message": f"Light not found: {name}"},
        }

    obj.data.energy = energy

    return {"success": True, "data": {"energy": energy}}


def handle_hdri_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Set up HDRI environment lighting"""
    hdri_path = params.get("hdri_path")
    strength = params.get("strength", 1.0)
    rotation = params.get("rotation", 0.0)

    # Get or create world
    world = bpy.context.scene.world
    if not world:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world

    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links

    # Clear existing nodes
    nodes.clear()

    # Create nodes
    output = nodes.new(type="ShaderNodeOutputWorld")
    output.location = (300, 0)

    background = nodes.new(type="ShaderNodeBackground")
    background.location = (0, 0)
    background.inputs["Strength"].default_value = strength

    env_tex = nodes.new(type="ShaderNodeTexEnvironment")
    env_tex.location = (-300, 0)

    mapping = nodes.new(type="ShaderNodeMapping")
    mapping.location = (-500, 0)
    mapping.inputs["Rotation"].default_value[2] = rotation

    tex_coord = nodes.new(type="ShaderNodeTexCoord")
    tex_coord.location = (-700, 0)

    # Load HDRI
    try:
        image = bpy.data.images.load(hdri_path)
        env_tex.image = image
    except Exception as e:
        return {
            "success": False,
            "error": {"code": "IMAGE_LOAD_ERROR", "message": f"Failed to load HDRI: {e}"},
        }

    # Connect nodes
    links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], env_tex.inputs["Vector"])
    links.new(env_tex.outputs["Color"], background.inputs["Color"])
    links.new(background.outputs["Background"], output.inputs["Surface"])

    return {"success": True, "data": {}}
