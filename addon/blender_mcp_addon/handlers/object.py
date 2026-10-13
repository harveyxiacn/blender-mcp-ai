"""
Object Handler

Handles object-related commands.
"""

import fnmatch
from typing import Any

import bpy
import mathutils

from .compat import select_only


def _create_mesh_primitive(obj_type: str, mp: dict[str, Any]) -> None:
    """Create a mesh primitive based on type and mesh_params"""
    if obj_type in ("SPHERE", "UV_SPHERE"):
        bpy.ops.mesh.primitive_uv_sphere_add(
            segments=mp.get("segments", 32),
            ring_count=mp.get("ring_count", 16),
            radius=mp.get("radius", 1.0),
        )
    elif obj_type == "ICO_SPHERE":
        bpy.ops.mesh.primitive_ico_sphere_add(
            subdivisions=mp.get("subdivisions", 2),
            radius=mp.get("radius", 1.0),
        )
    elif obj_type == "CYLINDER":
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=mp.get("vertices", 32),
            radius=mp.get("radius", 1.0),
            depth=mp.get("depth", 2.0),
            end_fill_type=mp.get("fill_type", "NGON"),
        )
    elif obj_type == "CONE":
        bpy.ops.mesh.primitive_cone_add(
            vertices=mp.get("vertices", 32),
            radius1=mp.get("radius1", 1.0),
            radius2=mp.get("radius2", 0.0),
            depth=mp.get("depth", 2.0),
            end_fill_type=mp.get("fill_type", "NGON"),
        )
    elif obj_type == "TORUS":
        bpy.ops.mesh.primitive_torus_add(
            major_segments=mp.get("major_segments", 48),
            minor_segments=mp.get("minor_segments", 12),
            major_radius=mp.get("major_radius", 1.0),
            minor_radius=mp.get("minor_radius", 0.25),
        )
    elif obj_type == "CIRCLE":
        bpy.ops.mesh.primitive_circle_add(
            vertices=mp.get("vertices", 32),
            radius=mp.get("radius", 1.0),
            fill_type=mp.get("fill_type", "NOTHING"),
        )
    elif obj_type == "GRID":
        bpy.ops.mesh.primitive_grid_add(
            x_subdivisions=mp.get("x_subdivisions", 10),
            y_subdivisions=mp.get("y_subdivisions", 10),
            size=mp.get("size", 2.0),
        )
    elif obj_type == "CUBE":
        bpy.ops.mesh.primitive_cube_add(
            size=mp.get("size", 2.0),
        )
    elif obj_type == "PLANE":
        bpy.ops.mesh.primitive_plane_add(
            size=mp.get("size", 2.0),
        )
    elif obj_type == "MONKEY":
        bpy.ops.mesh.primitive_monkey_add()
    else:
        return False
    return True


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create an object"""
    obj_type = params.get("type", "CUBE")
    name = params.get("name")
    location = params.get("location", [0, 0, 0])
    rotation = params.get("rotation", [0, 0, 0])
    scale = params.get("scale", [1, 1, 1])
    mp = params.get("mesh_params", {}) or {}

    # Create mesh object
    mesh_types = [
        "CUBE",
        "SPHERE",
        "UV_SPHERE",
        "ICO_SPHERE",
        "CYLINDER",
        "CONE",
        "TORUS",
        "PLANE",
        "CIRCLE",
        "GRID",
        "MONKEY",
    ]

    if obj_type in mesh_types:
        result = _create_mesh_primitive(obj_type, mp)
        if result is False:
            return {
                "success": False,
                "error": {"code": "INVALID_TYPE", "message": f"Unsupported mesh type: {obj_type}"},
            }
    elif obj_type == "EMPTY":
        bpy.ops.object.empty_add(type="PLAIN_AXES", location=location)
    elif obj_type == "TEXT":
        bpy.ops.object.text_add(location=location)
    elif obj_type == "CAMERA":
        bpy.ops.object.camera_add(location=location)
    elif obj_type == "LIGHT":
        bpy.ops.object.light_add(type="POINT", location=location)
    elif obj_type == "ARMATURE":
        bpy.ops.object.armature_add(location=location)
    elif obj_type == "LATTICE":
        u_res = mp.get("u_resolution", 2)
        v_res = mp.get("v_resolution", 2)
        w_res = mp.get("w_resolution", 2)
        bpy.ops.object.add(type="LATTICE", location=location)
        lat = bpy.context.active_object.data
        lat.points_u = u_res
        lat.points_v = v_res
        lat.points_w = w_res
    else:
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": f"Unsupported object type: {obj_type}"},
        }

    # Get the newly created object
    obj = bpy.context.active_object

    # Set transform
    obj.location = location
    obj.rotation_euler = rotation
    obj.scale = scale

    # Rename
    if name:
        obj.name = name

    return {
        "success": True,
        "data": {"object_name": obj.name, "object_type": obj.type, "location": list(obj.location)},
    }


def handle_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete an object"""
    name = params.get("name", "")
    delete_data = params.get("delete_data", True)

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    # Save data reference
    data = obj.data if delete_data else None

    # Delete object
    bpy.data.objects.remove(obj, do_unlink=True)

    # Delete data
    if data:
        if isinstance(data, bpy.types.Mesh):
            bpy.data.meshes.remove(data)
        elif isinstance(data, bpy.types.Curve):
            bpy.data.curves.remove(data)
        # Other types...

    return {"success": True, "data": {}}


