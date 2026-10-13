"""
AI assistance handler

Handles AI assistance feature commands.
"""

from typing import Any

import bpy


def handle_describe_scene(params: dict[str, Any]) -> dict[str, Any]:
    """Describe scene"""
    detail_level = params.get("detail_level", "medium")
    include_materials = params.get("include_materials", True)
    include_animations = params.get("include_animations", True)

    try:
        scene = bpy.context.scene

        description = {
            "name": scene.name,
            "frame_range": [scene.frame_start, scene.frame_end],
            "current_frame": scene.frame_current,
            "render_engine": scene.render.engine,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        }

        # Object statistics
        objects = {"total": len(scene.objects), "by_type": {}}

        for obj in scene.objects:
            obj_type = obj.type
            if obj_type not in objects["by_type"]:
                objects["by_type"][obj_type] = 0
            objects["by_type"][obj_type] += 1

        description["objects"] = objects

        # Detailed information
        if detail_level in ["medium", "high"]:
            object_list = []
            for obj in scene.objects:
                obj_info = {
                    "name": obj.name,
                    "type": obj.type,
                    "location": list(obj.location),
                    "visible": obj.visible_get(),
                }

                if detail_level == "high":
                    obj_info["rotation"] = list(obj.rotation_euler)
                    obj_info["scale"] = list(obj.scale)

                    if obj.type == "MESH":
                        mesh = obj.data
                        obj_info["vertices"] = len(mesh.vertices)
                        obj_info["faces"] = len(mesh.polygons)
                        obj_info["edges"] = len(mesh.edges)

                object_list.append(obj_info)

            description["object_list"] = object_list

        # Material information
        if include_materials:
            materials = []
            for mat in bpy.data.materials:
                mat_info = {"name": mat.name, "use_nodes": mat.use_nodes}
                if mat.use_nodes and mat.node_tree:
                    mat_info["node_count"] = len(mat.node_tree.nodes)
                materials.append(mat_info)

            description["materials"] = {
                "count": len(materials),
                "list": materials[:20] if detail_level != "high" else materials,
            }

        # Animation information
        if include_animations:
            animations = []
            for action in bpy.data.actions:
                anim_info = {"name": action.name, "frame_range": list(action.frame_range)}
                if detail_level == "high" and hasattr(action, "fcurves"):
                    anim_info["fcurve_count"] = len(action.fcurves)
                animations.append(anim_info)

            description["animations"] = {"count": len(animations), "list": animations}

        # World settings
        if scene.world:
            description["world"] = {"name": scene.world.name, "use_nodes": scene.world.use_nodes}

        return {"success": True, "data": description}

    except Exception as e:
        return {"success": False, "error": {"code": "DESCRIBE_ERROR", "message": str(e)}}


