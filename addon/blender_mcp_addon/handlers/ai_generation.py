"""
AI-assisted modeling handler

Handles AI texture generation, material creation, and related commands.
Note: Actual AI service calls should be performed on the MCP server side; this handles Blender-side operations.
"""

import os
import tempfile
from typing import Any

import bpy

from .node_utils import find_principled_bsdf as get_principled_bsdf

# AI configuration storage
AI_CONFIG = {
    "provider": "stability",
    "api_key": None,
    "local_url": "http://127.0.0.1:7860",
    "model": "sdxl-1.0",
}


def handle_config(params: dict[str, Any]) -> dict[str, Any]:
    """Configure AI service"""
    global AI_CONFIG

    try:
        if params.get("provider"):
            AI_CONFIG["provider"] = params["provider"]
        if params.get("api_key"):
            AI_CONFIG["api_key"] = params["api_key"]
        if params.get("local_url"):
            AI_CONFIG["local_url"] = params["local_url"]
        if params.get("model"):
            AI_CONFIG["model"] = params["model"]

        return {
            "success": True,
            "data": {
                "provider": AI_CONFIG["provider"],
                "model": AI_CONFIG["model"],
                "local_url": AI_CONFIG["local_url"] if AI_CONFIG["provider"] == "local" else None,
                "api_key_set": bool(AI_CONFIG["api_key"]),
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CONFIG_ERROR", "message": str(e)}}


def handle_texture_generate(params: dict[str, Any]) -> dict[str, Any]:
    """AI texture generation"""
    prompt = params.get("prompt")
    params.get("negative_prompt", "")
    width = params.get("width", 1024)
    height = params.get("height", 1024)
    seamless = params.get("seamless", True)
    apply_to = params.get("apply_to", "")

    try:
        # Note: Actual AI generation should be done on the MCP server side
        # Here we simulate generation and handle Blender-side operations

        # Build full prompt
        full_prompt = prompt
        if seamless:
            full_prompt += ", seamless texture, tileable, pattern"

        # Create a temporary solid color texture as a placeholder
        # In the actual implementation, the MCP server would call the AI API to generate and save images
        temp_dir = tempfile.gettempdir()
        os.path.join(temp_dir, f"ai_texture_{hash(prompt)}.png")

        # Create new image
        img = bpy.data.images.new(name=f"AI_{prompt[:20]}", width=width, height=height, alpha=True)

        # If a target object is specified
        if apply_to:
            obj = bpy.data.objects.get(apply_to)
            if obj and obj.type == "MESH":
                # Create material
                mat = bpy.data.materials.new(name=f"AI_Material_{prompt[:15]}")
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links

                # Clear default nodes
                nodes.clear()

                # Create nodes
                output = nodes.new("ShaderNodeOutputMaterial")
                output.location = (300, 0)

                bsdf = nodes.new("ShaderNodeBsdfPrincipled")
                bsdf.location = (0, 0)

                tex_node = nodes.new("ShaderNodeTexImage")
                tex_node.location = (-300, 0)
                tex_node.image = img

                # Connect
                links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
                links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

                # Apply material
                if obj.data.materials:
                    obj.data.materials[0] = mat
                else:
                    obj.data.materials.append(mat)

        return {
            "success": True,
            "data": {
                "image_name": img.name,
                "prompt": full_prompt,
                "size": [width, height],
                "applied_to": apply_to,
                "note": "AI generation requires API configuration. Use blender_ai_config to set up.",
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "TEXTURE_GEN_ERROR", "message": str(e)}}


def handle_concept_art(params: dict[str, Any]) -> dict[str, Any]:
    """Generate concept art"""
    prompt = params.get("prompt")
    style = params.get("style", "realistic")
    aspect_ratio = params.get("aspect_ratio", "16:9")

    try:
        # Parse aspect ratio
        ratio_map = {
            "16:9": (1920, 1080),
            "1:1": (1024, 1024),
            "4:3": (1024, 768),
            "9:16": (1080, 1920),
        }
        width, height = ratio_map.get(aspect_ratio, (1920, 1080))

        # Add style prompts
        style_prompts = {
            "realistic": "photorealistic, detailed, high quality",
            "anime": "anime style, cel shaded, vibrant colors",
            "cartoon": "cartoon style, bold lines, stylized",
            "sketch": "pencil sketch, line art, concept art drawing",
        }

        full_prompt = f"{prompt}, {style_prompts.get(style, '')}"

        # Create image placeholder
        img = bpy.data.images.new(
            name=f"Concept_{prompt[:20]}", width=width, height=height, alpha=False
        )

        return {
            "success": True,
            "data": {
                "image_name": img.name,
                "prompt": full_prompt,
                "style": style,
                "size": [width, height],
                "note": "AI generation requires API configuration.",
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CONCEPT_ART_ERROR", "message": str(e)}}


def handle_material_from_text(params: dict[str, Any]) -> dict[str, Any]:
    """Generate material from text description"""
    description = params.get("description")
    object_name = params.get("object_name", "")
    params.get("generate_textures", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Parse material description
        desc_lower = description.lower()

        # Create material
        mat = bpy.data.materials.new(name=f"AI_{description[:20]}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        # Get Principled BSDF
        bsdf = get_principled_bsdf(nodes)
        if not bsdf:
            bsdf = nodes.new("ShaderNodeBsdfPrincipled")

        # Set parameters based on description
        # Metals
        if any(word in desc_lower for word in ["metal", "steel", "iron", "chrome", "aluminum"]):
            bsdf.inputs["Metallic"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = 0.3

            if "rust" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (0.4, 0.2, 0.1, 1.0)
                bsdf.inputs["Roughness"].default_value = 0.8
            elif "gold" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
            elif "silver" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (0.972, 0.960, 0.915, 1.0)
            elif "copper" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (0.955, 0.637, 0.538, 1.0)
            else:
                bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)

        # Wood
        elif any(word in desc_lower for word in ["wood", "wooden", "oak", "pine"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.7
            bsdf.inputs["Base Color"].default_value = (0.4, 0.25, 0.13, 1.0)

        # Stone
        elif any(word in desc_lower for word in ["stone", "marble", "granite", "concrete"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            if "marble" in desc_lower:
                bsdf.inputs["Roughness"].default_value = 0.2
                bsdf.inputs["Base Color"].default_value = (0.95, 0.95, 0.95, 1.0)
            else:
                bsdf.inputs["Roughness"].default_value = 0.8
                bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1.0)

        # Glass
        elif any(word in desc_lower for word in ["glass", "transparent", "crystal"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.0
            bsdf.inputs["Transmission"].default_value = 1.0
            bsdf.inputs["IOR"].default_value = 1.45

        # Fabric
        elif any(word in desc_lower for word in ["fabric", "cloth", "velvet", "silk"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.8
            bsdf.inputs["Sheen Weight"].default_value = 0.5

        # Leather
        elif any(word in desc_lower for word in ["leather"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.6
            bsdf.inputs["Base Color"].default_value = (0.3, 0.2, 0.15, 1.0)

        # Plastic
        elif any(word in desc_lower for word in ["plastic"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.3
            bsdf.inputs["Specular IOR Level"].default_value = 0.5

        # Apply material
        if obj.type == "MESH":
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)

        return {
            "success": True,
            "data": {
                "material_name": mat.name,
                "description": description,
                "applied_to": object_name,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "MATERIAL_FROM_TEXT_ERROR", "message": str(e)}}


def handle_upscale(params: dict[str, Any]) -> dict[str, Any]:
    """AI texture upscaling"""
    image_path = params.get("image_path")
    scale = params.get("scale", 2)

    try:
        # Check if image exists
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": {"code": "IMAGE_NOT_FOUND", "message": f"Image not found: {image_path}"},
            }

        # Load image
        img = bpy.data.images.load(image_path)
        original_size = [img.size[0], img.size[1]]

        # Calculate new dimensions
        new_width = original_size[0] * scale
        new_height = original_size[1] * scale

        # Note: Actual AI upscaling needs to be done on the MCP server side
        # Here we use Blender's scaling as a placeholder
        img.scale(new_width, new_height)

        # Save
        output_path = image_path.replace(".", f"_x{scale}.")
        img.filepath_raw = output_path
        img.file_format = "PNG"
        img.save()

        return {
            "success": True,
            "data": {
                "input": image_path,
                "output": output_path,
                "original_size": original_size,
                "new_size": [new_width, new_height],
                "scale": scale,
                "note": "True AI upscaling requires API configuration.",
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "UPSCALE_ERROR", "message": str(e)}}


def handle_remove_background(params: dict[str, Any]) -> dict[str, Any]:
    """Background removal"""
    image_path = params.get("image_path")
    output_path = params.get("output_path")

    try:
        if not os.path.exists(image_path):
            return {
                "success": False,
                "error": {"code": "IMAGE_NOT_FOUND", "message": f"Image not found: {image_path}"},
            }

        # Generate output path
        if not output_path:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_nobg.png"

        # Load image
        img = bpy.data.images.load(image_path)

        # Note: Actual background removal requires an AI service
        # Here we only return information

        return {
            "success": True,
            "data": {
                "input": image_path,
                "output": output_path,
                "image_name": img.name,
                "note": "AI background removal requires API configuration.",
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "REMOVE_BG_ERROR", "message": str(e)}}


def handle_image_to_reference(params: dict[str, Any]) -> dict[str, Any]:
    """Generate image and set as reference"""
    prompt = params.get("prompt")
    as_background = params.get("as_background", False)

    try:
        # Create reference image placeholder
        img = bpy.data.images.new(
            name=f"Reference_{prompt[:20]}", width=1920, height=1080, alpha=True
        )

        if as_background:
            # Set as world background
            world = bpy.context.scene.world
            if not world:
                world = bpy.data.worlds.new("World")
                bpy.context.scene.world = world

            world.use_nodes = True
            nodes = world.node_tree.nodes
            links = world.node_tree.links

            # Add environment texture node
            env_tex = nodes.new("ShaderNodeTexEnvironment")
            env_tex.image = img

            bg = nodes.get("Background")
            if bg:
                links.new(env_tex.outputs["Color"], bg.inputs["Color"])
        else:
            # Create as empty object reference image
            bpy.ops.object.empty_add(type="IMAGE", location=(0, -5, 0))
            empty = bpy.context.active_object
            empty.name = f"Reference_{prompt[:15]}"
            empty.data = img
            empty.empty_display_size = 5

        return {
            "success": True,
            "data": {
                "image_name": img.name,
                "prompt": prompt,
                "as_background": as_background,
                "note": "AI generation requires API configuration.",
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "REFERENCE_ERROR", "message": str(e)}}
