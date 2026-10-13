"""
Modeling Handler

Handles modeling-related commands.
"""

from typing import Any

import bpy

from .compat import select_only


def _apply_modifier(obj: "bpy.types.Object", modifier_name: str) -> str | None:
    """Apply a modifier using the depsgraph data API (no bpy.ops, Blender 5.x safe).

    Returns None on success, or an error string on failure.
    """
    mod = obj.modifiers.get(modifier_name)
    if not mod:
        return f"Modifier not found: {modifier_name}"

    try:
        # Evaluate the object with all modifiers applied up to this one
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        new_mesh = bpy.data.meshes.new_from_object(eval_obj, depsgraph=depsgraph)

        # Swap the mesh data and remove the modifier
        old_mesh = obj.data
        obj.data = new_mesh
        obj.modifiers.remove(mod)

        # Clean up orphan mesh if nothing else uses it
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

        return None
    except Exception as e:
        return str(e)


def handle_edit_mode(params: dict[str, Any]) -> dict[str, Any]:
    """Enter/exit edit mode"""
    object_name = params.get("object_name", "")
    enter = params.get("enter", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Switch mode
    if enter:
        bpy.ops.object.mode_set(mode="EDIT")
    else:
        bpy.ops.object.mode_set(mode="OBJECT")

    return {"success": True, "data": {"mode": bpy.context.mode}}


def handle_select(params: dict[str, Any]) -> dict[str, Any]:
    """Mesh selection"""
    object_name = params.get("object_name", "")
    select_mode = params.get("select_mode", "VERT")
    action = params.get("action", "ALL")
    random_ratio = params.get("random_ratio", 0.5)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_OBJECT", "message": "Object not found or is not a mesh"},
        }

    # Ensure in edit mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    # Set selection mode
    mode_map = {
        "VERT": (True, False, False),
        "EDGE": (False, True, False),
        "FACE": (False, False, True),
    }
    bpy.context.tool_settings.mesh_select_mode = mode_map.get(select_mode, (True, False, False))

    # Execute selection operation
    if action == "ALL":
        bpy.ops.mesh.select_all(action="SELECT")
    elif action == "NONE":
        bpy.ops.mesh.select_all(action="DESELECT")
    elif action == "INVERT":
        bpy.ops.mesh.select_all(action="INVERT")
    elif action == "RANDOM":
        bpy.ops.mesh.select_random(ratio=random_ratio)
    elif action == "LINKED":
        bpy.ops.mesh.select_linked()

    return {"success": True, "data": {}}


def handle_extrude(params: dict[str, Any]) -> dict[str, Any]:
    """Extrude"""
    object_name = params.get("object_name", "")
    direction = params.get("direction", [0, 0, 1])
    distance = params.get("distance", 1.0)
    use_normal = params.get("use_normal", True)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_OBJECT", "message": "Object not found or is not a mesh"},
        }

    # Ensure in edit mode
    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    # Extrude
    if use_normal:
        bpy.ops.mesh.extrude_region_shrink_fatten(TRANSFORM_OT_shrink_fatten={"value": distance})
    else:
        bpy.ops.mesh.extrude_region_move(
            TRANSFORM_OT_translate={
                "value": (direction[0] * distance, direction[1] * distance, direction[2] * distance)
            }
        )

    return {"success": True, "data": {}}


def handle_subdivide(params: dict[str, Any]) -> dict[str, Any]:
    """Subdivide"""
    object_name = params.get("object_name", "")
    cuts = params.get("cuts", 1)
    smoothness = params.get("smoothness", 0.0)

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_OBJECT", "message": "Object not found or is not a mesh"},
        }

    # Ensure in edit mode
    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.mesh.subdivide(number_cuts=cuts, smoothness=smoothness)

    return {"success": True, "data": {}}


def handle_bevel(params: dict[str, Any]) -> dict[str, Any]:
    """Bevel"""
    object_name = params.get("object_name", "")
    width = params.get("width", 0.1)
    segments = params.get("segments", 1)
    profile = params.get("profile", 0.5)
    affect = params.get("affect", "EDGES")

    obj = bpy.data.objects.get(object_name)
    if not obj or obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_OBJECT", "message": "Object not found or is not a mesh"},
        }

    # Ensure in edit mode
    bpy.context.view_layer.objects.active = obj
    if bpy.context.mode != "EDIT_MESH":
        bpy.ops.object.mode_set(mode="EDIT")

    bpy.ops.mesh.bevel(offset=width, segments=segments, profile=profile, affect=affect)

    return {"success": True, "data": {}}


