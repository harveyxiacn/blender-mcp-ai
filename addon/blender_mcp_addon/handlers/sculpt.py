"""
Sculpt Handler

Handles sculpting-related commands.
"""

import contextlib
from typing import Any

import bpy


def handle_mode(params: dict[str, Any]) -> dict[str, Any]:
    """Enter/exit sculpt mode"""
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
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects can be sculpted"},
        }

    try:
        # Ensure in the correct context
        # First switch to object mode (if not already)
        current_mode = bpy.context.mode
        if current_mode != "OBJECT":
            with contextlib.suppress(BaseException):
                bpy.ops.object.mode_set(mode="OBJECT")

        # Select object
        for o in bpy.context.selected_objects:
            o.select_set(False)
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Switch mode
        if enable:
            bpy.ops.object.mode_set(mode="SCULPT")
        else:
            bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "success": True,
            "data": {"mode": bpy.context.object.mode if bpy.context.object else "OBJECT"},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "MODE_ERROR", "message": str(e)}}


def handle_set_brush(params: dict[str, Any]) -> dict[str, Any]:
    """Set sculpt brush"""
    brush_type = params.get("brush_type", "DRAW")
    radius = params.get("radius", 50.0)
    strength = params.get("strength", 0.5)
    auto_smooth = params.get("auto_smooth", 0.0)

    try:
        # Get current tool settings

        # Brush type mapping
        brush_map = {
            "DRAW": "SculptDraw",
            "CLAY": "Clay",
            "CLAY_STRIPS": "Clay Strips",
            "INFLATE": "Inflate/Deflate",
            "BLOB": "Blob",
            "CREASE": "Crease",
            "SMOOTH": "Smooth",
            "FLATTEN": "Flatten/Contrast",
            "FILL": "Fill/Deepen",
            "SCRAPE": "Scrape/Peaks",
            "PINCH": "Pinch/Magnify",
            "GRAB": "Grab",
            "SNAKE_HOOK": "Snake Hook",
            "THUMB": "Thumb",
            "NUDGE": "Nudge",
            "ROTATE": "Rotate",
            "MASK": "Mask",
            "DRAW_FACE_SETS": "Draw Face Sets",
        }

        brush_name = brush_map.get(brush_type, "SculptDraw")

        # Find brush - Blender 5.0+ compatible
        brush = bpy.data.brushes.get(brush_name)
        if not brush:
            # Try to find matching brush
            for b in bpy.data.brushes:
                # Blender 5.0+ may use different properties
                tool = getattr(b, "sculpt_tool", None) or getattr(b, "brush_type", None)
                if tool == brush_type:
                    brush = b
                    break

        if not brush:
            # Create new brush
            brush = bpy.data.brushes.new(name=brush_name, mode="SCULPT")

        if brush:
            # Blender 5.0+ brush is read-only, need different approach
            # Directly set brush properties
            brush.size = int(radius)
            brush.strength = strength
            if hasattr(brush, "auto_smooth_factor"):
                brush.auto_smooth_factor = auto_smooth

        return {
            "success": True,
            "data": {
                "brush": brush.name if brush else "default",
                "radius": radius,
                "strength": strength,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "BRUSH_ERROR", "message": str(e)}}


def handle_stroke(params: dict[str, Any]) -> dict[str, Any]:
    """Execute sculpt stroke"""
    object_name = params.get("object_name", "")
    stroke_points = params.get("stroke_points", [])
    brush_type = params.get("brush_type")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Ensure in sculpt mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    if bpy.context.object.mode != "SCULPT":
        bpy.ops.object.mode_set(mode="SCULPT")

    # Set brush
    if brush_type:
        handle_set_brush({"brush_type": brush_type})

    # Note: Directly executing strokes in MCP environment is difficult
    # Using programmatic mesh modification here
    # For real strokes, use bpy.ops.sculpt.brush_stroke

    try:
        # Build stroke data
        stroke_data = []
        for point in stroke_points:
            x, y, z = point[:3]
            pressure = point[3] if len(point) > 3 else 1.0
            stroke_data.append(
                {
                    "name": "",
                    "mouse": (0, 0),
                    "mouse_event": (0, 0),
                    "x_tilt": 0,
                    "y_tilt": 0,
                    "pressure": pressure,
                    "size": 1.0,
                    "pen_flip": False,
                    "time": 0,
                    "is_start": len(stroke_data) == 0,
                    "location": (x, y, z),
                }
            )

        # Due to API limitations, using alternative approach
        # Apply deformation to mesh
        mesh = obj.data

        # Simple deformation example
        for point in stroke_points:
            x, y, z = point[:3]
            pressure = point[3] if len(point) > 3 else 1.0

            # Find nearest vertex and move it slightly
            for vert in mesh.vertices:
                world_co = obj.matrix_world @ vert.co
                dist = (
                    (world_co.x - x) ** 2 + (world_co.y - y) ** 2 + (world_co.z - z) ** 2
                ) ** 0.5

                if dist < 0.5:  # Influence radius
                    # Move along normal direction
                    normal = vert.normal
                    factor = pressure * 0.1 * (1 - dist / 0.5)
                    vert.co += normal * factor

        mesh.update()

        return {"success": True, "data": {"points_applied": len(stroke_points)}}
    except Exception as e:
        return {"success": False, "error": {"code": "STROKE_ERROR", "message": str(e)}}