def handle_duplicate(params: dict[str, Any]) -> dict[str, Any]:
    """Duplicate an object"""
    name = params.get("name", "")
    new_name = params.get("new_name")
    linked = params.get("linked", False)
    offset = params.get("offset", [0, 0, 0])

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    # Duplicate object
    if linked:
        new_obj = obj.copy()
    else:
        new_obj = obj.copy()
        if obj.data:
            new_obj.data = obj.data.copy()

    # Set name
    if new_name:
        new_obj.name = new_name

    # Set position offset
    new_obj.location = (
        obj.location.x + offset[0],
        obj.location.y + offset[1],
        obj.location.z + offset[2],
    )

    # Link to the scene master collection (always part of the active view layer)
    bpy.context.scene.collection.objects.link(new_obj)

    return {"success": True, "data": {"new_object_name": new_obj.name}}


def handle_transform(params: dict[str, Any]) -> dict[str, Any]:
    """Transform an object"""
    name = params.get("name", "")

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    # Absolute transform
    if "location" in params:
        obj.location = params["location"]
    if "rotation" in params:
        obj.rotation_euler = params["rotation"]
    if "scale" in params:
        obj.scale = params["scale"]

    # Incremental transform
    if "delta_location" in params:
        delta = params["delta_location"]
        obj.location = (
            obj.location.x + delta[0],
            obj.location.y + delta[1],
            obj.location.z + delta[2],
        )
    if "delta_rotation" in params:
        delta = params["delta_rotation"]
        obj.rotation_euler = (
            obj.rotation_euler.x + delta[0],
            obj.rotation_euler.y + delta[1],
            obj.rotation_euler.z + delta[2],
        )
    if "delta_scale" in params:
        delta = params["delta_scale"]
        obj.scale = (obj.scale.x + delta[0], obj.scale.y + delta[1], obj.scale.z + delta[2])

    return {
        "success": True,
        "data": {
            "location": list(obj.location),
            "rotation": list(obj.rotation_euler),
            "scale": list(obj.scale),
        },
    }


def handle_select(params: dict[str, Any]) -> dict[str, Any]:
    """Select objects"""
    names = params.get("names")
    pattern = params.get("pattern")
    deselect_all = params.get("deselect_all", True)
    set_active = params.get("set_active", "")

    # Deselect all
    if deselect_all:
        bpy.ops.object.select_all(action="DESELECT")

    selected_count = 0

    # Select by name
    if names:
        for name in names:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.select_set(True)
                selected_count += 1

    # Select by pattern
    if pattern:
        for obj in bpy.data.objects:
            if fnmatch.fnmatch(obj.name, pattern):
                obj.select_set(True)
                selected_count += 1

    # Set active object
    if set_active:
        obj = bpy.data.objects.get(set_active)
        if obj:
            bpy.context.view_layer.objects.active = obj

    return {"success": True, "data": {"selected_count": selected_count}}


def handle_list(params: dict[str, Any]) -> dict[str, Any]:
    """List objects"""
    type_filter = params.get("type_filter")
    name_pattern = params.get("name_pattern")
    limit = params.get("limit", 50)

    objects = []

    for obj in bpy.data.objects:
        # Type filter
        if type_filter and obj.type != type_filter:
            continue

        # Name filter
        if name_pattern and not fnmatch.fnmatch(obj.name, name_pattern):
            continue

        objects.append(
            {
                "name": obj.name,
                "type": obj.type,
                "location": list(obj.location),
                "visible": obj.visible_get(),
            }
        )

        if len(objects) >= limit:
            break

    return {"success": True, "data": {"objects": objects, "total": len(bpy.data.objects)}}


