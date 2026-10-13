"""
Curve Modeling Handler

Handles curve creation, editing, conversion, and related commands.
"""

import math
from typing import Any

import bpy


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create curve"""
    curve_type = params.get("curve_type", "BEZIER")
    name = params.get("name", "Curve")
    points = params.get("points", [])
    cyclic = params.get("cyclic", False)
    location = params.get("location", [0, 0, 0])

    # Generate sensible default points if none provided
    if not points or len(points) < 2:
        default_points = {
            "BEZIER": [[0, 0, 0], [1, 0, 0]],
            "NURBS": [[0, 0, 0], [0.5, 0.5, 0], [1, 0, 0]],
            "POLY": [[0, 0, 0], [1, 0, 0]],
        }
        points = default_points.get(curve_type, [[0, 0, 0], [1, 0, 0]])

    # Create curve data
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"

    # Create spline
    if curve_type == "BEZIER":
        spline = curve_data.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)

        for i, point in enumerate(points):
            bp = spline.bezier_points[i]
            bp.co = point
            bp.handle_left_type = "AUTO"
            bp.handle_right_type = "AUTO"

    elif curve_type == "NURBS":
        spline = curve_data.splines.new("NURBS")
        spline.points.add(len(points) - 1)

        for i, point in enumerate(points):
            spline.points[i].co = point + [1.0]  # NURBS requires weight

        spline.use_endpoint_u = True

    else:  # POLY
        spline = curve_data.splines.new("POLY")
        spline.points.add(len(points) - 1)

        for i, point in enumerate(points):
            spline.points[i].co = point + [1.0]

    spline.use_cyclic_u = cyclic

    # Create object
    curve_obj = bpy.data.objects.new(name, curve_data)
    curve_obj.location = location
    bpy.context.collection.objects.link(curve_obj)

    return {"success": True, "data": {"curve_name": curve_obj.name, "points_count": len(points)}}


def handle_circle(params: dict[str, Any]) -> dict[str, Any]:
    """Create circle curve"""
    name = params.get("name", "Circle")
    radius = params.get("radius", 1.0)
    location = params.get("location", [0, 0, 0])
    fill_mode = params.get("fill_mode", "FULL")

    bpy.ops.curve.primitive_bezier_circle_add(radius=radius, location=location)
    curve_obj = bpy.context.active_object
    curve_obj.name = name

    # Set fill mode (FULL, BACK, FRONT, HALF)
    if fill_mode in ("FULL", "BACK", "FRONT", "HALF"):
        curve_obj.data.fill_mode = fill_mode

    return {"success": True, "data": {"curve_name": curve_obj.name}}


def handle_path(params: dict[str, Any]) -> dict[str, Any]:
    """Create path curve"""
    name = params.get("name", "Path")
    length = params.get("length", 4.0)
    points_count = params.get("points_count", 5)
    location = params.get("location", [0, 0, 0])

    # Create curve data
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.use_path = True

    # Create NURBS spline
    spline = curve_data.splines.new("NURBS")
    spline.points.add(points_count - 1)

    # Set point positions
    step = length / (points_count - 1)
    for i in range(points_count):
        x = -length / 2 + i * step
        spline.points[i].co = [x, 0, 0, 1]

    spline.use_endpoint_u = True

    # Create object
    curve_obj = bpy.data.objects.new(name, curve_data)
    curve_obj.location = location
    bpy.context.collection.objects.link(curve_obj)

    return {"success": True, "data": {"curve_name": curve_obj.name}}


def handle_spiral(params: dict[str, Any]) -> dict[str, Any]:
    """Create spiral curve"""
    name = params.get("name", "Spiral")
    turns = params.get("turns", 2.0)
    radius = params.get("radius", 1.0)
    height = params.get("height", 2.0)
    location = params.get("location", [0, 0, 0])

    # Create curve data
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"

    # Create spline
    points_per_turn = 16
    total_points = int(turns * points_per_turn)

    spline = curve_data.splines.new("POLY")
    spline.points.add(total_points - 1)

    for i in range(total_points):
        t = i / total_points
        angle = t * turns * 2 * math.pi
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = t * height
        spline.points[i].co = [x, y, z, 1]

    # Create object
    curve_obj = bpy.data.objects.new(name, curve_data)
    curve_obj.location = location
    bpy.context.collection.objects.link(curve_obj)

    return {"success": True, "data": {"curve_name": curve_obj.name}}


def handle_to_mesh(params: dict[str, Any]) -> dict[str, Any]:
    """Convert curve to mesh"""
    curve_name = params.get("curve_name", "")
    resolution = params.get("resolution", 12)
    keep_original = params.get("keep_original", False)

    curve_obj = bpy.data.objects.get(curve_name)
    if not curve_obj or curve_obj.type != "CURVE":
        return {
            "success": False,
            "error": {"code": "CURVE_NOT_FOUND", "message": f"Curve not found: {curve_name}"},
        }

    # Set resolution
    curve_obj.data.resolution_u = resolution

    # Select curve
    bpy.ops.object.select_all(action="DESELECT")
    curve_obj.select_set(True)
    bpy.context.view_layer.objects.active = curve_obj

    # Convert to mesh
    bpy.ops.object.convert(target="MESH", keep_original=keep_original)

    mesh_obj = bpy.context.active_object

    return {"success": True, "data": {"mesh_name": mesh_obj.name}}


def handle_extrude(params: dict[str, Any]) -> dict[str, Any]:
    """Curve extrude settings"""
    curve_name = params.get("curve_name", "")
    depth = params.get("depth", 0.1)
    bevel_depth = params.get("bevel_depth", 0.0)
    bevel_resolution = params.get("bevel_resolution", 0)

    curve_obj = bpy.data.objects.get(curve_name)
    if not curve_obj or curve_obj.type != "CURVE":
        return {
            "success": False,
            "error": {"code": "CURVE_NOT_FOUND", "message": f"Curve not found: {curve_name}"},
        }

    curve_data = curve_obj.data
    curve_data.extrude = depth
    curve_data.bevel_depth = bevel_depth
    curve_data.bevel_resolution = bevel_resolution

    return {"success": True, "data": {}}


def handle_text(params: dict[str, Any]) -> dict[str, Any]:
    """Create text"""
    text = params.get("text", "Text")
    name = params.get("name", "Text")
    font_size = params.get("font_size", 1.0)
    extrude = params.get("extrude", 0.0)
    location = params.get("location", [0, 0, 0])

    # Create text object
    bpy.ops.object.text_add(location=location)
    text_obj = bpy.context.active_object
    text_obj.name = name

    # Set text content
    text_obj.data.body = text
    text_obj.data.size = font_size
    text_obj.data.extrude = extrude

    # Center alignment
    text_obj.data.align_x = "CENTER"
    text_obj.data.align_y = "CENTER"

    return {"success": True, "data": {"text_name": text_obj.name}}
