"""
External Integration Handler

Handles commands for integration with external tools (Unity, Unreal, etc.).
"""

import os
from typing import Any

import bpy


def _select_objects(object_names: list[str] = None) -> None:
    """Select specified objects"""
    bpy.ops.object.select_all(action="DESELECT")

    if object_names:
        for name in object_names:
            obj = bpy.data.objects.get(name)
            if obj:
                obj.select_set(True)
    else:
        # Select all visible mesh objects
        for obj in bpy.context.view_layer.objects:
            if obj.type in ("MESH", "ARMATURE", "CURVE"):
                obj.select_set(True)


def handle_unity_export(params: dict[str, Any]) -> dict[str, Any]:
    """Unity export"""
    filepath = params.get("filepath")
    objects = params.get("objects")
    apply_modifiers = params.get("apply_modifiers", True)
    apply_scale = params.get("apply_scale", True)
    export_animations = params.get("export_animations", True)
    bake_animation = params.get("bake_animation", False)

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        _select_objects(objects)

        # Unity FBX export settings
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=bool(objects),
            apply_scale_options="FBX_SCALE_ALL" if apply_scale else "FBX_SCALE_NONE",
            use_mesh_modifiers=apply_modifiers,
            bake_anim=export_animations,
            bake_anim_use_all_actions=export_animations,
            bake_anim_use_nla_strips=export_animations,
            bake_anim_force_startend_keying=bake_animation,
            # Unity-specific settings
            axis_forward="-Z",
            axis_up="Y",
            global_scale=1.0,
            apply_unit_scale=True,
            # Geometry settings
            mesh_smooth_type="FACE",
            use_mesh_edges=False,
            use_triangles=False,
            use_tspace=True,
            # Armature settings
            add_leaf_bones=False,
            primary_bone_axis="Y",
            secondary_bone_axis="X",
            use_armature_deform_only=True,
        )

        return {"success": True, "data": {"filepath": filepath, "target": "Unity"}}

    except Exception as e:
        return {"success": False, "error": {"code": "UNITY_EXPORT_ERROR", "message": str(e)}}


def handle_unreal_export(params: dict[str, Any]) -> dict[str, Any]:
    """Unreal export"""
    filepath = params.get("filepath")
    objects = params.get("objects")
    export_animations = params.get("export_animations", True)
    smoothing = params.get("smoothing", "FACE")
    use_tspace = params.get("use_tspace", True)

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        _select_objects(objects)

        # Unreal FBX export settings
        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=bool(objects),
            apply_scale_options="FBX_SCALE_ALL",
            use_mesh_modifiers=True,
            bake_anim=export_animations,
            bake_anim_use_all_actions=export_animations,
            # Unreal-specific settings
            axis_forward="X",
            axis_up="Z",
            global_scale=1.0,
            apply_unit_scale=True,
            # Geometry settings
            mesh_smooth_type=smoothing,
            use_mesh_edges=False,
            use_triangles=False,
            use_tspace=use_tspace,
            # Armature settings
            add_leaf_bones=False,
            primary_bone_axis="Y",
            secondary_bone_axis="X",
            use_armature_deform_only=True,
            # Other
            batch_mode="OFF",
            use_metadata=True,
        )

        return {"success": True, "data": {"filepath": filepath, "target": "Unreal"}}

    except Exception as e:
        return {"success": False, "error": {"code": "UNREAL_EXPORT_ERROR", "message": str(e)}}


def handle_godot_export(params: dict[str, Any]) -> dict[str, Any]:
    """Godot export"""
    filepath = params.get("filepath")
    objects = params.get("objects")
    export_format = params.get("export_format", "GLTF")

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        _select_objects(objects)

        # Ensure correct file extension
        if export_format == "GLB":
            if not filepath.lower().endswith(".glb"):
                filepath = os.path.splitext(filepath)[0] + ".glb"
            export_format_enum = "GLB"
        else:
            if not filepath.lower().endswith(".gltf"):
                filepath = os.path.splitext(filepath)[0] + ".gltf"
            export_format_enum = "GLTF_SEPARATE"

        # Godot GLTF export settings
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            use_selection=bool(objects),
            export_format=export_format_enum,
            # Godot-specific settings
            export_apply=True,
            export_animations=True,
            export_materials="EXPORT",
            export_colors=True,
            export_cameras=False,
            export_lights=False,
            # Transform settings
            export_yup=True,
        )

        return {
            "success": True,
            "data": {"filepath": filepath, "target": "Godot", "format": export_format},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "GODOT_EXPORT_ERROR", "message": str(e)}}


def handle_batch_export(params: dict[str, Any]) -> dict[str, Any]:
    """Batch export"""
    output_dir = params.get("output_dir")
    format = params.get("format", "FBX")
    separate_files = params.get("separate_files", True)
    objects = params.get("objects")

    try:
        os.makedirs(output_dir, exist_ok=True)

        # Get objects to export
        if objects:
            export_objects = [
                bpy.data.objects.get(name) for name in objects if bpy.data.objects.get(name)
            ]
        else:
            export_objects = [obj for obj in bpy.context.view_layer.objects if obj.type == "MESH"]

        exported_files = []

        if separate_files:
            # Export each object separately
            for obj in export_objects:
                bpy.ops.object.select_all(action="DESELECT")
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                filename = f"{obj.name}.{format.lower()}"
                filepath = os.path.join(output_dir, filename)

                if format == "FBX":
                    bpy.ops.export_scene.fbx(
                        filepath=filepath, use_selection=True, use_mesh_modifiers=True
                    )
                elif format == "GLTF":
                    bpy.ops.export_scene.gltf(
                        filepath=filepath, use_selection=True, export_format="GLTF_SEPARATE"
                    )
                elif format == "OBJ":
                    bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)

                exported_files.append(filepath)
        else:
            # Export all objects to a single file
            _select_objects([obj.name for obj in export_objects])

            filename = f"export_all.{format.lower()}"
            filepath = os.path.join(output_dir, filename)

            if format == "FBX":
                bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True)
            elif format == "GLTF":
                bpy.ops.export_scene.gltf(filepath=filepath, use_selection=True)
            elif format == "OBJ":
                bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)

            exported_files.append(filepath)

        return {
            "success": True,
            "data": {
                "output_dir": output_dir,
                "exported_files": exported_files,
                "count": len(exported_files),
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "BATCH_EXPORT_ERROR", "message": str(e)}}


def handle_collection_export(params: dict[str, Any]) -> dict[str, Any]:
    """Collection export"""
    collection_name = params.get("collection_name", "")
    filepath = params.get("filepath")
    format = params.get("format", "FBX")

    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return {
            "success": False,
            "error": {
                "code": "COLLECTION_NOT_FOUND",
                "message": f"Collection not found: {collection_name}",
            },
        }

    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Select all objects in the collection
        bpy.ops.object.select_all(action="DESELECT")
        for obj in collection.objects:
            obj.select_set(True)

        if format == "FBX":
            bpy.ops.export_scene.fbx(filepath=filepath, use_selection=True, use_mesh_modifiers=True)
        elif format == "GLTF":
            bpy.ops.export_scene.gltf(
                filepath=filepath,
                use_selection=True,
                export_format="GLTF_SEPARATE" if filepath.lower().endswith(".gltf") else "GLB",
            )
        elif format == "OBJ":
            bpy.ops.wm.obj_export(filepath=filepath, export_selected_objects=True)

        return {
            "success": True,
            "data": {
                "collection": collection_name,
                "filepath": filepath,
                "format": format,
                "objects_count": len(collection.objects),
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "COLLECTION_EXPORT_ERROR", "message": str(e)}}