def handle_remesh(params: dict[str, Any]) -> dict[str, Any]:
    """Remesh"""
    object_name = params.get("object_name", "")
    mode = params.get("mode", "VOXEL")
    voxel_size = params.get("voxel_size", 0.1)
    smooth_normals = params.get("smooth_normals", True)

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

    if mode == "VOXEL":
        # Voxel remesh
        obj.data.remesh_voxel_size = voxel_size
        obj.data.use_remesh_preserve_volume = True
        obj.data.use_remesh_fix_poles = True

        bpy.ops.object.voxel_remesh()
    else:
        # Quad remesh (using modifier)
        mod = obj.modifiers.new(name="Remesh", type="REMESH")
        mod.mode = "VOXEL"
        mod.voxel_size = voxel_size
        mod.use_smooth_shade = smooth_normals

        from blender_mcp_addon.handlers.modeling import _apply_modifier

        _apply_modifier(obj, mod.name)

    return {
        "success": True,
        "data": {"vertices": len(obj.data.vertices), "faces": len(obj.data.polygons)},
    }


def handle_multires(params: dict[str, Any]) -> dict[str, Any]:
    """Multiresolution subdivision"""
    object_name = params.get("object_name", "")
    levels = params.get("levels", 2)
    sculpt_level = params.get("sculpt_level")

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

    # Find or add multiresolution modifier
    multires = None
    for mod in obj.modifiers:
        if mod.type == "MULTIRES":
            multires = mod
            break

    if not multires:
        multires = obj.modifiers.new(name="Multires", type="MULTIRES")

    # Subdivide
    current_levels = multires.total_levels
    for _ in range(levels - current_levels):
        bpy.ops.object.multires_subdivide(modifier=multires.name, mode="CATMULL_CLARK")

    # Set sculpt level
    if sculpt_level is not None:
        multires.sculpt_levels = min(sculpt_level, multires.total_levels)
    else:
        multires.sculpt_levels = multires.total_levels

    return {
        "success": True,
        "data": {"total_levels": multires.total_levels, "sculpt_levels": multires.sculpt_levels},
    }


def handle_mask(params: dict[str, Any]) -> dict[str, Any]:
    """Mask operations"""
    object_name = params.get("object_name", "")
    action = params.get("action", "CLEAR")

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

    # Switch to sculpt mode
    if bpy.context.object.mode != "SCULPT":
        bpy.ops.object.mode_set(mode="SCULPT")

    # Execute mask operation
    action_map = {
        "CLEAR": "CLEAR",
        "INVERT": "INVERT",
        "SMOOTH": "SMOOTH",
        "EXPAND": "GROW",
        "CONTRACT": "SHRINK",
    }

    mask_action = action_map.get(action, "CLEAR")

    try:
        if mask_action == "CLEAR":
            bpy.ops.paint.mask_flood_fill(mode="VALUE", value=0)
        elif mask_action == "INVERT":
            bpy.ops.paint.mask_flood_fill(mode="INVERT")
        elif mask_action == "SMOOTH":
            bpy.ops.sculpt.mask_filter(filter_type="SMOOTH")
        elif mask_action in ["GROW", "SHRINK"]:
            bpy.ops.sculpt.mask_filter(filter_type=mask_action)
    except Exception as e:
        return {"success": False, "error": {"code": "MASK_ERROR", "message": str(e)}}

    return {"success": True, "data": {"action": action}}


def handle_symmetry(params: dict[str, Any]) -> dict[str, Any]:
    """Set symmetry"""
    use_x = params.get("use_x", True)
    use_y = params.get("use_y", False)
    use_z = params.get("use_z", False)

    sculpt = bpy.context.tool_settings.sculpt

    sculpt.use_symmetry_x = use_x
    sculpt.use_symmetry_y = use_y
    sculpt.use_symmetry_z = use_z

    return {"success": True, "data": {"use_x": use_x, "use_y": use_y, "use_z": use_z}}


def handle_dyntopo(params: dict[str, Any]) -> dict[str, Any]:
    """Dynamic topology"""
    object_name = params.get("object_name", "")
    enable = params.get("enable", True)
    detail_size = params.get("detail_size", 12.0)
    detail_type = params.get("detail_type", "RELATIVE")

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

    # Switch to sculpt mode
    if bpy.context.object.mode != "SCULPT":
        bpy.ops.object.mode_set(mode="SCULPT")

    sculpt = bpy.context.tool_settings.sculpt

    try:
        if enable:
            # Enable dynamic topology
            if not bpy.context.sculpt_object.use_dynamic_topology_sculpting:
                bpy.ops.sculpt.dynamic_topology_toggle()

            # Set detail
            sculpt.detail_size = detail_size
            sculpt.detail_type_method = detail_type
        else:
            # Disable dynamic topology
            if bpy.context.sculpt_object.use_dynamic_topology_sculpting:
                bpy.ops.sculpt.dynamic_topology_toggle()

        return {
            "success": True,
            "data": {"enabled": enable, "detail_size": detail_size, "detail_type": detail_type},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "DYNTOPO_ERROR", "message": str(e)}}