def handle_analyze_object(params: dict[str, Any]) -> dict[str, Any]:
    """Analyze object"""
    object_name = params.get("object_name", "")
    include_modifiers = params.get("include_modifiers", True)
    include_topology = params.get("include_topology", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        analysis = {
            "name": obj.name,
            "type": obj.type,
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
            "dimensions": list(obj.dimensions),
            "visible": obj.visible_get(),
            "parent": obj.parent.name if obj.parent else None,
        }

        # Mesh topology analysis
        if obj.type == "MESH" and include_topology:
            mesh = obj.data

            analysis["topology"] = {
                "vertices": len(mesh.vertices),
                "edges": len(mesh.edges),
                "faces": len(mesh.polygons),
                "triangles": sum(len(p.vertices) - 2 for p in mesh.polygons),
                "has_custom_normals": mesh.has_custom_normals,
                "uv_layers": len(mesh.uv_layers),
                "vertex_colors": len(mesh.vertex_colors) if hasattr(mesh, "vertex_colors") else 0,
            }

            # Analyze face types
            ngons = 0
            quads = 0
            tris = 0
            for poly in mesh.polygons:
                if len(poly.vertices) > 4:
                    ngons += 1
                elif len(poly.vertices) == 4:
                    quads += 1
                else:
                    tris += 1

            analysis["topology"]["face_types"] = {"triangles": tris, "quads": quads, "ngons": ngons}

        # Modifier analysis
        if include_modifiers:
            modifiers = []
            for mod in obj.modifiers:
                mod_info = {
                    "name": mod.name,
                    "type": mod.type,
                    "show_viewport": mod.show_viewport,
                    "show_render": mod.show_render,
                }
                modifiers.append(mod_info)

            analysis["modifiers"] = modifiers

        # Materials
        if obj.data and hasattr(obj.data, "materials"):
            analysis["materials"] = [mat.name if mat else None for mat in obj.data.materials]

        # Constraints
        if obj.constraints:
            analysis["constraints"] = [{"name": c.name, "type": c.type} for c in obj.constraints]

        # Animation data
        if obj.animation_data:
            analysis["animation"] = {
                "action": obj.animation_data.action.name if obj.animation_data.action else None,
                "nla_tracks": len(obj.animation_data.nla_tracks),
            }

        return {"success": True, "data": analysis}

    except Exception as e:
        return {"success": False, "error": {"code": "ANALYZE_ERROR", "message": str(e)}}


def handle_suggest_optimization(params: dict[str, Any]) -> dict[str, Any]:
    """Optimization suggestions"""
    target = params.get("target", "performance")

    try:
        suggestions = []

        scene = bpy.context.scene

        # Check for high-poly objects
        high_poly_objects = []
        for obj in scene.objects:
            if obj.type == "MESH":
                face_count = len(obj.data.polygons)
                if face_count > 100000:
                    high_poly_objects.append({"name": obj.name, "faces": face_count})

        if high_poly_objects:
            suggestions.append(
                {
                    "type": "HIGH_POLY",
                    "severity": "warning",
                    "message": f"Found {len(high_poly_objects)} high-poly objects",
                    "suggestion": "Consider using subdivision modifiers or decimation tools",
                    "objects": high_poly_objects[:5],
                }
            )

        # Check for unapplied transforms
        unapplied_transforms = []
        for obj in scene.objects:
            if obj.type == "MESH" and list(obj.scale) != [1, 1, 1]:
                unapplied_transforms.append(obj.name)

        if unapplied_transforms:
            suggestions.append(
                {
                    "type": "UNAPPLIED_SCALE",
                    "severity": "info",
                    "message": f"Found {len(unapplied_transforms)} objects with unapplied scale",
                    "suggestion": "Apply scale to avoid export issues",
                    "objects": unapplied_transforms[:10],
                }
            )

        # Check materials
        unused_materials = []
        for mat in bpy.data.materials:
            if mat.users == 0:
                unused_materials.append(mat.name)

        if unused_materials:
            suggestions.append(
                {
                    "type": "UNUSED_MATERIALS",
                    "severity": "info" if target != "memory" else "warning",
                    "message": f"Found {len(unused_materials)} unused materials",
                    "suggestion": "Remove unused materials to reduce memory usage",
                    "items": unused_materials[:10],
                }
            )

        # Check texture sizes
        large_textures = []
        for img in bpy.data.images:
            if img.size[0] * img.size[1] > 4096 * 4096:
                large_textures.append({"name": img.name, "size": list(img.size)})

        if large_textures:
            suggestions.append(
                {
                    "type": "LARGE_TEXTURES",
                    "severity": "warning" if target in ["performance", "memory"] else "info",
                    "message": f"Found {len(large_textures)} oversized textures",
                    "suggestion": "Consider reducing texture resolution",
                    "textures": large_textures,
                }
            )

        # Render settings suggestions
        if target == "performance" and scene.render.engine == "CYCLES":
            suggestions.append(
                {
                    "type": "RENDER_ENGINE",
                    "severity": "info",
                    "message": "Currently using Cycles render engine",
                    "suggestion": "For real-time preview, consider using EEVEE",
                }
            )

        return {
            "success": True,
            "data": {"target": target, "suggestions": suggestions, "count": len(suggestions)},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "SUGGEST_ERROR", "message": str(e)}}


