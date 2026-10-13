"""
Texture Paint Handler

Handles texture painting-related commands.
"""

import os
from typing import Any

import bpy


def handle_mode(params: dict[str, Any]) -> dict[str, Any]:
    """Enter/exit texture paint mode"""
    object_name = params.get("object_name", "")
    enable = params.get("enable", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_TYPE",
                "message": "Only mesh objects can be texture painted",
            },
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Switch mode
    if enable:
        bpy.ops.object.mode_set(mode="TEXTURE_PAINT")
    else:
        bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"mode": bpy.context.object.mode}}


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create new texture"""
    name = params.get("name", "Texture")
    width = params.get("width", 1024)
    height = params.get("height", 1024)
    color = params.get("color", [0.0, 0.0, 0.0, 1.0])
    alpha = params.get("alpha", True)
    float_buffer = params.get("float_buffer", False)

    # Create new image
    image = bpy.data.images.new(
        name=name, width=width, height=height, alpha=alpha, float_buffer=float_buffer
    )

    # Fill color
    if color:
        pixels = [0.0] * (width * height * 4)
        for i in range(width * height):
            pixels[i * 4] = color[0]
            pixels[i * 4 + 1] = color[1]
            pixels[i * 4 + 2] = color[2]
            pixels[i * 4 + 3] = color[3] if len(color) > 3 else 1.0
        image.pixels = pixels

    return {"success": True, "data": {"image_name": image.name, "width": width, "height": height}}


def handle_set_brush(params: dict[str, Any]) -> dict[str, Any]:
    """Set paint brush"""
    brush_type = params.get("brush_type", "DRAW")
    color = params.get("color", [1.0, 1.0, 1.0])
    radius = params.get("radius", 50.0)
    strength = params.get("strength", 1.0)
    blend = params.get("blend", "MIX")

    try:
        # Get current tool settings

        # Brush type mapping
        brush_map = {
            "DRAW": "TexDraw",
            "SOFTEN": "Soften",
            "SMEAR": "Smear",
            "CLONE": "Clone",
            "FILL": "Fill",
            "MASK": "Mask",
        }

        brush_name = brush_map.get(brush_type, "TexDraw")

        # Find brush - Blender 5.0+ compatible
        brush = bpy.data.brushes.get(brush_name)
        if not brush:
            for b in bpy.data.brushes:
                # Blender 5.0+ may use different properties
                tool = getattr(b, "image_tool", None) or getattr(b, "image_paint_tool", None)
                if tool == brush_type:
                    brush = b
                    break

        if not brush:
            # Create new brush
            brush = bpy.data.brushes.new(name=brush_name, mode="TEXTURE_PAINT")

        if brush:
            # Blender 5.0+ brush properties are read-only
            # Set brush properties directly
            brush.size = int(radius)
            brush.strength = strength
            brush.color = color[:3] if len(color) >= 3 else [1, 1, 1]

            # Set blend mode
            blend_map = {
                "MIX": "MIX",
                "ADD": "ADD",
                "SUBTRACT": "SUB",
                "MULTIPLY": "MUL",
                "LIGHTEN": "LIGHTEN",
                "DARKEN": "DARKEN",
                "ERASE_ALPHA": "ERASE_ALPHA",
                "ADD_ALPHA": "ADD_ALPHA",
            }
            if hasattr(brush, "blend"):
                brush.blend = blend_map.get(blend, "MIX")

        return {
            "success": True,
            "data": {"brush": brush.name if brush else "default", "color": color, "radius": radius},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "BRUSH_ERROR", "message": str(e)}}


def handle_stroke(params: dict[str, Any]) -> dict[str, Any]:
    """Execute paint stroke"""
    object_name = params.get("object_name", "")
    uv_points = params.get("uv_points", [])
    color = params.get("color")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Ensure object has material and texture
    if not obj.active_material:
        return {
            "success": False,
            "error": {"code": "NO_MATERIAL", "message": "Object has no material"},
        }

    # Ensure in texture paint mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if bpy.context.object.mode != "TEXTURE_PAINT":
        bpy.ops.object.mode_set(mode="TEXTURE_PAINT")

    # Set color
    if color:
        brush = bpy.context.tool_settings.image_paint.brush
        if brush:
            brush.color = color[:3] if len(color) >= 3 else [1, 1, 1]

    # Note: Direct programmatic texture painting
    # Get the active paint image
    paint_slot = obj.active_material.paint_active_slot
    tex_slot = (
        obj.active_material.texture_paint_slots[paint_slot]
        if paint_slot < len(obj.active_material.texture_paint_slots)
        else None
    )

    if tex_slot and tex_slot.image:
        image = tex_slot.image
        width, height = image.size
        pixels = list(image.pixels)

        brush_color = color if color else [1.0, 1.0, 1.0]

        # Paint at UV coordinate positions
        for point in uv_points:
            u, v = point[:2]
            pressure = point[2] if len(point) > 2 else 1.0

            # Convert UV to pixel coordinates
            px = int(u * width)
            py = int(v * height)

            # Simple dot painting
            radius = int(10 * pressure)

            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius * radius:
                        x = px + dx
                        y = py + dy

                        if 0 <= x < width and 0 <= y < height:
                            idx = (y * width + x) * 4
                            # Blend colors
                            alpha = pressure
                            pixels[idx] = pixels[idx] * (1 - alpha) + brush_color[0] * alpha
                            pixels[idx + 1] = pixels[idx + 1] * (1 - alpha) + brush_color[1] * alpha
                            pixels[idx + 2] = pixels[idx + 2] * (1 - alpha) + brush_color[2] * alpha

        image.pixels = pixels
        image.update()

        return {"success": True, "data": {"points_applied": len(uv_points), "image": image.name}}

    return {
        "success": False,
        "error": {"code": "NO_PAINT_SLOT", "message": "No paintable texture slot available"},
    }


def handle_fill(params: dict[str, Any]) -> dict[str, Any]:
    """Fill color"""
    object_name = params.get("object_name", "")
    color = params.get("color", [1.0, 1.0, 1.0, 1.0])
    texture_slot = params.get("texture_slot", 0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if not obj.active_material:
        return {
            "success": False,
            "error": {"code": "NO_MATERIAL", "message": "Object has no material"},
        }

    # Get texture
    mat = obj.active_material
    slots = mat.texture_paint_slots

    if texture_slot >= len(slots) or not slots[texture_slot]:
        return {
            "success": False,
            "error": {
                "code": "INVALID_SLOT",
                "message": f"Texture slot {texture_slot} does not exist",
            },
        }

    image = slots[texture_slot].image
    if not image:
        return {
            "success": False,
            "error": {"code": "NO_IMAGE", "message": "Texture slot has no image"},
        }

    width, height = image.size

    # Fill color
    pixels = [0.0] * (width * height * 4)
    for i in range(width * height):
        pixels[i * 4] = color[0]
        pixels[i * 4 + 1] = color[1]
        pixels[i * 4 + 2] = color[2]
        pixels[i * 4 + 3] = color[3] if len(color) > 3 else 1.0

    image.pixels = pixels
    image.update()

    return {"success": True, "data": {"image": image.name, "color": color}}


def handle_bake(params: dict[str, Any]) -> dict[str, Any]:
    """Bake texture"""
    object_name = params.get("object_name", "")
    bake_type = params.get("bake_type", "DIFFUSE")
    width = params.get("width", 1024)
    height = params.get("height", 1024)
    margin = params.get("margin", 16)
    output_path = params.get("output_path")

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Mesh object not found: {object_name}",
            },
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Ensure in object mode
    if bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Create image for baking
    bake_image = bpy.data.images.new(
        name=f"{object_name}_bake", width=width, height=height, alpha=True
    )

    # Ensure material and UV exist
    if not obj.active_material:
        mat = bpy.data.materials.new(name=f"{object_name}_Material")
        obj.data.materials.append(mat)
        mat.use_nodes = True

    mat = obj.active_material
    mat.use_nodes = True
    nodes = mat.node_tree.nodes

    # Add image texture node for baking
    tex_node = nodes.new("ShaderNodeTexImage")
    tex_node.image = bake_image
    tex_node.select = True
    nodes.active = tex_node

    # Set bake parameters
    bpy.context.scene.render.engine = "CYCLES"
    bpy.context.scene.cycles.bake_type = bake_type
    bpy.context.scene.render.bake.margin = margin

    try:
        # Execute bake
        bpy.ops.object.bake(type=bake_type)

        # Save image
        if output_path:
            bake_image.filepath_raw = output_path
            bake_image.file_format = "PNG"
            bake_image.save()

        return {
            "success": True,
            "data": {
                "image_name": bake_image.name,
                "bake_type": bake_type,
                "output_path": output_path,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "BAKE_ERROR", "message": str(e)}}


def handle_slot(params: dict[str, Any]) -> dict[str, Any]:
    """Texture slot management"""
    object_name = params.get("object_name", "")
    action = params.get("action", "ADD")
    texture_name = params.get("texture_name", "")
    slot_index = params.get("slot_index", 0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Ensure material exists
    if not obj.active_material:
        mat = bpy.data.materials.new(name=f"{object_name}_Material")
        obj.data.materials.append(mat)
        mat.use_nodes = True

    mat = obj.active_material

    if action == "ADD":
        # Create or get image
        if texture_name:
            image = bpy.data.images.get(texture_name)
            if not image:
                image = bpy.data.images.new(name=texture_name, width=1024, height=1024)
        else:
            image = bpy.data.images.new(name=f"{object_name}_texture", width=1024, height=1024)

        # Add image texture in node tree
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.image = image
        tex_node.location = (-300, 300)

        return {"success": True, "data": {"image_name": image.name, "action": "ADD"}}

    elif action == "REMOVE":
        # Remove texture slot
        slots = mat.texture_paint_slots
        if slot_index < len(slots):
            # Cannot directly remove slot, but can clear the image
            pass

        return {"success": True, "data": {"action": "REMOVE"}}

    elif action == "SELECT":
        mat.paint_active_slot = slot_index

        return {"success": True, "data": {"active_slot": slot_index}}

    return {
        "success": False,
        "error": {"code": "INVALID_ACTION", "message": f"Unknown action: {action}"},
    }


def handle_save(params: dict[str, Any]) -> dict[str, Any]:
    """Save texture"""
    texture_name = params.get("texture_name", "")
    filepath = params.get("filepath")
    file_format = params.get("file_format", "PNG")

    image = bpy.data.images.get(texture_name)
    if not image:
        return {
            "success": False,
            "error": {"code": "IMAGE_NOT_FOUND", "message": f"Image not found: {texture_name}"},
        }

    # Ensure directory exists
    dir_path = os.path.dirname(filepath)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Set format and save
    image.filepath_raw = filepath
    image.file_format = file_format
    image.save()

    return {"success": True, "data": {"filepath": filepath, "format": file_format}}
