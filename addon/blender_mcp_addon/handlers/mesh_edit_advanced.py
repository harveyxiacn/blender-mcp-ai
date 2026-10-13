"""
Advanced mesh editing handler

Handles inset, bridge, spin, knife, fill, separate, symmetrize,
edge marks, select by trait, vertex groups, vertex colors and other operations.
"""

import math
from typing import Any

import bmesh
import bpy

from .compat import ensure_object_mode


def handle_edit(params: dict[str, Any]) -> dict[str, Any]:
    """Execute advanced mesh editing operations"""
    object_name = params.get("object_name", "")
    operation = params.get("operation")
    op_params = params.get("params", {})

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object does not exist or is not a mesh: {object_name}",
            },
        }

    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    try:
        if operation == "INSET_FACES":
            bpy.ops.mesh.inset(
                thickness=op_params.get("thickness", 0.01),
                depth=op_params.get("depth", 0.0),
                use_individual=op_params.get("individual", False),
                use_boundary=op_params.get("use_boundary", True),
                use_even_offset=op_params.get("use_even_offset", True),
            )

        elif operation == "BRIDGE_EDGE_LOOPS":
            bpy.ops.mesh.bridge_edge_loops(
                number_cuts=op_params.get("segments", 1),
                twist=op_params.get("twist", 0),
                profile_shape_factor=op_params.get("blend", 1.0),
            )

        elif operation == "SPIN":
            angle = op_params.get("angle", math.pi * 2)
            steps = op_params.get("steps", 12)
            axis_str = op_params.get("axis", "Z").upper()
            axis = [0, 0, 0]
            if axis_str == "X":
                axis = [1, 0, 0]
            elif axis_str == "Y":
                axis = [0, 1, 0]
            else:
                axis = [0, 0, 1]
            center = op_params.get("center", [0, 0, 0])
            bpy.ops.mesh.spin(
                angle=angle,
                steps=steps,
                axis=axis,
                center=center,
                dupli=op_params.get("dupli", False),
            )

        elif operation == "KNIFE_CUT":
            # Knife requires interactive mode; use bisect as alternative
            # For programmatic use, we use bisect plane
            plane_co = op_params.get("plane_co", [0, 0, 0])
            plane_no = op_params.get("plane_no", [0, 0, 1])
            bpy.ops.mesh.bisect(
                plane_co=plane_co,
                plane_no=plane_no,
                clear_inner=op_params.get("clear_inner", False),
                clear_outer=op_params.get("clear_outer", False),
            )

        elif operation == "FILL":
            bpy.ops.mesh.fill(use_beauty=op_params.get("use_beauty", True))

        elif operation == "GRID_FILL":
            bpy.ops.mesh.fill_grid(
                span=op_params.get("span", 1),
                offset=op_params.get("offset", 0),
            )

        elif operation == "SEPARATE":
            mode = op_params.get("mode", "SELECTED")
            bpy.ops.mesh.separate(type=mode)

        elif operation == "SYMMETRIZE":
            direction = op_params.get("direction", "NEGATIVE_X")
            bpy.ops.mesh.symmetrize(direction=direction)

        elif operation == "POKE_FACES":
            bpy.ops.mesh.poke()

        elif operation == "TRIANGULATE":
            bpy.ops.mesh.quads_convert_to_tris(
                quad_method=op_params.get("quad_method", "BEAUTY"),
                ngon_method=op_params.get("ngon_method", "BEAUTY"),
            )

        elif operation == "TRIS_TO_QUADS":
            bpy.ops.mesh.tris_convert_to_quads(
                face_threshold=math.radians(op_params.get("max_angle", 40.0)),
            )

        elif operation == "DISSOLVE":
            use_verts = op_params.get("use_verts", False)
            if use_verts:
                bpy.ops.mesh.dissolve_verts()
            else:
                bpy.ops.mesh.dissolve_faces(
                    use_verts=op_params.get("use_face_split", False),
                )

        else:
            return {
                "success": False,
                "error": {
                    "code": "UNKNOWN_OPERATION",
                    "message": f"Unknown operation: {operation}",
                },
            }

    except Exception as e:
        ensure_object_mode()
        return {"success": False, "error": {"code": "OPERATION_FAILED", "message": str(e)}}

    ensure_object_mode()
    return {"success": True, "data": {}}