def handle_get_info(params: dict[str, Any]) -> dict[str, Any]:
    """Get object info"""
    name = params.get("name", "")
    include_mesh_stats = params.get("include_mesh_stats", True)
    include_modifiers = params.get("include_modifiers", True)
    include_materials = params.get("include_materials", True)

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    data = {
        "name": obj.name,
        "type": obj.type,
        "location": list(obj.location),
        "rotation_euler": list(obj.rotation_euler),
        "scale": list(obj.scale),
        "dimensions": list(obj.dimensions),
    }

    # Mesh statistics
    if include_mesh_stats and obj.type == "MESH" and obj.data:
        mesh = obj.data
        data["mesh_stats"] = {
            "vertices": len(mesh.vertices),
            "edges": len(mesh.edges),
            "faces": len(mesh.polygons),
            "triangles": sum(len(p.vertices) - 2 for p in mesh.polygons),
        }

    # Modifiers
    if include_modifiers:
        data["modifiers"] = [mod.name for mod in obj.modifiers]

    # Materials
    if include_materials:
        data["materials"] = [
            slot.material.name if slot.material else None for slot in obj.material_slots
        ]

    # Unity-readiness / Transform check: surfaces a baked-translation footgun
    # that mesh_stats can't reveal (under bake_space_transform a non-zero
    # .location imports into Unity offset, not at (0,0,0)).
    if params.get("include_transform_check", False):
        eps = 1e-5
        loc = obj.location
        rot = obj.rotation_euler
        scl = obj.scale
        loc_zero = all(abs(v) < eps for v in loc)
        rot_id = all(abs(v) < eps for v in rot)
        scl_one = all(abs(v - 1.0) < eps for v in scl)
        notes = []
        if not loc_zero:
            notes.append(
                "object .location is non-zero; under bake_space_transform it bakes "
                "into the FBX as a translation (imports offset, not at 0,0,0)"
            )
        if not rot_id:
            notes.append("unapplied rotation will bake into the mesh on export")
        if not scl_one:
            notes.append("unapplied scale will bake into the mesh on export")
        data["unity_ready"] = {
            "world_translation": [round(v, 5) for v in obj.matrix_world.translation],
            "location_is_zero": loc_zero,
            "rotation_is_identity": rot_id,
            "scale_is_one": scl_one,
            "will_import_at_origin": loc_zero,
            "notes": notes,
        }

    return {"success": True, "data": data}


def handle_rename(params: dict[str, Any]) -> dict[str, Any]:
    """Rename an object"""
    name = params.get("name", "")
    new_name = params.get("new_name")

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    obj.name = new_name

    return {"success": True, "data": {"new_name": obj.name}}


def handle_set_parent(params: dict[str, Any]) -> dict[str, Any]:
    """Set parent-child relationship"""
    child_name = params.get("child_name", "")
    parent_name = params.get("parent_name", "")
    keep_transform = params.get("keep_transform", True)

    if not child_name:
        return {
            "success": False,
            "error": {
                "code": "MISSING_PARAM",
                "message": "child_name parameter is required",
            },
        }

    child = bpy.data.objects.get(child_name)
    if not child:
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Child object not found: {child_name}",
            },
        }

    if parent_name:
        parent = bpy.data.objects.get(parent_name)
        if not parent:
            return {
                "success": False,
                "error": {
                    "code": "OBJECT_NOT_FOUND",
                    "message": f"Parent object not found: {parent_name}",
                },
            }

        if keep_transform:
            child.parent = parent
            child.matrix_parent_inverse = parent.matrix_world.inverted()
        else:
            child.parent = parent
    else:
        child.parent = None

    return {"success": True, "data": {}}


def handle_join(params: dict[str, Any]) -> dict[str, Any]:
    """Join objects"""
    objects = params.get("objects", [])
    target = params.get("target")

    if len(objects) < 2:
        return {
            "success": False,
            "error": {
                "code": "INVALID_PARAMS",
                "message": "At least two objects are required to join",
            },
        }

    # Deselect all
    bpy.ops.object.select_all(action="DESELECT")

    # Select objects to join
    target_obj = None
    for name in objects:
        obj = bpy.data.objects.get(name)
        if obj:
            obj.select_set(True)
            if target and name == target or target_obj is None:
                target_obj = obj

    if not target_obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": "No objects found to join"},
        }

    # Set active object
    bpy.context.view_layer.objects.active = target_obj

    # Join
    bpy.ops.object.join()

    return {"success": True, "data": {"result_object": bpy.context.active_object.name}}


def _set_origin_to_point(obj: "bpy.types.Object", new_origin_world: "mathutils.Vector") -> None:
    """Relocate the object's origin to new_origin_world (world space).

    Shifts mesh vertices by the inverse offset so geometry stays in place,
    then moves obj.location to the new origin. No bpy.ops needed.
    """
    # Offset in world space
    offset_world = new_origin_world - obj.matrix_world.translation

    # Convert offset to object-local space for vertex adjustment
    offset_local = obj.matrix_world.inverted().to_3x3() @ offset_world

    if obj.type == "MESH" and obj.data:
        for v in obj.data.vertices:
            v.co += offset_local
        obj.data.update()

    # Move object location to compensate
    obj.matrix_world.translation += offset_world


