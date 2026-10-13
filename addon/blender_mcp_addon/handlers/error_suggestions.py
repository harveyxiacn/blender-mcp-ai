"""
Error suggestions utility - Enriches error responses with actionable hints.

Not a handler module. Called by executor.py to add suggestion fields.
"""

from __future__ import annotations

from typing import Any

# Error code to suggestion mapping
SUGGESTIONS: dict[str, str] = {
    # Object errors
    "OBJECT_NOT_FOUND": "Use 'blender_describe_scene' to list all objects in the scene.",
    "OBJECT_TYPE_ERROR": "Check the object type with 'blender_describe_object'. This operation may only work on mesh objects.",
    # Material errors
    "MATERIAL_NOT_FOUND": "Use 'blender_describe_scene' to see available materials.",
    "MATERIAL_ERROR": "Ensure the material exists and the object has material slots.",
    # Modifier errors
    "MODIFIER_ERROR": "Check that the target object is a mesh. Use 'blender_describe_object' to inspect it.",
    "MODIFIER_NOT_FOUND": "Use 'blender_describe_object' to see the modifier stack for this object.",
    # Scene errors
    "SCENE_NOT_FOUND": "Use 'blender_scene_list' to see all available scenes.",
    # Checkpoint errors
    "CHECKPOINT_NOT_FOUND": "Use 'blender_checkpoint_list' to see available checkpoints.",
    "CHECKPOINT_SAVE_ERROR": "Check that Blender has write access to the temp directory.",
    "CHECKPOINT_RESTORE_ERROR": "The checkpoint file may be corrupted. Try saving a new checkpoint.",
    # Snapshot errors
    "NO_VIEWPORT": "Ensure a 3D View area is open in Blender.",
    "SNAPSHOT_ERROR": "Try 'blender_snapshot_render_preview' as an alternative.",
    "RENDER_PREVIEW_ERROR": "Check that the scene has a camera set. Use 'blender_describe_scene' to verify.",
    # Parameter errors
    "MISSING_PARAM": "Check the tool documentation for required parameters.",
    "INVALID_ENUM": "Check the API reference for valid enum values.",
    "VALIDATION_ERROR": "Verify parameter types and ranges match the tool specification.",
    # Connection errors
    "CONNECTION_LOST": "Ensure Blender is running and the MCP addon is enabled.",
    "EXECUTION_ERROR": "Check Blender's system console for detailed error output.",
    # Handler errors
    "UNKNOWN_CATEGORY": "Use 'blender_activate_skill' to load additional tool categories.",
    "UNKNOWN_ACTION": "Check available actions for this category in the tool documentation.",
    # Python execution
    "PYTHON_ERROR": "Check the Python code for syntax errors. Use 'blender_describe_scene' to verify object names.",
    "SAFETY_CHECK_FAILED": "The code contains potentially unsafe operations. Review and modify accordingly.",
    # Quick tools
    "PRODUCT_SHOT_ERROR": "Ensure a target mesh object exists. Create one with 'blender_object_create'.",
    "TURNTABLE_ERROR": "Ensure the target object exists and is selectable.",
    "SCENE_SETUP_ERROR": "Try with clear_scene=true to start fresh.",
    # Describe
    "DESCRIBE_SCENE_ERROR": "The scene may be in an unexpected state. Try opening a new file.",
    "DESCRIBE_HIERARCHY_ERROR": "Try 'blender_describe_scene' for a simpler overview.",
    "DESCRIBE_OBJECT_ERROR": "The object may have been deleted. Use 'blender_describe_scene' to check.",
}

# Default suggestion for unknown error codes
DEFAULT_SUGGESTION = "Try 'blender_describe_scene' to understand the current scene state."


def enrich_error(result: dict[str, Any]) -> dict[str, Any]:
    """Add a suggestion field to error responses if not already present.

    Args:
        result: The command result dictionary.

    Returns:
        The same dictionary, potentially with an added suggestion.
    """
    if not result.get("success") and "error" in result:
        error = result["error"]
        # A handler can return a bare string by mistake. Every downstream
        # consumer expects the {code, message} envelope, so normalise it here
        # rather than letting `error.get(...)` blow up the whole call.
        if not isinstance(error, dict):
            error = {"code": "HANDLER_ERROR", "message": str(error)}
            result["error"] = error
        if "suggestion" not in error:
            code = error.get("code", "")
            error["suggestion"] = SUGGESTIONS.get(code, DEFAULT_SUGGESTION)
    return result