def handle_modifier_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add modifier"""
    object_name = params.get("object_name", "")
    modifier_type = params.get("modifier_type")
    modifier_name = params.get("modifier_name")
    settings = params.get("settings", {})

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    # Ensure in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # Add modifier. Passing an empty name lets Blender apply its canonical
    # default ("BEVEL" would otherwise show up in the UI as the raw enum value).
    mod = obj.modifiers.new(name=modifier_name or "", type=modifier_type)

    # Apply settings
    for key, value in settings.items():
        if hasattr(mod, key):
            setattr(mod, key, value)

    return {"success": True, "data": {"modifier_name": mod.name}}


def handle_modifier_apply(params: dict[str, Any]) -> dict[str, Any]:
    """Apply modifier"""
    object_name = params.get("object_name", "")
    modifier_name = params.get("modifier_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    mod = obj.modifiers.get(modifier_name)
    if not mod:
        return {
            "success": False,
            "error": {
                "code": "MODIFIER_NOT_FOUND",
                "message": f"Modifier not found: {modifier_name}",
            },
        }

    error = _apply_modifier(obj, modifier_name)
    if error:
        return {"success": False, "error": {"code": "MODIFIER_APPLY_FAILED", "message": error}}

    return {"success": True, "data": {}}


def handle_modifier_remove(params: dict[str, Any]) -> dict[str, Any]:
    """Remove modifier"""
    object_name = params.get("object_name", "")
    modifier_name = params.get("modifier_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    mod = obj.modifiers.get(modifier_name)
    if not mod:
        return {
            "success": False,
            "error": {
                "code": "MODIFIER_NOT_FOUND",
                "message": f"Modifier not found: {modifier_name}",
            },
        }

    obj.modifiers.remove(mod)

    return {"success": True, "data": {}}


def handle_boolean(params: dict[str, Any]) -> dict[str, Any]:
    """Boolean operation via the BOOLEAN modifier.

    apply=False (default): adds the modifier with viewport display disabled.
      This is non-destructive and, crucially, avoids Blender evaluating the
      boolean on the next viewport redraw — live boolean evaluation against a
      heavy scene can crash/stall Blender 5.x. Enable show_viewport manually
      in Blender when you want to preview it.

    apply=True: evaluates and bakes the result into the mesh via the depsgraph
      data API (no bpy.ops). Suitable for simple/manifold inputs; can be slow
      on very heavy scenes.
    """
    object_name = params.get("object_name", "")
    target_name = params.get("target_name", "")
    operation = params.get("operation", "DIFFERENCE")
    apply = params.get("apply", False)
    hide_target = params.get("hide_target", apply)
    solver = params.get("solver", "EXACT")

    obj = bpy.data.objects.get(object_name)
    target = bpy.data.objects.get(target_name)

    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }
    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": f"'{object_name}' is not a mesh"},
        }
    if not target:
        return {
            "success": False,
            "error": {
                "code": "OBJECT_NOT_FOUND",
                "message": f"Target object not found: {target_name}",
            },
        }
    if target.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": f"'{target_name}' is not a mesh"},
        }

    op_upper = operation.upper()
    if op_upper not in ("DIFFERENCE", "UNION", "INTERSECT"):
        op_upper = "DIFFERENCE"

    mod = obj.modifiers.new(name="Boolean", type="BOOLEAN")
    mod.operation = op_upper
    mod.object = target
    if hasattr(mod, "solver"):
        mod.solver = solver

    if not apply:
        # Disable viewport evaluation to avoid crash-on-redraw in heavy scenes.
        mod.show_viewport = False
        return {
            "success": True,
            "data": {
                "modifier_name": mod.name,
                "modifier_applied": False,
                "operation": op_upper,
                "note": "Modifier added with viewport display off; enable it to preview.",
            },
        }

    error = _apply_modifier(obj, mod.name)
    if error:
        return {
            "success": False,
            "error": {
                "code": "BOOLEAN_APPLY_FAILED",
                "message": f"Boolean apply failed: {error}. The mesh may be non-manifold.",
            },
        }

    if hide_target:
        target.hide_viewport = True
        target.hide_render = True

    return {
        "success": True,
        "data": {
            "operation": op_upper,
            "modifier_applied": True,
            "vertices": len(obj.data.vertices),
            "faces": len(obj.data.polygons),
        },
    }


# ==================== Shape Keys Functions ====================


def handle_shapekey_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create shape key

    Args:
        params:
            - object_name: Object name
            - key_name: Shape key name
            - from_mix: Whether to create from current mix state
    """
    object_name = params.get("object_name", "")
    key_name = params.get("key_name", "Key")
    from_mix = params.get("from_mix", False)

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
                "message": "Shape keys are only supported for mesh objects",
            },
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Ensure in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    # If no shape keys exist, create the basis shape key first
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)

    # Create new shape key
    shape_key = obj.shape_key_add(name=key_name, from_mix=from_mix)

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "key_name": shape_key.name,
            "key_index": len(obj.data.shape_keys.key_blocks) - 1,
        },
    }