def handle_auto_material(params: dict[str, Any]) -> dict[str, Any]:
    """Auto material"""
    object_name = params.get("object_name", "")
    description = params.get("description", "")
    style = params.get("style", "realistic")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Create material based on description
        mat = bpy.data.materials.new(name=f"{object_name}_{description[:20]}")
        mat.use_nodes = True

        nodes = mat.node_tree.nodes
        links = mat.node_tree.links

        # Clear default nodes
        nodes.clear()

        # Create output node
        output = nodes.new("ShaderNodeOutputMaterial")
        output.location = (300, 0)

        # Create BSDF node
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.location = (0, 0)

        # Set parameters based on description
        desc_lower = description.lower()

        # Metal materials
        if any(
            word in desc_lower for word in ["metal", "steel", "iron", "gold", "silver", "copper"]
        ):
            bsdf.inputs["Metallic"].default_value = 1.0
            bsdf.inputs["Roughness"].default_value = 0.3

            if "gold" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (1.0, 0.766, 0.336, 1.0)
            elif "silver" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (0.972, 0.960, 0.915, 1.0)
            elif "copper" in desc_lower:
                bsdf.inputs["Base Color"].default_value = (0.955, 0.637, 0.538, 1.0)
            else:
                bsdf.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)

        # Wood
        elif any(word in desc_lower for word in ["wood", "wooden"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.7
            bsdf.inputs["Base Color"].default_value = (0.4, 0.2, 0.1, 1.0)

        # Glass
        elif any(word in desc_lower for word in ["glass", "transparent"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.0
            bsdf.inputs["Transmission"].default_value = 1.0
            bsdf.inputs["IOR"].default_value = 1.45

        # Plastic
        elif any(word in desc_lower for word in ["plastic"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.4
            bsdf.inputs["Specular IOR Level"].default_value = 0.5

        # Fabric
        elif any(word in desc_lower for word in ["fabric", "cloth", "cotton"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.9
            bsdf.inputs["Sheen Weight"].default_value = 0.3

        # Skin
        elif any(word in desc_lower for word in ["skin"]):
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.5
            bsdf.inputs["Subsurface Weight"].default_value = 0.3
            bsdf.inputs["Base Color"].default_value = (0.8, 0.6, 0.5, 1.0)

        # Default
        else:
            bsdf.inputs["Metallic"].default_value = 0.0
            bsdf.inputs["Roughness"].default_value = 0.5

        # Style adjustments
        if style == "cartoon":
            bsdf.inputs["Roughness"].default_value = 1.0
        elif style == "stylized":
            bsdf.inputs["Roughness"].default_value = 0.7

        # Connect nodes
        links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

        # Apply material
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)

        return {
            "success": True,
            "data": {"material_name": mat.name, "description": description, "style": style},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "AUTO_MATERIAL_ERROR", "message": str(e)}}


def handle_scene_statistics(params: dict[str, Any]) -> dict[str, Any]:
    """Scene statistics"""
    include_hidden = params.get("include_hidden", False)

    try:
        scene = bpy.context.scene

        stats = {
            "scene_name": scene.name,
            "objects": {"total": 0, "visible": 0, "by_type": {}},
            "geometry": {
                "total_vertices": 0,
                "total_edges": 0,
                "total_faces": 0,
                "total_triangles": 0,
            },
            "materials": {"total": len(bpy.data.materials), "used": 0},
            "textures": {"total": len(bpy.data.images), "memory_estimate_mb": 0},
            "animations": {"actions": len(bpy.data.actions), "total_keyframes": 0},
        }

        # Object statistics
        for obj in scene.objects:
            if not include_hidden and not obj.visible_get():
                continue

            stats["objects"]["total"] += 1
            if obj.visible_get():
                stats["objects"]["visible"] += 1

            obj_type = obj.type
            if obj_type not in stats["objects"]["by_type"]:
                stats["objects"]["by_type"][obj_type] = 0
            stats["objects"]["by_type"][obj_type] += 1

            # Mesh statistics
            if obj.type == "MESH":
                mesh = obj.data
                stats["geometry"]["total_vertices"] += len(mesh.vertices)
                stats["geometry"]["total_edges"] += len(mesh.edges)
                stats["geometry"]["total_faces"] += len(mesh.polygons)
                stats["geometry"]["total_triangles"] += sum(
                    len(p.vertices) - 2 for p in mesh.polygons
                )

        # Material statistics
        for mat in bpy.data.materials:
            if mat.users > 0:
                stats["materials"]["used"] += 1

        # Texture memory estimation
        for img in bpy.data.images:
            if img.size[0] > 0 and img.size[1] > 0:
                # Estimate: RGBA 4 bytes per pixel
                memory_bytes = img.size[0] * img.size[1] * 4
                stats["textures"]["memory_estimate_mb"] += memory_bytes / (1024 * 1024)

        stats["textures"]["memory_estimate_mb"] = round(stats["textures"]["memory_estimate_mb"], 2)

        # Animation statistics
        for action in bpy.data.actions:
            if hasattr(action, "fcurves"):
                for fcurve in action.fcurves:
                    stats["animations"]["total_keyframes"] += len(fcurve.keyframe_points)

        return {"success": True, "data": stats}

    except Exception as e:
        return {"success": False, "error": {"code": "STATISTICS_ERROR", "message": str(e)}}


def handle_list_issues(params: dict[str, Any]) -> dict[str, Any]:
    """Detect issues"""
    try:
        issues = []

        scene = bpy.context.scene

        # Check for non-manifold geometry
        for obj in scene.objects:
            if obj.type == "MESH":
                mesh = obj.data

                # Check for isolated vertices
                used_verts = set()
                for edge in mesh.edges:
                    used_verts.update(edge.vertices)

                isolated = len(mesh.vertices) - len(used_verts)
                if isolated > 0:
                    issues.append(
                        {
                            "type": "ISOLATED_VERTICES",
                            "severity": "warning",
                            "object": obj.name,
                            "message": f"Found {isolated} isolated vertices",
                        }
                    )

                # Check for zero-area faces
                zero_area_faces = 0
                for poly in mesh.polygons:
                    if poly.area < 0.00001:
                        zero_area_faces += 1

                if zero_area_faces > 0:
                    issues.append(
                        {
                            "type": "ZERO_AREA_FACES",
                            "severity": "warning",
                            "object": obj.name,
                            "message": f"Found {zero_area_faces} zero-area faces",
                        }
                    )

        # Check for missing textures
        for img in bpy.data.images:
            if img.source == "FILE" and img.filepath:
                import os

                filepath = bpy.path.abspath(img.filepath)
                if not os.path.exists(filepath):
                    issues.append(
                        {
                            "type": "MISSING_TEXTURE",
                            "severity": "error",
                            "image": img.name,
                            "message": f"Texture file not found: {img.filepath}",
                        }
                    )

        # Check for circular dependencies
        for obj in scene.objects:
            if obj.parent:
                parent = obj.parent
                visited = {obj.name}
                while parent:
                    if parent.name in visited:
                        issues.append(
                            {
                                "type": "CIRCULAR_PARENTING",
                                "severity": "error",
                                "object": obj.name,
                                "message": "Circular parenting detected",
                            }
                        )
                        break
                    visited.add(parent.name)
                    parent = parent.parent

        # Check for oversized objects
        for obj in scene.objects:
            max_dim = max(obj.dimensions)
            if max_dim > 1000:
                issues.append(
                    {
                        "type": "OVERSIZED_OBJECT",
                        "severity": "info",
                        "object": obj.name,
                        "message": f"Object dimensions too large: {max_dim:.1f}",
                    }
                )

        return {
            "success": True,
            "data": {
                "issues": issues,
                "total": len(issues),
                "by_severity": {
                    "error": len([i for i in issues if i["severity"] == "error"]),
                    "warning": len([i for i in issues if i["severity"] == "warning"]),
                    "info": len([i for i in issues if i["severity"] == "info"]),
                },
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "ISSUES_ERROR", "message": str(e)}}
