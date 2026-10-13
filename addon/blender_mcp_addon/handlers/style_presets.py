"""
Style Presets Handler

Handles style environment setup, outline effects, baking workflows and other operations.
"""

import contextlib
import os
from typing import Any

import bpy

from .compat import get_eevee_engine

# ==================== Style Configuration Data ====================

STYLE_CONFIGS = {
    "PIXEL": {
        "render_engine": get_eevee_engine(),
        "shading": "FLAT",
        "texture_filter": "Closest",
        "color_management": "Standard",
        "film_transparent": False,
        "samples": 16,
        "tips": (
            "Pixel/Voxel style modeling tips:\n"
            "1. Use Cube as the basic unit, arrange via Array modifier\n"
            "2. Primitive params: segments=4~8 (low segment count)\n"
            "3. Materials: Solid color Flat material, disable Smooth Shading\n"
            "4. Textures: Use Closest (nearest neighbor) interpolation, keep pixel-sharp edges\n"
            "5. Camera: Use Orthographic projection\n"
            "6. Lighting: Simple directional light, disable shadows or use hard shadows"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Flat Shading",
            "Texture Filtering": "Closest (Nearest Neighbor)",
            "Recommended Poly Count": "50-500 faces",
            "Texture Resolution": "16×16 ~ 64×64",
        },
    },
    "LOW_POLY": {
        "render_engine": get_eevee_engine(),
        "shading": "FLAT",
        "texture_filter": "Linear",
        "color_management": "Standard",
        "film_transparent": False,
        "samples": 32,
        "tips": (
            "Low Poly style modeling tips:\n"
            "1. Primitive params: segments=6~12, subdivisions=1\n"
            "2. Use Flat Shading, do not use Subdivision Surface\n"
            "3. Coloring: Use Vertex Color or simple solid-color materials\n"
            "4. Triangles are acceptable, keep geometry clean\n"
            "5. Scene: Make heavy use of Array and Mirror modifiers\n"
            "6. Recommended: Use blender_vertex_color tool to color faces"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Flat Shading",
            "Texture Filtering": "Linear",
            "Recommended Poly Count": "200-2000 faces",
            "Texture Resolution": "No textures / Solid colors",
        },
    },
    "STYLIZED": {
        "render_engine": get_eevee_engine(),
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Standard",
        "film_transparent": False,
        "samples": 64,
        "tips": (
            "Stylized modeling tips:\n"
            "1. Use Subdivision Surface (SubSurf) level=1~2\n"
            "2. Use Bevel with support loops to maintain silhouette\n"
            "3. Materials: Use ColorRamp gradients + Shader to RGB\n"
            "4. Scene: Scatter vegetation/decorations via Geometry Nodes\n"
            "5. Moderately exaggerate proportions, round off corners\n"
            "6. Consider adding outlines (blender_outline_effect)"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Smooth Shading",
            "Texture Filtering": "Linear",
            "Recommended Poly Count": "2K-10K faces",
            "Texture Resolution": "128-512",
        },
    },
    "TOON": {
        "render_engine": get_eevee_engine(),
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Standard",
        "film_transparent": False,
        "samples": 64,
        "tips": (
            "Toon/Cel-shading style modeling tips:\n"
            "1. Use Shader to RGB + ColorRamp(Constant) for Cel Shading\n"
            "2. Must add outlines: blender_outline_effect(method=SOLIDIFY)\n"
            "3. Split shadows into 2-3 layers: light/dark/darkest\n"
            "4. Use sharp ColorRamp bands for highlights\n"
            "5. Rim light (Fresnel) to enhance silhouette\n"
            "6. Materials: Use blender_create_toon_material or blender_procedural_material"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Smooth Shading + Cel Shading",
            "Outline": "Recommended: Solidify with flipped normals",
            "Recommended Poly Count": "3K-15K faces",
            "Texture Resolution": "512-1K",
        },
    },
    "HAND_PAINTED": {
        "render_engine": get_eevee_engine(),
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Standard",
        "film_transparent": False,
        "samples": 64,
        "tips": (
            "Hand-painted style modeling tips:\n"
            "1. UV unwrap quality is critical! Use Smart UV Project + manual adjustments\n"
            "2. Materials: Diffuse (Base Color) only, no PBR data channels\n"
            "3. Texture painting: First bake AO to texture as a darkening base\n"
            "4. Paint shadows/highlights directly onto the Diffuse texture\n"
            "5. Low-saturation shadows + high-saturation highlights\n"
            "6. Use the blender_texture_paint tool suite"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Smooth Shading",
            "Material Mode": "Diffuse Only (No PBR)",
            "Recommended Poly Count": "5K-30K faces",
            "Texture Resolution": "1K-2K",
        },
    },
    "SEMI_REALISTIC": {
        "render_engine": get_eevee_engine(),
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Filmic",
        "film_transparent": False,
        "samples": 128,
        "tips": (
            "Semi-realistic style modeling tips:\n"
            "1. Use Subdivision Surface level=2 + support loops/crease edges\n"
            "2. Good quad-dominant topology\n"
            "3. Materials: Simplified PBR (Base Color + Normal + Roughness)\n"
            "4. Normal maps: Bake from high poly or use procedural bump\n"
            "5. Auto Smooth angle 30°~45°\n"
            "6. Use blender_bake_maps to bake normals/AO"
        ),
        "settings_applied": {
            "Render Engine": "EEVEE",
            "Shading": "Smooth + Auto Smooth",
            "Color Management": "Filmic",
            "Recommended Poly Count": "10K-50K faces",
            "Texture Resolution": "1K-2K",
        },
    },
    "PBR_REALISTIC": {
        "render_engine": "CYCLES",
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Filmic",
        "film_transparent": False,
        "samples": 256,
        "tips": (
            "PBR Realistic style modeling tips:\n"
            "1. Sculpt high poly → Retopologize low poly → Bake normals\n"
            "2. Full PBR: BaseColor/Normal/Roughness/Metallic/AO/Displacement\n"
            "3. Use blender_procedural_material for procedural PBR presets\n"
            "4. Add wear effects: edge_wear via Pointiness/Curvature\n"
            "5. Use blender_bake_maps to bake a full texture set\n"
            "6. LOD: Use blender_lod_generate to create multi-level detail"
        ),
        "settings_applied": {
            "Render Engine": "Cycles",
            "Shading": "Smooth + Auto Smooth",
            "Color Management": "Filmic",
            "Recommended Poly Count": "30K-100K faces",
            "Texture Resolution": "2K-4K",
        },
    },
    "AAA": {
        "render_engine": "CYCLES",
        "shading": "SMOOTH",
        "texture_filter": "Linear",
        "color_management": "Filmic",
        "film_transparent": False,
        "samples": 512,
        "tips": (
            "AAA/Cinematic modeling tips:\n"
            "1. High-precision sculpting (Multires) → QuadriFlow retopology\n"
            "2. UDIM multi-tile UV (for ultra-high resolution)\n"
            "3. Full PBR texture set + Displacement\n"
            "4. Skin: SSS subsurface scattering + pore details\n"
            "5. Hair: Hair Curves system\n"
            "6. Eyes/Teeth: Specialized materials\n"
            "7. Cloth: Physics simulation baking\n"
            "8. Use blender_bake_maps to bake full high→low texture set"
        ),
        "settings_applied": {
            "Render Engine": "Cycles",
            "Shading": "Smooth + Adaptive Subdivision",
            "Color Management": "Filmic",
            "Recommended Poly Count": "100K-10M faces (sculpting)",
            "Texture Resolution": "4K-8K + UDIM",
        },
    },
}