def handle_shapekey_edit(params: dict[str, Any]) -> dict[str, Any]:
    """Edit shape key

    Args:
        params:
            - object_name: Object name
            - key_name: Shape key name
            - vertex_offsets: Vertex offset list [{"index": int, "offset": [x, y, z]}, ...]
            - value: Shape key value (0.0 - 1.0)
            - mute: Whether to mute
    """
    object_name = params.get("object_name", "")
    key_name = params.get("key_name", "")
    vertex_offsets = params.get("vertex_offsets", [])
    value = params.get("value")
    mute = params.get("mute")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if not obj.data.shape_keys:
        return {
            "success": False,
            "error": {"code": "NO_SHAPE_KEYS", "message": "Object has no shape keys"},
        }

    shape_key = obj.data.shape_keys.key_blocks.get(key_name)
    if not shape_key:
        return {
            "success": False,
            "error": {"code": "SHAPE_KEY_NOT_FOUND", "message": f"Shape key not found: {key_name}"},
        }

    # Set value
    if value is not None:
        shape_key.value = value

    # Set mute
    if mute is not None:
        shape_key.mute = mute

    # Apply vertex offsets
    if vertex_offsets:
        basis = obj.data.shape_keys.key_blocks.get("Basis")
        if not basis:
            return {
                "success": False,
                "error": {"code": "NO_BASIS", "message": "Basis shape key not found"},
            }

        for offset_data in vertex_offsets:
            idx = offset_data.get("index")
            offset = offset_data.get("offset", [0, 0, 0])

            if idx is not None and 0 <= idx < len(shape_key.data):
                # Get basis position and apply offset
                base_co = basis.data[idx].co
                shape_key.data[idx].co = (
                    base_co.x + offset[0],
                    base_co.y + offset[1],
                    base_co.z + offset[2],
                )

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "key_name": key_name,
            "value": shape_key.value,
            "mute": shape_key.mute,
        },
    }


