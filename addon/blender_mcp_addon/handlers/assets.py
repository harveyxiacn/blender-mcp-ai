"""
Asset Management Handler

Handles Blender asset library management commands.
"""

import os
from typing import Any

import bpy


def handle_mark(params: dict[str, Any]) -> dict[str, Any]:
    """Mark as asset"""
    object_name = params.get("object_name", "")
    asset_type = params.get("asset_type", "OBJECT")
    description = params.get("description", "")
    tags = params.get("tags", [])

    try:
        if asset_type == "OBJECT":
            obj = bpy.data.objects.get(object_name)
            if not obj:
                return {
                    "success": False,
                    "error": {
                        "code": "OBJECT_NOT_FOUND",
                        "message": f"Object not found: {object_name}",
                    },
                }

            obj.asset_mark()

            if description:
                obj.asset_data.description = description

            for tag in tags:
                obj.asset_data.tags.new(tag)

            return {"success": True, "data": {"name": obj.name, "type": "OBJECT"}}

        elif asset_type == "MATERIAL":
            mat = bpy.data.materials.get(object_name)
            if not mat:
                return {
                    "success": False,
                    "error": {
                        "code": "MATERIAL_NOT_FOUND",
                        "message": f"Material not found: {object_name}",
                    },
                }

            mat.asset_mark()

            if description:
                mat.asset_data.description = description

            for tag in tags:
                mat.asset_data.tags.new(tag)

            return {"success": True, "data": {"name": mat.name, "type": "MATERIAL"}}

        elif asset_type == "WORLD":
            world = bpy.data.worlds.get(object_name)
            if not world:
                return {
                    "success": False,
                    "error": {
                        "code": "WORLD_NOT_FOUND",
                        "message": f"World not found: {object_name}",
                    },
                }

            world.asset_mark()

            return {"success": True, "data": {"name": world.name, "type": "WORLD"}}

        return {
            "success": False,
            "error": {"code": "INVALID_TYPE", "message": f"Unsupported asset type: {asset_type}"},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "ASSET_MARK_ERROR", "message": str(e)}}


def handle_catalog(params: dict[str, Any]) -> dict[str, Any]:
    """Catalog operations"""
    action = params.get("action", "LIST")
    params.get("catalog_name")
    params.get("parent_catalog")

    try:
        if action == "LIST":
            # List all assets
            assets = {"objects": [], "materials": [], "worlds": []}

            for obj in bpy.data.objects:
                if obj.asset_data:
                    assets["objects"].append(
                        {
                            "name": obj.name,
                            "description": obj.asset_data.description if obj.asset_data else "",
                        }
                    )

            for mat in bpy.data.materials:
                if mat.asset_data:
                    assets["materials"].append(
                        {
                            "name": mat.name,
                            "description": mat.asset_data.description if mat.asset_data else "",
                        }
                    )

            for world in bpy.data.worlds:
                if world.asset_data:
                    assets["worlds"].append({"name": world.name})

            return {"success": True, "data": assets}

        elif action == "CREATE":
            # Blender's asset catalogs need to be created via the Asset Browser
            return {
                "success": True,
                "data": {"note": "Catalog creation requires Asset Browser. Use Blender UI."},
            }

        elif action == "DELETE":
            return {
                "success": True,
                "data": {"note": "Catalog deletion requires Asset Browser. Use Blender UI."},
            }

        return {
            "success": False,
            "error": {"code": "INVALID_ACTION", "message": f"Unknown action: {action}"},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CATALOG_ERROR", "message": str(e)}}


def handle_import(params: dict[str, Any]) -> dict[str, Any]:
    """Import asset"""
    filepath = params.get("filepath")
    asset_name = params.get("asset_name")
    link = params.get("link", False)

    if not os.path.exists(filepath):
        return {
            "success": False,
            "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {filepath}"},
        }

    try:
        # Use bpy.ops.wm.append or link
        with bpy.data.libraries.load(filepath, link=link) as (data_from, data_to):
            # Try to import objects
            if asset_name in data_from.objects:
                data_to.objects = [asset_name]
            # Try to import materials
            elif asset_name in data_from.materials:
                data_to.materials = [asset_name]
            # Try to import collections
            elif asset_name in data_from.collections:
                data_to.collections = [asset_name]
            else:
                return {
                    "success": False,
                    "error": {
                        "code": "ASSET_NOT_FOUND",
                        "message": f"Asset not found: {asset_name}",
                    },
                }

        # Link to scene
        for obj in data_to.objects:
            if obj:
                bpy.context.collection.objects.link(obj)

        for coll in data_to.collections:
            if coll:
                bpy.context.scene.collection.children.link(coll)

        return {"success": True, "data": {"asset_name": asset_name, "linked": link}}

    except Exception as e:
        return {"success": False, "error": {"code": "IMPORT_ERROR", "message": str(e)}}


def handle_search(params: dict[str, Any]) -> dict[str, Any]:
    """Search assets"""
    query = params.get("query", "").lower()
    asset_type = params.get("asset_type")

    try:
        results = []

        if not asset_type or asset_type == "OBJECT":
            for obj in bpy.data.objects:
                if obj.asset_data and query in obj.name.lower():
                    results.append(
                        {
                            "name": obj.name,
                            "type": "OBJECT",
                            "description": obj.asset_data.description if obj.asset_data else "",
                        }
                    )

        if not asset_type or asset_type == "MATERIAL":
            for mat in bpy.data.materials:
                if mat.asset_data and query in mat.name.lower():
                    results.append(
                        {
                            "name": mat.name,
                            "type": "MATERIAL",
                            "description": mat.asset_data.description if mat.asset_data else "",
                        }
                    )

        if not asset_type or asset_type == "WORLD":
            for world in bpy.data.worlds:
                if world.asset_data and query in world.name.lower():
                    results.append({"name": world.name, "type": "WORLD"})

        return {
            "success": True,
            "data": {"query": query, "results": results, "count": len(results)},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "SEARCH_ERROR", "message": str(e)}}


def handle_preview(params: dict[str, Any]) -> dict[str, Any]:
    """Generate asset preview"""
    object_name = params.get("object_name", "")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        if not obj.asset_data:
            return {
                "success": False,
                "error": {"code": "NOT_ASSET", "message": "Object is not marked as an asset"},
            }

        # Generate preview
        obj.asset_generate_preview()

        return {"success": True, "data": {"name": obj.name, "preview_generated": True}}

    except Exception as e:
        return {"success": False, "error": {"code": "PREVIEW_ERROR", "message": str(e)}}


def handle_clear(params: dict[str, Any]) -> dict[str, Any]:
    """Clear asset marking"""
    object_name = params.get("object_name")

    # Try to find in different data blocks
    data_block = None

    if object_name in bpy.data.objects:
        data_block = bpy.data.objects[object_name]
    elif object_name in bpy.data.materials:
        data_block = bpy.data.materials[object_name]
    elif object_name in bpy.data.worlds:
        data_block = bpy.data.worlds[object_name]

    if not data_block:
        return {
            "success": False,
            "error": {"code": "NOT_FOUND", "message": f"Not found: {object_name}"},
        }

    try:
        if data_block.asset_data:
            data_block.asset_clear()

            return {"success": True, "data": {"name": object_name, "cleared": True}}
        else:
            return {"success": True, "data": {"name": object_name, "note": "Not an asset"}}

    except Exception as e:
        return {"success": False, "error": {"code": "CLEAR_ERROR", "message": str(e)}}