def handle_set_origin(params: dict[str, Any]) -> dict[str, Any]:
    """Set object origin without bpy.ops (Blender 5.x safe).

    origin_type options:
      GEOMETRY  — centroid of all vertices (MEDIAN) or bounding-box centre (BOUNDS)
      CURSOR    — current 3D-cursor position
      BOTTOM    — bottom-centre of the world-space bounding box (useful for characters)
      CENTER_OF_MASS — same as GEOMETRY/MEDIAN for meshes
    """
    name = params.get("name", "")
    origin_type = params.get("origin_type", "GEOMETRY")
    center = params.get("center", "MEDIAN")

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    try:
        if origin_type in ("GEOMETRY", "CENTER_OF_MASS"):
            if obj.type != "MESH" or not obj.data or not obj.data.vertices:
                return {
                    "success": False,
                    "error": {"code": "INVALID_TYPE", "message": "Object has no mesh vertices"},
                }
            verts_world = [obj.matrix_world @ v.co for v in obj.data.vertices]
            if center == "BOUNDS":
                xs = [v.x for v in verts_world]
                ys = [v.y for v in verts_world]
                zs = [v.z for v in verts_world]
                new_origin = mathutils.Vector(
                    ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2)
                )
            else:  # MEDIAN
                n = len(verts_world)
                new_origin = mathutils.Vector(
                    (
                        sum(v.x for v in verts_world) / n,
                        sum(v.y for v in verts_world) / n,
                        sum(v.z for v in verts_world) / n,
                    )
                )
            _set_origin_to_point(obj, new_origin)

        elif origin_type == "CURSOR":
            cursor_world = mathutils.Vector(bpy.context.scene.cursor.location)
            _set_origin_to_point(obj, cursor_world)

        elif origin_type == "BOTTOM":
            bbox_world = [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]
            min_z = min(v.z for v in bbox_world)
            cx = sum(v.x for v in bbox_world) / 8
            cy = sum(v.y for v in bbox_world) / 8
            _set_origin_to_point(obj, mathutils.Vector((cx, cy, min_z)))

        else:
            return {
                "success": False,
                "error": {
                    "code": "INVALID_ORIGIN_TYPE",
                    "message": f"Unsupported origin type: {origin_type}",
                },
            }

        return {
            "success": True,
            "data": {
                "object_name": obj.name,
                "origin_type": origin_type,
                "new_origin": list(obj.location),
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "SET_ORIGIN_ERROR", "message": str(e)}}


def handle_apply_transform(params: dict[str, Any]) -> dict[str, Any]:
    """Apply transform

    Args:
        params:
            - name: Object name
            - location: Apply location
            - rotation: Apply rotation
            - scale: Apply scale
    """
    name = params.get("name", "")
    apply_location = params.get("location", False)
    apply_rotation = params.get("rotation", False)
    apply_scale = params.get("scale", True)

    obj = bpy.data.objects.get(name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {name}"},
        }

    if obj.type != "MESH" or obj.data is None:
        return {
            "success": False,
            "error": {
                "code": "INVALID_TYPE",
                "message": "apply_transform currently supports mesh objects only",
            },
        }

    # Pure data-API transform apply (no bpy.ops, Blender 5.x safe).
    # Decompose the local matrix and bake the requested components into the mesh.
    try:
        loc, rot, scale = obj.matrix_basis.decompose()

        bake = mathutils.Matrix.Identity(4)
        if apply_location:
            bake = mathutils.Matrix.Translation(loc) @ bake
        if apply_rotation:
            bake = bake @ rot.to_matrix().to_4x4()
        if apply_scale:
            bake = bake @ mathutils.Matrix.Diagonal(scale.to_4d())

        # Apply baked matrix to mesh vertices, then reset those components.
        obj.data.transform(bake)
        obj.data.update()

        if apply_location:
            obj.location = (0.0, 0.0, 0.0)
        if apply_rotation:
            obj.rotation_euler = (0.0, 0.0, 0.0)
        if apply_scale:
            obj.scale = (1.0, 1.0, 1.0)

        return {
            "success": True,
            "data": {
                "object_name": obj.name,
                "applied": {
                    "location": apply_location,
                    "rotation": apply_rotation,
                    "scale": apply_scale,
                },
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "APPLY_TRANSFORM_ERROR", "message": str(e)}}