def handle_shapekey_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Delete shape key

    Args:
        params:
            - object_name: Object name
            - key_name: Shape key name
    """
    object_name = params.get("object_name", "")
    key_name = params.get("key_name")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if not obj.data.shape_keys:
        return {
            "success": False,
            "error": {"code": "NO_SHAPE_KEYS", "message": "Object has no shape keys"},
        }

    # Find shape key index
    key_index = None
    for i, key in enumerate(obj.data.shape_keys.key_blocks):
        if key.name == key_name:
            key_index = i
            break

    if key_index is None:
        return {
            "success": False,
            "error": {"code": "SHAPE_KEY_NOT_FOUND", "message": f"Shape key not found: {key_name}"},
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Set active shape key
    obj.active_shape_key_index = key_index

    # Delete shape key
    bpy.ops.object.shape_key_remove()

    return {"success": True, "data": {"object_name": obj.name, "deleted_key": key_name}}


def handle_shapekey_list(params: dict[str, Any]) -> dict[str, Any]:
    """List shape keys

    Args:
        params:
            - object_name: Object name
    """
    object_name = params.get("object_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if not obj.data.shape_keys:
        return {"success": True, "data": {"object_name": obj.name, "shape_keys": [], "total": 0}}

    keys = []
    for i, key in enumerate(obj.data.shape_keys.key_blocks):
        keys.append(
            {
                "index": i,
                "name": key.name,
                "value": key.value,
                "mute": key.mute,
                "slider_min": key.slider_min,
                "slider_max": key.slider_max,
            }
        )

    return {
        "success": True,
        "data": {"object_name": obj.name, "shape_keys": keys, "total": len(keys)},
    }


def handle_shapekey_create_expression(params: dict[str, Any]) -> dict[str, Any]:
    """Create expression shape key set

    Quickly create a set of commonly used expression shape keys for a character.

    Args:
        params:
            - object_name: Object name
            - expressions: List of expressions to create, possible values:
                - smile: Smile
                - frown: Frown
                - surprise: Surprise
                - angry: Angry
                - sad: Sad
                - blink_l: Left eye close
                - blink_r: Right eye close
                - blink: Both eyes close
                - mouth_open: Mouth open
                - mouth_wide: Mouth wide open
    """
    object_name = params.get("object_name", "")
    expressions = params.get("expressions", ["smile", "blink", "surprise", "angry"])

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Shape keys only support mesh objects"},
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # Ensure base shape key exists
    if not obj.data.shape_keys:
        obj.shape_key_add(name="Basis", from_mix=False)

    # Expression name mapping
    expression_names = {
        "smile": "Smile",
        "frown": "Frown",
        "surprise": "Surprise",
        "angry": "Angry",
        "sad": "Sad",
        "blink_l": "Blink_L",
        "blink_r": "Blink_R",
        "blink": "Blink",
        "mouth_open": "MouthOpen",
        "mouth_wide": "MouthWide",
    }

    created_keys = []
    for expr in expressions:
        name = expression_names.get(expr, expr)
        # Check if already exists
        if obj.data.shape_keys.key_blocks.get(name):
            continue

        shape_key = obj.shape_key_add(name=name, from_mix=False)
        created_keys.append(shape_key.name)

    return {
        "success": True,
        "data": {"object_name": obj.name, "created_keys": created_keys, "total": len(created_keys)},
    }


def handle_mesh_assign_material_to_faces(params: dict[str, Any]) -> dict[str, Any]:
    """Assign material to specific faces

    Args:
        params:
            - object_name: Object name
            - face_indices: List of face indices
            - material_slot: Material slot index
            - material_name: Or specify by material name
    """
    object_name = params.get("object_name", "")
    face_indices = params.get("face_indices", [])
    material_slot = params.get("material_slot")
    material_name = params.get("material_name")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Find slot index by material name
    if material_name and material_slot is None:
        for i, slot in enumerate(obj.material_slots):
            if slot.material and slot.material.name == material_name:
                material_slot = i
                break

        if material_slot is None:
            return {
                "success": False,
                "error": {
                    "code": "MATERIAL_NOT_FOUND",
                    "message": f"Material not in object's material slots: {material_name}",
                },
            }

    if material_slot is None:
        return {
            "success": False,
            "error": {
                "code": "INVALID_PARAMS",
                "message": "Please specify material_slot or material_name",
            },
        }

    if material_slot >= len(obj.material_slots):
        return {
            "success": False,
            "error": {
                "code": "INVALID_SLOT",
                "message": f"Material slot index out of range: {material_slot}",
            },
        }

    # Assign material to faces
    mesh = obj.data

    # Ensure in object mode
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")

    assigned_count = 0
    for idx in face_indices:
        if 0 <= idx < len(mesh.polygons):
            mesh.polygons[idx].material_index = material_slot
            assigned_count += 1

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "material_slot": material_slot,
            "assigned_faces": assigned_count,
        },
    }


def handle_select_faces_by_material(params: dict[str, Any]) -> dict[str, Any]:
    """Select faces by material

    Args:
        params:
            - object_name: Object name
            - material_slot: Material slot index
            - material_name: Or specify by material name
    """
    object_name = params.get("object_name", "")
    material_slot = params.get("material_slot")
    material_name = params.get("material_name")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Find slot index by material name
    if material_name and material_slot is None:
        for i, slot in enumerate(obj.material_slots):
            if slot.material and slot.material.name == material_name:
                material_slot = i
                break

    if material_slot is None:
        return {
            "success": False,
            "error": {
                "code": "INVALID_PARAMS",
                "message": "Please specify material_slot or material_name",
            },
        }

    # Select object and enter edit mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    # Deselect all
    bpy.ops.mesh.select_all(action="DESELECT")

    # Set face selection mode
    bpy.context.tool_settings.mesh_select_mode = (False, False, True)

    # Set active material slot
    obj.active_material_index = material_slot

    # Select faces using this material
    bpy.ops.object.material_slot_select()

    # Return to object mode
    bpy.ops.object.mode_set(mode="OBJECT")

    # Count selected faces
    selected_count = sum(1 for p in obj.data.polygons if p.select)

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "material_slot": material_slot,
            "selected_faces": selected_count,
        },
    }


# ==================== Production-grade optimization tools ====================

# Platform triangle limit configuration
PLATFORM_LIMITS = {
    "MOBILE": {"min": 500, "max": 2000, "recommended": 1500},
    "PC_CONSOLE": {"min": 2000, "max": 50000, "recommended": 20000},
    "CINEMATIC": {"min": 0, "max": float("inf"), "recommended": 100000},
    "VR": {"min": 1000, "max": 10000, "recommended": 5000},
}


def handle_mesh_analyze(params: dict[str, Any]) -> dict[str, Any]:
    """Analyze mesh topology quality

    Args:
        params:
            - object_name: Object name
            - target_platform: Target platform
    """
    import bmesh

    object_name = params.get("object_name", "")
    target_platform = params.get("target_platform", "PC_CONSOLE")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    mesh = obj.data

    # Basic statistics
    vertex_count = len(mesh.vertices)
    edge_count = len(mesh.edges)
    face_count = len(mesh.polygons)

    # Calculate triangle count and face type distribution
    tris = 0
    quads = 0
    ngons = 0
    triangle_count = 0

    for poly in mesh.polygons:
        vert_count = len(poly.vertices)
        if vert_count == 3:
            tris += 1
            triangle_count += 1
        elif vert_count == 4:
            quads += 1
            triangle_count += 2  # One quad = 2 triangles
        else:
            ngons += 1
            triangle_count += vert_count - 2  # N-gon to triangle count

    # Calculate percentages
    total_faces = max(face_count, 1)
    tris_percent = (tris / total_faces) * 100
    quads_percent = (quads / total_faces) * 100
    ngons_percent = (ngons / total_faces) * 100

    # Use bmesh for advanced analysis
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # Detect issues
    issues = []

    # Non-manifold edges
    non_manifold_edges = [e for e in bm.edges if not e.is_manifold]
    if non_manifold_edges:
        issues.append(f"Non-manifold edges: {len(non_manifold_edges)}")

    # Non-manifold vertices
    non_manifold_verts = [v for v in bm.verts if not v.is_manifold]
    if non_manifold_verts:
        issues.append(f"Non-manifold vertices: {len(non_manifold_verts)}")

    # Loose vertices
    loose_verts = [v for v in bm.verts if not v.link_edges]
    if loose_verts:
        issues.append(f"Loose vertices: {len(loose_verts)}")

    # Loose edges
    loose_edges = [e for e in bm.edges if not e.link_faces]
    if loose_edges:
        issues.append(f"Loose edges: {len(loose_edges)}")

    # Degenerate faces (zero area)
    degenerate_faces = [f for f in bm.faces if f.calc_area() < 1e-8]
    if degenerate_faces:
        issues.append(f"Degenerate faces: {len(degenerate_faces)}")

    # N-gon warning
    if ngons > 0:
        issues.append("Contains N-gons, may cause deformation issues")

    # Check normal consistency (simple check for flipped normals)
    # By checking face normal direction consistency

    bm.free()

    # Platform compatibility check
    limits = PLATFORM_LIMITS.get(target_platform, PLATFORM_LIMITS["PC_CONSOLE"])
    platform_passed = limits["min"] <= triangle_count <= limits["max"]

    suggestion = ""
    if triangle_count > limits["max"]:
        suggestion = f"Triangle count too high, recommend using mesh optimization to reduce below {limits['recommended']}"
    elif triangle_count < limits["min"]:
        suggestion = "Triangle count too low, may need more detail"

    # Calculate quality score (0-100)
    quality_score = 100

    # N-gon penalty
    if ngons_percent > 0:
        quality_score -= min(20, ngons_percent)

    # Issue penalty
    quality_score -= min(30, len(issues) * 5)

    # Platform compatibility penalty
    if not platform_passed:
        quality_score -= 20

    # Quad bonus (preferred in games and animation)
    if quads_percent > 80:
        quality_score = min(100, quality_score + 10)

    quality_score = max(0, quality_score)

    return {
        "success": True,
        "data": {
            "stats": {
                "vertices": vertex_count,
                "edges": edge_count,
                "faces": face_count,
                "triangles": triangle_count,
            },
            "face_types": {
                "tris": tris,
                "tris_percent": tris_percent,
                "quads": quads,
                "quads_percent": quads_percent,
                "ngons": ngons,
                "ngons_percent": ngons_percent,
            },
            "platform_check": {
                "passed": platform_passed,
                "min_tris": limits["min"],
                "max_tris": limits["max"] if limits["max"] != float("inf") else "unlimited",
                "suggestion": suggestion,
            },
            "issues": issues,
            "quality_score": int(quality_score),
        },
    }


def handle_mesh_optimize(params: dict[str, Any]) -> dict[str, Any]:
    """Optimize mesh (decimation)

    Args:
        params:
            - object_name: Object name
            - target_triangles: Target triangle count
            - target_platform: Target platform
            - preserve_uvs: Preserve UVs
            - preserve_normals: Preserve normals
            - symmetry: Maintain symmetry
    """
    object_name = params.get("object_name", "")
    target_triangles = params.get("target_triangles")
    target_platform = params.get("target_platform", "PC_CONSOLE")
    preserve_uvs = params.get("preserve_uvs", True)
    params.get("preserve_normals", True)
    symmetry = params.get("symmetry", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Calculate original triangle count
    original_triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    # Determine target triangle count
    if target_triangles is None:
        limits = PLATFORM_LIMITS.get(target_platform, PLATFORM_LIMITS["PC_CONSOLE"])
        target_triangles = limits["recommended"]

    # Calculate required decimation ratio
    if original_triangles <= target_triangles:
        return {
            "success": True,
            "data": {
                "original_triangles": original_triangles,
                "optimized_triangles": original_triangles,
                "reduction_percent": 0,
                "message": "Face count is already within target range, no optimization needed",
            },
        }

    ratio = target_triangles / original_triangles

    # Add Decimate modifier
    decimate = obj.modifiers.new(name="MCP_Decimate", type="DECIMATE")
    decimate.decimate_type = "COLLAPSE"
    decimate.ratio = ratio

    # Set UV and normal preservation
    if preserve_uvs:
        decimate.use_collapse_triangulate = False

    if symmetry:
        decimate.use_symmetry = True
        decimate.symmetry_axis = "X"

    # Apply modifier
    _apply_modifier(obj, decimate.name)

    # Calculate optimized triangle count
    optimized_triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    reduction_percent = ((original_triangles - optimized_triangles) / original_triangles) * 100

    return {
        "success": True,
        "data": {
            "original_triangles": original_triangles,
            "optimized_triangles": optimized_triangles,
            "reduction_percent": reduction_percent,
        },
    }


def handle_mesh_cleanup(params: dict[str, Any]) -> dict[str, Any]:
    """Clean up mesh

    Args:
        params:
            - object_name: Object name
            - merge_distance: Merge distance
            - remove_doubles: Remove duplicate vertices
            - dissolve_degenerate: Dissolve degenerate geometry
            - fix_non_manifold: Fix non-manifold geometry
            - recalculate_normals: Recalculate normals
            - remove_loose: Remove loose geometry
    """

    object_name = params.get("object_name", "")
    merge_distance = params.get("merge_distance", 0.0001)
    remove_doubles = params.get("remove_doubles", True)
    dissolve_degenerate = params.get("dissolve_degenerate", True)
    fix_non_manifold = params.get("fix_non_manifold", True)
    recalculate_normals = params.get("recalculate_normals", True)
    remove_loose = params.get("remove_loose", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Select object and enter edit mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    original_verts = len(obj.data.vertices)
    fixed_issues = 0

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")

    # Remove duplicate vertices
    if remove_doubles:
        bpy.ops.mesh.remove_doubles(threshold=merge_distance)
        # Removed vertex count calculated later

    # Dissolve degenerate geometry
    if dissolve_degenerate:
        bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
        fixed_issues += 1

    # Remove loose geometry
    if remove_loose:
        bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
        fixed_issues += 1

    # Recalculate normals
    if recalculate_normals:
        bpy.ops.mesh.normals_make_consistent(inside=False)
        fixed_issues += 1

    # Fix non-manifold (try to fill holes)
    if fix_non_manifold:
        # Select non-manifold geometry
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.mesh.select_non_manifold()
        # Try to fill small holes
        try:
            bpy.ops.mesh.fill_holes(sides=4)
            fixed_issues += 1
        except:
            pass  # Skip if no non-manifold edges selected

    bpy.ops.object.mode_set(mode="OBJECT")

    # Calculate removed vertex count
    removed_verts = original_verts - len(obj.data.vertices)

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "removed_vertices": removed_verts,
            "fixed_issues": fixed_issues,
        },
    }


def handle_tris_to_quads(params: dict[str, Any]) -> dict[str, Any]:
    """Convert triangles to quads

    Args:
        params:
            - object_name: Object name
            - max_angle: Maximum angle
            - compare_uvs: Compare UVs
            - compare_vcol: Compare vertex colors
            - compare_materials: Compare materials
    """
    object_name = params.get("object_name", "")
    max_angle = params.get("max_angle", 40.0)
    compare_uvs = params.get("compare_uvs", True)
    compare_vcol = params.get("compare_vcol", True)
    compare_materials = params.get("compare_materials", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Record original face count
    original_faces = len(obj.data.polygons)
    original_tris = sum(1 for p in obj.data.polygons if len(p.vertices) == 3)

    # Select object and enter edit mode
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")

    # Select all faces
    bpy.ops.mesh.select_all(action="SELECT")

    # Convert triangles to quads
    import math

    bpy.ops.mesh.tris_convert_to_quads(
        face_threshold=math.radians(max_angle),
        shape_threshold=math.radians(max_angle),
        uvs=compare_uvs,
        vcols=compare_vcol,
        seam=False,
        sharp=False,
        materials=compare_materials,
    )

    bpy.ops.object.mode_set(mode="OBJECT")

    # Calculate face count after conversion
    new_faces = len(obj.data.polygons)
    converted = (
        original_faces - new_faces
    )  # Each pair of triangles converted to a quad reduces face count by one

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "original_tris": original_tris,
            "converted_faces": converted,
        },
    }


def handle_lod_generate(params: dict[str, Any]) -> dict[str, Any]:
    """Generate LOD (Level of Detail)

    Args:
        params:
            - object_name: Object name
            - lod_levels: Number of LOD levels
            - ratio_step: Reduction ratio per level
            - create_collection: Whether to create a collection
    """
    object_name = params.get("object_name", "")
    lod_levels = params.get("lod_levels", 3)
    ratio_step = params.get("ratio_step", 0.5)
    create_collection = params.get("create_collection", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Create LOD collection
    if create_collection:
        lod_collection_name = f"{obj.name}_LOD"
        if lod_collection_name not in bpy.data.collections:
            lod_collection = bpy.data.collections.new(lod_collection_name)
            bpy.context.scene.collection.children.link(lod_collection)
        else:
            lod_collection = bpy.data.collections[lod_collection_name]

    lod_objects = []
    original_triangles = sum(len(p.vertices) - 2 for p in obj.data.polygons)

    # LOD0 is the original model
    lod_objects.append({"name": f"{obj.name}_LOD0", "triangles": original_triangles, "level": 0})

    # Copy original object as LOD0
    lod0 = obj.copy()
    lod0.data = obj.data.copy()
    lod0.name = f"{obj.name}_LOD0"
    if create_collection:
        lod_collection.objects.link(lod0)
    else:
        bpy.context.scene.collection.objects.link(lod0)

    # Generate other LOD levels
    current_ratio = 1.0
    for level in range(1, lod_levels + 1):
        current_ratio *= ratio_step

        # Copy original object
        lod_obj = obj.copy()
        lod_obj.data = obj.data.copy()
        lod_obj.name = f"{obj.name}_LOD{level}"

        if create_collection:
            lod_collection.objects.link(lod_obj)
        else:
            bpy.context.scene.collection.objects.link(lod_obj)

        # Add Decimate modifier
        decimate = lod_obj.modifiers.new(name="LOD_Decimate", type="DECIMATE")
        decimate.decimate_type = "COLLAPSE"
        decimate.ratio = current_ratio

        # Apply modifier
        _apply_modifier(lod_obj, decimate.name)

        # Calculate triangle count
        lod_triangles = sum(len(p.vertices) - 2 for p in lod_obj.data.polygons)

        lod_objects.append({"name": lod_obj.name, "triangles": lod_triangles, "level": level})

        # Offset position for viewing
        lod_obj.location.x = obj.location.x + (level * 3)

    return {
        "success": True,
        "data": {
            "original_object": obj.name,
            "lod_objects": lod_objects,
            "collection": lod_collection.name if create_collection else None,
        },
    }


def handle_smart_subdivide(params: dict[str, Any]) -> dict[str, Any]:
    """Smart subdivision

    Args:
        params:
            - object_name: Object name
            - levels: Subdivision levels
            - render_levels: Render levels
            - use_creases: Use crease edges
            - apply_smooth: Apply smooth shading
            - quality: Quality level
    """
    object_name = params.get("object_name", "")
    levels = params.get("levels", 1)
    render_levels = params.get("render_levels", levels)
    use_creases = params.get("use_creases", True)
    apply_smooth = params.get("apply_smooth", False)
    quality = params.get("quality", 3)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Select object
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # If using crease edges, auto-detect and mark sharp edges first
    if use_creases:
        if bpy.context.mode != "EDIT":
            bpy.ops.object.mode_set(mode="EDIT")

        import bmesh

        bm = bmesh.from_edit_mesh(obj.data)

        # Get or create crease layer
        crease_layer = bm.edges.layers.crease.verify()

        # Set angle threshold based on quality
        angle_threshold = {1: 60, 2: 45, 3: 30, 4: 20, 5: 10}.get(quality, 30)

        import math

        for edge in bm.edges:
            if len(edge.link_faces) == 2:
                angle = edge.calc_face_angle()
                if angle and math.degrees(angle) > angle_threshold:
                    edge[crease_layer] = 1.0

        bmesh.update_edit_mesh(obj.data)
        bpy.ops.object.mode_set(mode="OBJECT")

    # Add subdivision surface modifier
    subsurf = obj.modifiers.new(name="MCP_Subdivision", type="SUBSURF")
    subsurf.levels = levels
    subsurf.render_levels = render_levels
    subsurf.subdivision_type = "CATMULL_CLARK"
    subsurf.use_creases = use_creases
    subsurf.quality = quality

    # Apply smooth shading
    if apply_smooth:
        bpy.ops.object.shade_smooth()

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "viewport_levels": levels,
            "render_levels": render_levels,
            "modifier_name": subsurf.name,
        },
    }


def handle_auto_smooth(params: dict[str, Any]) -> dict[str, Any]:
    """Auto smooth

    Uses different implementations based on Blender version:
    - Blender < 4.1: Uses the use_auto_smooth property
    - Blender 4.1+: Uses Smooth by Angle modifier
    - Blender 5.0+: Uses Weighted Normal modifier or geometry nodes

    Args:
        params:
            - object_name: Object name
            - angle: Smooth angle threshold (degrees)
            - use_sharp_edges: Use hard edges for sharp edges
    """
    import math

    object_name = params.get("object_name", "")
    angle = params.get("angle", 30.0)
    use_sharp_edges = params.get("use_sharp_edges", True)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    if obj.type != "MESH":
        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": "Only mesh objects are supported"},
        }

    # Select object (Blender 5.x safe: ensures OBJECT mode + view-layer membership)
    select_only(obj)

    blender_version = bpy.app.version
    method_used = "unknown"
    sharp_count = 0

    # Choose implementation based on Blender version
    if blender_version >= (4, 1, 0):
        # Blender 4.1+ (including 5.0): Use WEIGHTED_NORMAL modifier
        # Note: SMOOTH_BY_ANGLE does not exist in Blender 5.0
        method_used = "weighted_normal"

        # Step 1: Set smooth shading
        for poly in obj.data.polygons:
            poly.use_smooth = True

        # Step 2: Add or update WEIGHTED_NORMAL modifier
        wn_mod = None
        for mod in obj.modifiers:
            if mod.type == "WEIGHTED_NORMAL":
                wn_mod = mod
                break

        if not wn_mod:
            wn_mod = obj.modifiers.new(name="WeightedNormal", type="WEIGHTED_NORMAL")

        if wn_mod:
            wn_mod.weight = 50  # Area weight
            wn_mod.keep_sharp = use_sharp_edges  # Whether to keep sharp edges
            wn_mod.mode = "FACE_AREA"

        # Step 3: Mark sharp edges based on angle if needed
        if use_sharp_edges:
            import bmesh

            # Ensure in object mode
            if bpy.context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            # Enter edit mode
            bpy.ops.object.mode_set(mode="EDIT")
            bm = bmesh.from_edit_mesh(obj.data)

            angle_rad = math.radians(angle)

            for edge in bm.edges:
                if len(edge.link_faces) == 2:
                    try:
                        face_angle = edge.calc_face_angle()
                        if face_angle is not None and face_angle > angle_rad:
                            edge.smooth = False  # Mark as sharp edge
                            sharp_count += 1
                        else:
                            edge.smooth = True
                    except:
                        pass

            bmesh.update_edit_mesh(obj.data)
            bpy.ops.object.mode_set(mode="OBJECT")

    else:
        # Blender < 4.1: Use legacy use_auto_smooth property
        method_used = "legacy_auto_smooth"
        try:
            # Apply smooth shading
            bpy.ops.object.shade_smooth()
            # Set auto smooth
            obj.data.use_auto_smooth = True
            obj.data.auto_smooth_angle = math.radians(angle)
        except AttributeError:
            # If property does not exist, fall back to manual settings
            for poly in obj.data.polygons:
                poly.use_smooth = True

    return {
        "success": True,
        "data": {
            "object_name": obj.name,
            "smooth_angle": angle,
            "sharp_edges_marked": sharp_count,
            "method_used": method_used,
            "blender_version": f"{blender_version[0]}.{blender_version[1]}.{blender_version[2]}",
        },
    }
