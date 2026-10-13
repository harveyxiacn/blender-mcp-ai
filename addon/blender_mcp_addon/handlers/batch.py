"""
Batch processing handler

Handles batch material, transform, rename, export and related commands.
"""

import fnmatch
import os
from typing import Any

import bpy


def _get_matching_objects(pattern: str) -> list[bpy.types.Object]:
    """Get objects matching the pattern"""
    matching = []
    for obj in bpy.data.objects:
        if fnmatch.fnmatch(obj.name, pattern):
            matching.append(obj)
    return matching


def handle_apply_material(params: dict[str, Any]) -> dict[str, Any]:
    """Batch apply material"""
    pattern = params.get("pattern")
    material_name = params.get("material_name", "")
    replace_existing = params.get("replace_existing", True)

    material = bpy.data.materials.get(material_name)
    if not material:
        return {
            "success": False,
            "error": {
                "code": "MATERIAL_NOT_FOUND",
                "message": f"Material not found: {material_name}",
            },
        }

    objects = _get_matching_objects(pattern)
    affected = 0

    for obj in objects:
        if obj.type != "MESH":
            continue

        if replace_existing:
            obj.data.materials.clear()

        obj.data.materials.append(material)
        affected += 1

    return {"success": True, "data": {"objects_affected": affected}}


def handle_transform(params: dict[str, Any]) -> dict[str, Any]:
    """Batch transform"""
    pattern = params.get("pattern")
    location_offset = params.get("location_offset")
    rotation_offset = params.get("rotation_offset")
    scale_factor = params.get("scale_factor")

    objects = _get_matching_objects(pattern)
    affected = 0

    for obj in objects:
        if location_offset:
            obj.location[0] += location_offset[0]
            obj.location[1] += location_offset[1]
            obj.location[2] += location_offset[2]

        if rotation_offset:
            obj.rotation_euler[0] += rotation_offset[0]
            obj.rotation_euler[1] += rotation_offset[1]
            obj.rotation_euler[2] += rotation_offset[2]

        if scale_factor:
            obj.scale[0] *= scale_factor[0]
            obj.scale[1] *= scale_factor[1]
            obj.scale[2] *= scale_factor[2]

        affected += 1

    return {"success": True, "data": {"objects_affected": affected}}


def handle_rename(params: dict[str, Any]) -> dict[str, Any]:
    """Batch rename"""
    pattern = params.get("pattern")
    new_name = params.get("new_name")
    numbering = params.get("numbering", True)
    start_number = params.get("start_number", 1)

    objects = _get_matching_objects(pattern)
    renamed = 0

    for i, obj in enumerate(objects):
        if numbering:
            obj.name = f"{new_name}_{start_number + i:03d}"
        else:
            obj.name = new_name
        renamed += 1

    return {"success": True, "data": {"objects_renamed": renamed}}


def handle_delete(params: dict[str, Any]) -> dict[str, Any]:
    """Batch delete"""
    pattern = params.get("pattern")
    delete_data = params.get("delete_data", True)

    objects = _get_matching_objects(pattern)
    deleted = 0

    for obj in list(objects):
        data = obj.data if delete_data else None
        bpy.data.objects.remove(obj, do_unlink=True)

        if data:
            try:
                if isinstance(data, bpy.types.Mesh):
                    bpy.data.meshes.remove(data)
                elif isinstance(data, bpy.types.Curve):
                    bpy.data.curves.remove(data)
            except:
                pass

        deleted += 1

    return {"success": True, "data": {"objects_deleted": deleted}}


def handle_export(params: dict[str, Any]) -> dict[str, Any]:
    """Batch export"""
    pattern = params.get("pattern")
    export_path = params.get("export_path")
    format_type = params.get("format", "fbx")
    individual_files = params.get("individual_files", True)

    # Ensure directory exists
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    objects = _get_matching_objects(pattern)
    exported = 0

    if individual_files:
        # Export each object individually
        for obj in objects:
            if obj.type != "MESH":
                continue

            # Select object
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            filepath = os.path.join(export_path, f"{obj.name}.{format_type}")

            try:
                if format_type == "fbx":
                    bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True)
                elif format_type == "obj":
                    bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
                elif format_type == "gltf":
                    bpy.ops.export_scene.gltf(
                        filepath=filepath, use_selection=True, export_format="GLB"
                    )
                exported += 1
            except Exception as e:
                print(f"Failed to export {obj.name}: {e}")
    else:
        # Export all objects together
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            if obj.type == "MESH":
                obj.select_set(True)

        filepath = os.path.join(export_path, f"batch_export.{format_type}")

        try:
            if format_type == "fbx":
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True)
            elif format_type == "obj":
                bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)
            elif format_type == "gltf":
                bpy.ops.export_scene.gltf(
                    filepath=filepath, use_selection=True, export_format="GLB"
                )
            exported = 1
        except Exception as e:
            return {"success": False, "error": {"code": "EXPORT_ERROR", "message": str(e)}}

    return {"success": True, "data": {"files_exported": exported}}


def handle_add_modifier(params: dict[str, Any]) -> dict[str, Any]:
    """Batch add modifier"""
    pattern = params.get("pattern")
    modifier_type = params.get("modifier_type")
    settings = params.get("settings", {})

    objects = _get_matching_objects(pattern)
    added = 0

    for obj in objects:
        if obj.type != "MESH":
            continue

        modifier = obj.modifiers.new(name=modifier_type, type=modifier_type)

        # Apply settings
        for key, value in settings.items():
            if hasattr(modifier, key):
                setattr(modifier, key, value)

        added += 1

    return {"success": True, "data": {"modifiers_added": added}}


def handle_set_parent(params: dict[str, Any]) -> dict[str, Any]:
    """Batch set parent"""
    pattern = params.get("pattern")
    parent_name = params.get("parent_name", "")
    keep_transform = params.get("keep_transform", True)

    parent = bpy.data.objects.get(parent_name)
    if not parent:
        return {
            "success": False,
            "error": {
                "code": "PARENT_NOT_FOUND",
                "message": f"Parent object not found: {parent_name}",
            },
        }

    objects = _get_matching_objects(pattern)
    parented = 0

    for obj in objects:
        if obj == parent:
            continue

        if keep_transform:
            obj.parent = parent
            obj.matrix_parent_inverse = parent.matrix_world.inverted()
        else:
            obj.parent = parent

        parented += 1

    return {"success": True, "data": {"objects_parented": parented}}