def handle_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Set up style environment"""
    style = params.get("style", "LOW_POLY")
    apply_to_scene = params.get("apply_to_scene", True)
    apply_to_objects = params.get("apply_to_objects", [])

    config = STYLE_CONFIGS.get(style)
    if not config:
        return {
            "success": False,
            "error": {"code": "UNKNOWN_STYLE", "message": f"Unknown style: {style}"},
        }

    scene = bpy.context.scene
    extra_applied = []

    if apply_to_scene:
        # Set render engine
        try:
            scene.render.engine = config["render_engine"]
        except Exception:
            if "EEVEE" in config["render_engine"]:
                with contextlib.suppress(Exception):
                    scene.render.engine = get_eevee_engine()

        # Set samples
        if hasattr(scene, "eevee") and "EEVEE" in scene.render.engine:
            scene.eevee.taa_render_samples = config["samples"]
        elif scene.render.engine == "CYCLES":
            scene.cycles.samples = config["samples"]
            # Cycles denoising
            if style in ("PBR_REALISTIC", "AAA", "SEMI_REALISTIC"):
                scene.cycles.use_denoising = True
                with contextlib.suppress(Exception):
                    scene.cycles.denoiser = "OPENIMAGEDENOISE"
                extra_applied.append("Denoising: OpenImageDenoise")

        # Color management
        scene.view_settings.view_transform = config.get("color_management", "Standard")

        # EEVEE features (Bloom/AO/SSR)
        if hasattr(scene, "eevee") and "EEVEE" in scene.render.engine:
            eevee = scene.eevee
            if style in ("STYLIZED", "TOON"):
                # Stylized/Toon: Optional Bloom, disable AO
                if hasattr(eevee, "use_bloom"):
                    eevee.use_bloom = True
                    eevee.bloom_threshold = 0.8
                    eevee.bloom_intensity = 0.1
                    extra_applied.append("Bloom: Enabled (low intensity)")
                if hasattr(eevee, "use_gtao"):
                    eevee.use_gtao = False
                    extra_applied.append("AO: Disabled (preserve Cel style)")
            elif style in ("SEMI_REALISTIC",):
                if hasattr(eevee, "use_gtao"):
                    eevee.use_gtao = True
                    extra_applied.append("AO: Enabled")
                if hasattr(eevee, "use_ssr"):
                    eevee.use_ssr = True
                    extra_applied.append("Screen Space Reflections: Enabled")
            elif style in ("PIXEL", "LOW_POLY"):
                if hasattr(eevee, "use_bloom"):
                    eevee.use_bloom = False
                if hasattr(eevee, "use_gtao"):
                    eevee.use_gtao = False
                if hasattr(eevee, "use_ssr"):
                    eevee.use_ssr = False

        # Pixel style: Set active camera to orthographic
        if style == "PIXEL":
            cam = scene.camera
            if cam and cam.type == "CAMERA":
                cam.data.type = "ORTHO"
                cam.data.ortho_scale = 10.0
                extra_applied.append("Camera: Orthographic projection")

        # Transparent film
        scene.render.film_transparent = config.get("film_transparent", False)

    # Apply shading and texture settings to specified objects
    for obj_name in apply_to_objects:
        obj = bpy.data.objects.get(obj_name)
        if obj and obj.type == "MESH":
            # Shading mode
            if config["shading"] == "FLAT":
                for poly in obj.data.polygons:
                    poly.use_smooth = False
            else:
                for poly in obj.data.polygons:
                    poly.use_smooth = True

            # Pixel style: Set existing material texture interpolation to Closest
            if style == "PIXEL" and obj.data.materials:
                for mat in obj.data.materials:
                    if mat and mat.use_nodes:
                        for node in mat.node_tree.nodes:
                            if node.type == "TEX_IMAGE":
                                node.interpolation = "Closest"
                extra_applied.append(f"{obj_name}: Texture interpolation -> Closest")

    return {
        "success": True,
        "data": {
            "style": style,
            "tips": config["tips"],
            "settings_applied": config["settings_applied"],
            "extra_applied": extra_applied,
        },
    }


def handle_outline(params: dict[str, Any]) -> dict[str, Any]:
    """Add outline effect"""
    object_name = params.get("object_name", "")
    method = params.get("method", "SOLIDIFY")
    thickness = params.get("thickness", 0.02)
    color = params.get("color", [0, 0, 0])

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object does not exist or is not a mesh: {object_name}",
            },
        }

    try:
        if method == "SOLIDIFY":
            # Create outline material
            outline_mat_name = f"{object_name}_Outline"
            outline_mat = bpy.data.materials.get(outline_mat_name)
            if not outline_mat:
                outline_mat = bpy.data.materials.new(name=outline_mat_name)
                outline_mat.use_nodes = True
                outline_mat.use_backface_culling = True
                # Set to solid color
                nodes = outline_mat.node_tree.nodes
                bsdf = None
                for node in nodes:
                    if node.type == "BSDF_PRINCIPLED":
                        bsdf = node
                        break
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = (*color[:3], 1.0)
                    if "Emission Color" in bsdf.inputs:
                        bsdf.inputs["Emission Color"].default_value = (*color[:3], 1.0)
                    elif "Emission" in bsdf.inputs:
                        bsdf.inputs["Emission"].default_value = (*color[:3], 1.0)

            # Add to material slot
            if outline_mat_name not in [
                ms.material.name for ms in obj.material_slots if ms.material
            ]:
                obj.data.materials.append(outline_mat)

            outline_slot = len(obj.material_slots) - 1

            # Add Solidify modifier
            mod = obj.modifiers.new(name="Outline", type="SOLIDIFY")
            mod.thickness = -thickness  # Negative value = outward
            mod.use_flip_normals = True
            mod.use_rim = False
            mod.material_offset = outline_slot
            mod.offset = 1.0  # Outward only

        elif method == "FREESTYLE":
            scene = bpy.context.scene
            # Enable Freestyle
            scene.render.use_freestyle = True
            # Configure Freestyle lines
            view_layer = bpy.context.view_layer
            if hasattr(view_layer, "freestyle_settings"):
                fs = view_layer.freestyle_settings
                ls = fs.linesets.new("OutlineSet") if len(fs.linesets) == 0 else fs.linesets[0]
                ls.linestyle.thickness = thickness * 100  # Freestyle uses pixel units
                ls.linestyle.color = color[:3] if len(color) >= 3 else (0, 0, 0)

        elif method == "GREASE_PENCIL":
            # Use Line Art modifier (Blender 3.0+)
            bpy.ops.object.gpencil_add(type="LRT_COLLECTION")
            gp_obj = bpy.context.active_object
            if gp_obj and gp_obj.type == "GPENCIL":
                gp_obj.name = f"{object_name}_LineArt"
                # Configure Line Art modifier
                for mod in gp_obj.grease_pencil_modifiers:
                    if mod.type == "GP_LINEART":
                        mod.source_type = "OBJECT"
                        mod.source_object = obj
                        mod.thickness = int(thickness * 100)
                        break

        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_METHOD", "message": f"Unknown outline method: {method}"},
            }

    except Exception as e:
        return {"success": False, "error": {"code": "OUTLINE_FAILED", "message": str(e)}}

    return {"success": True, "data": {"method": method, "thickness": thickness}}


def handle_bake_maps(params: dict[str, Any]) -> dict[str, Any]:
    """Bake maps (high poly → low poly)"""
    high_poly_name = params.get("high_poly", "")
    low_poly_name = params.get("low_poly", "")
    maps = params.get("maps", ["NORMAL", "AO"])
    resolution = params.get("resolution", 2048)
    cage_extrusion = params.get("cage_extrusion", 0.1)
    output_dir = params.get("output_dir")
    margin = params.get("margin", 16)

    high_obj = bpy.data.objects.get(high_poly_name)
    low_obj = bpy.data.objects.get(low_poly_name)

    if not high_obj or high_obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"High poly does not exist or is not a mesh: {high_poly_name}",
            },
        }
    if not low_obj or low_obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Low poly does not exist or is not a mesh: {low_poly_name}",
            },
        }

    # Switch to Cycles (required for baking)
    scene = bpy.context.scene
    original_engine = scene.render.engine
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64

    # Determine output directory
    if not output_dir:
        blend_path = bpy.data.filepath
        output_dir = os.path.dirname(blend_path) if blend_path else os.path.expanduser("~")

    baked_maps = []

    try:
        # Ensure low poly has a material
        if len(low_obj.data.materials) == 0:
            mat = bpy.data.materials.new(name=f"{low_poly_name}_BakeMat")
            mat.use_nodes = True
            low_obj.data.materials.append(mat)

        mat = low_obj.data.materials[0]
        if not mat.use_nodes:
            mat.use_nodes = True

        nodes = mat.node_tree.nodes

        for map_type in maps:
            # Create image for baking
            img_name = f"{low_poly_name}_{map_type}"
            img = bpy.data.images.get(img_name)
            if img:
                bpy.data.images.remove(img)

            is_data = map_type != "DIFFUSE"
            img = bpy.data.images.new(
                name=img_name,
                width=resolution,
                height=resolution,
                alpha=False,
                float_buffer=is_data,
            )
            if is_data:
                img.colorspace_settings.name = "Non-Color"

            # Create image texture node
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.image = img
            tex_node.name = f"Bake_{map_type}"
            tex_node.label = f"Bake {map_type}"

            # Set this node as active
            for n in nodes:
                n.select = False
            tex_node.select = True
            nodes.active = tex_node

            # Set bake parameters
            scene.render.bake.use_selected_to_active = True
            scene.render.bake.cage_extrusion = cage_extrusion
            scene.render.bake.margin = margin

            # Select objects
            bpy.ops.object.select_all(action="DESELECT")
            high_obj.select_set(True)
            low_obj.select_set(True)
            bpy.context.view_layer.objects.active = low_obj

            # Execute bake
            bake_type_map = {
                "NORMAL": "NORMAL",
                "AO": "AO",
                "DIFFUSE": "DIFFUSE",
                "ROUGHNESS": "ROUGHNESS",
                "COMBINED": "COMBINED",
                "CURVATURE": "NORMAL",  # Curvature via post-processing
            }
            blender_bake_type = bake_type_map.get(map_type, "NORMAL")

            if map_type == "DIFFUSE":
                scene.render.bake.use_pass_direct = False
                scene.render.bake.use_pass_indirect = False
                scene.render.bake.use_pass_color = True

            bpy.ops.object.bake(type=blender_bake_type)

            # Save image
            output_path = os.path.join(output_dir, f"{img_name}.png")
            img.filepath_raw = output_path
            img.file_format = "PNG"
            img.save()

            baked_maps.append({"type": map_type, "path": output_path, "resolution": resolution})

            # Clean up nodes
            nodes.remove(tex_node)

    except Exception as e:
        scene.render.engine = original_engine
        return {"success": False, "error": {"code": "BAKE_FAILED", "message": str(e)}}

    # Restore render engine
    scene.render.engine = original_engine

    return {"success": True, "data": {"baked_maps": baked_maps}}