def handle_edge_mark(params: dict[str, Any]) -> dict[str, Any]:
    """Set edge marks (crease/sharp/seam/bevel_weight)"""
    object_name = params.get("object_name", "")
    mark_type = params.get("mark_type")
    value = params.get("value", 1.0)
    clear = params.get("clear", False)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object does not exist or is not a mesh: {object_name}",
            },
        }

    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    bm = bmesh.from_edit_mesh(obj.data)
    selected_edges = [e for e in bm.edges if e.select]

    if not selected_edges:
        return {"success": False, "error": {"code": "NO_SELECTION", "message": "No selected edges"}}

    actual_value = 0.0 if clear else value

    try:
        if mark_type == "CREASE":
            crease_layer = bm.edges.layers.crease.verify()
            for e in selected_edges:
                e[crease_layer] = actual_value

        elif mark_type == "SHARP":
            for e in selected_edges:
                e.smooth = actual_value == 0.0

        elif mark_type == "SEAM":
            for e in selected_edges:
                e.seam = actual_value > 0.0

        elif mark_type == "BEVEL_WEIGHT":
            bevel_layer = bm.edges.layers.bevel_weight.verify()
            for e in selected_edges:
                e[bevel_layer] = actual_value

        else:
            return {
                "success": False,
                "error": {
                    "code": "UNKNOWN_MARK_TYPE",
                    "message": f"Unknown mark type: {mark_type}",
                },
            }

        bmesh.update_edit_mesh(obj.data)

    except Exception as e:
        ensure_object_mode()
        return {"success": False, "error": {"code": "MARK_FAILED", "message": str(e)}}

    ensure_object_mode()
    return {"success": True, "data": {"marked_edges": len(selected_edges), "value": actual_value}}


def handle_select_by_trait(params: dict[str, Any]) -> dict[str, Any]:
    """Select mesh elements by trait"""
    object_name = params.get("object_name", "")
    select_mode = params.get("select_mode", "FACE")
    trait = params.get("trait")
    trait_params = params.get("params", {})

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object does not exist or is not a mesh: {object_name}",
            },
        }

    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    # Set selection mode
    mode_map = {
        "VERT": (True, False, False),
        "EDGE": (False, True, False),
        "FACE": (False, False, True),
    }
    mode_tuple = mode_map.get(select_mode, (False, False, True))
    bpy.context.tool_settings.mesh_select_mode = mode_tuple

    try:
        if trait == "ALL":
            bpy.ops.mesh.select_all(action="SELECT")
        elif trait == "NONE":
            bpy.ops.mesh.select_all(action="DESELECT")
        elif trait == "NON_MANIFOLD":
            extend = trait_params.get("extend", False)
            if not extend:
                bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold(
                use_wire=trait_params.get("use_wire", True),
                use_boundary=trait_params.get("use_boundary", True),
                use_multi_face=trait_params.get("use_multi_face", True),
                use_non_contiguous=trait_params.get("use_non_contiguous", True),
                use_verts=trait_params.get("use_verts", True),
            )
        elif trait == "LOOSE":
            extend = trait_params.get("extend", False)
            if not extend:
                bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_loose()
        elif trait == "INTERIOR_FACES":
            bpy.ops.mesh.select_interior_faces()
        elif trait == "FACE_SIDES":
            number = trait_params.get("number", 4)
            type_str = trait_params.get("type", "EQUAL")
            extend = trait_params.get("extend", False)
            bpy.ops.mesh.select_face_by_sides(
                number=number,
                type=type_str,
                extend=extend,
            )
        elif trait == "UNGROUPED":
            bpy.ops.mesh.select_ungrouped()
        elif trait == "LINKED_FLAT":
            sharpness = trait_params.get("sharpness", 0.0175)
            bpy.ops.mesh.select_linked_flat(sharpness=sharpness)
        elif trait == "SHARP_EDGES":
            sharpness = trait_params.get("sharpness", 0.523)
            bpy.ops.mesh.edges_select_sharp(sharpness=sharpness)
        elif trait == "BOUNDARY":
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.mesh.select_non_manifold(
                use_wire=False,
                use_boundary=True,
                use_multi_face=False,
                use_non_contiguous=False,
                use_verts=False,
            )
        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_TRAIT", "message": f"Unknown trait type: {trait}"},
            }
    except Exception as e:
        ensure_object_mode()
        return {"success": False, "error": {"code": "SELECT_FAILED", "message": str(e)}}

    # Count selected elements
    bm = bmesh.from_edit_mesh(obj.data)
    if select_mode == "VERT":
        count = sum(1 for v in bm.verts if v.select)
    elif select_mode == "EDGE":
        count = sum(1 for e in bm.edges if e.select)
    else:
        count = sum(1 for f in bm.faces if f.select)

    ensure_object_mode()
    return {"success": True, "data": {"selected_count": count}}


def handle_vertex_group(params: dict[str, Any]) -> dict[str, Any]:
    """Vertex group operations"""
    object_name = params.get("object_name", "")
    action = params.get("action")
    group_name = params.get("group_name", "Group")
    weight = params.get("weight", 1.0)
    vertex_indices = params.get("vertex_indices")

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
        if action == "CREATE":
            vg = obj.vertex_groups.new(name=group_name)
            if vertex_indices:
                vg.add(vertex_indices, weight, "REPLACE")
            return {"success": True, "data": {"group_name": vg.name, "group_index": vg.index}}

        vg = obj.vertex_groups.get(group_name)
        if not vg:
            return {
                "success": False,
                "error": {
                    "code": "GROUP_NOT_FOUND",
                    "message": f"Vertex group not found: {group_name}",
                },
            }

        if action == "ASSIGN":
            if vertex_indices:
                vg.add(vertex_indices, weight, "REPLACE")
            else:
                # Use selection from edit mode
                bpy.context.view_layer.objects.active = obj
                if bpy.context.mode != "EDIT_MESH":
                    bpy.ops.object.mode_set(mode="EDIT")
                bm = bmesh.from_edit_mesh(obj.data)
                indices = [v.index for v in bm.verts if v.select]
                bpy.ops.object.mode_set(mode="OBJECT")
                vg.add(indices, weight, "REPLACE")

        elif action == "REMOVE":
            obj.vertex_groups.remove(vg)

        elif action == "SELECT":
            bpy.context.view_layer.objects.active = obj
            if bpy.context.mode != "EDIT_MESH":
                bpy.ops.object.mode_set(mode="EDIT")
            obj.vertex_groups.active = vg
            bpy.ops.object.vertex_group_select()

        elif action == "DESELECT":
            bpy.context.view_layer.objects.active = obj
            if bpy.context.mode != "EDIT_MESH":
                bpy.ops.object.mode_set(mode="EDIT")
            obj.vertex_groups.active = vg
            bpy.ops.object.vertex_group_deselect()

        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_ACTION", "message": f"Unknown action: {action}"},
            }

    except Exception as e:
        return {"success": False, "error": {"code": "VERTEX_GROUP_FAILED", "message": str(e)}}

    return {"success": True, "data": {"group_name": group_name}}


def handle_vertex_color(params: dict[str, Any]) -> dict[str, Any]:
    """Vertex color operations"""
    object_name = params.get("object_name", "")
    action = params.get("action", "CREATE")
    layer_name = params.get("layer_name", "Col")
    color = params.get("color", [1.0, 1.0, 1.0, 1.0])
    face_indices = params.get("face_indices")

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT",
                "message": f"Object does not exist or is not a mesh: {object_name}",
            },
        }

    mesh = obj.data

    try:
        if action == "CREATE":
            # Create vertex color layer (Blender 3.2+ uses color_attributes)
            if hasattr(mesh, "color_attributes"):
                if layer_name not in [ca.name for ca in mesh.color_attributes]:
                    mesh.color_attributes.new(name=layer_name, type="BYTE_COLOR", domain="CORNER")
            else:
                if layer_name not in [vc.name for vc in mesh.vertex_colors]:
                    mesh.vertex_colors.new(name=layer_name)
            return {"success": True, "data": {"layer_name": layer_name}}

        elif action == "FILL":
            # Fill all vertex colors
            if hasattr(mesh, "color_attributes"):
                ca = mesh.color_attributes.get(layer_name)
                if not ca:
                    ca = mesh.color_attributes.new(
                        name=layer_name, type="BYTE_COLOR", domain="CORNER"
                    )
                for i in range(len(ca.data)):
                    ca.data[i].color = color[:4] if len(color) >= 4 else color + [1.0]
            else:
                vc = mesh.vertex_colors.get(layer_name)
                if not vc:
                    vc = mesh.vertex_colors.new(name=layer_name)
                for i in range(len(vc.data)):
                    vc.data[i].color = color[:4] if len(color) >= 4 else color + [1.0]
            return {"success": True, "data": {"layer_name": layer_name, "filled": True}}

        elif action == "PAINT":
            # Paint by face indices
            if hasattr(mesh, "color_attributes"):
                ca = mesh.color_attributes.get(layer_name)
                if not ca:
                    ca = mesh.color_attributes.new(
                        name=layer_name, type="BYTE_COLOR", domain="CORNER"
                    )
            else:
                ca = mesh.vertex_colors.get(layer_name)
                if not ca:
                    ca = mesh.vertex_colors.new(name=layer_name)

            col = color[:4] if len(color) >= 4 else color + [1.0]

            if face_indices:
                for fi in face_indices:
                    if fi < len(mesh.polygons):
                        poly = mesh.polygons[fi]
                        for li in poly.loop_indices:
                            ca.data[li].color = col
            else:
                # Paint all faces
                for i in range(len(ca.data)):
                    ca.data[i].color = col

            return {
                "success": True,
                "data": {
                    "layer_name": layer_name,
                    "painted_faces": len(face_indices) if face_indices else "all",
                },
            }

        else:
            return {
                "success": False,
                "error": {"code": "UNKNOWN_ACTION", "message": f"Unknown action: {action}"},
            }

    except Exception as e:
        return {"success": False, "error": {"code": "VERTEX_COLOR_FAILED", "message": str(e)}}
