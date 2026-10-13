"""
Preferences Handler

Handles Blender preferences management commands.
"""

from typing import Any

import bpy


def handle_get(params: dict[str, Any]) -> dict[str, Any]:
    """Get settings"""
    category = params.get("category")
    key = params.get("key")

    try:
        prefs = bpy.context.preferences

        category_map = {
            "view": prefs.view,
            "system": prefs.system,
            "edit": prefs.edit,
            "input": prefs.inputs,
            "filepaths": prefs.filepaths,
            "addons": prefs.addons,
        }

        if category not in category_map:
            return {
                "success": False,
                "error": {"code": "INVALID_CATEGORY", "message": f"Invalid category: {category}"},
            }

        cat_prefs = category_map[category]

        # If no key specified, return all available settings for this category
        if key is None:
            available_keys = [
                attr
                for attr in dir(cat_prefs)
                if not attr.startswith("_") and not callable(getattr(cat_prefs, attr, None))
            ]
            return {
                "success": True,
                "data": {"category": category, "available_keys": available_keys},
            }

        if hasattr(cat_prefs, key):
            value = getattr(cat_prefs, key)
            # Convert to serializable value
            if hasattr(value, "__iter__") and not isinstance(value, str):
                value = list(value)

            return {"success": True, "data": {"category": category, "key": key, "value": value}}
        else:
            return {
                "success": False,
                "error": {"code": "KEY_NOT_FOUND", "message": f"Key not found: {key}"},
            }

    except Exception as e:
        return {"success": False, "error": {"code": "GET_ERROR", "message": str(e)}}


def handle_set(params: dict[str, Any]) -> dict[str, Any]:
    """Set preferences"""
    category = params.get("category")
    key = params.get("key")
    value = params.get("value")

    try:
        prefs = bpy.context.preferences

        category_map = {
            "view": prefs.view,
            "system": prefs.system,
            "edit": prefs.edit,
            "input": prefs.inputs,
            "filepaths": prefs.filepaths,
        }

        if category not in category_map:
            return {
                "success": False,
                "error": {"code": "INVALID_CATEGORY", "message": f"Invalid category: {category}"},
            }

        cat_prefs = category_map[category]

        if hasattr(cat_prefs, key):
            setattr(cat_prefs, key, value)

            return {"success": True, "data": {"category": category, "key": key, "value": value}}
        else:
            return {
                "success": False,
                "error": {"code": "KEY_NOT_FOUND", "message": f"Key not found: {key}"},
            }

    except Exception as e:
        return {"success": False, "error": {"code": "SET_ERROR", "message": str(e)}}


def handle_theme(params: dict[str, Any]) -> dict[str, Any]:
    """Theme settings"""
    preset = params.get("preset", "")
    custom_colors = params.get("custom_colors")

    try:
        if preset:
            # Load preset theme
            # Blender 5.0 theme presets
            preset_map = {"Dark": "blender_dark", "Light": "blender_light", "Default": "Default"}

            preset_name = preset_map.get(preset, preset)

            try:
                bpy.ops.script.execute_preset(
                    filepath=f"//presets/interface_theme/{preset_name}.xml",
                    menu_idname="USERPREF_MT_interface_theme_presets",
                )
            except:
                # If preset doesn't exist, try to set basic colors
                pass

        if custom_colors:
            theme = bpy.context.preferences.themes[0]

            # Apply custom colors
            if "background" in custom_colors:
                theme.view_3d.space.gradients.high_gradient = custom_colors["background"][:3]

            if "text" in custom_colors:
                theme.user_interface.wcol_regular.text = custom_colors["text"][:3]

            if "accent" in custom_colors:
                theme.user_interface.wcol_state.inner_sel = custom_colors["accent"][:4]

        return {
            "success": True,
            "data": {"preset": preset, "custom_colors_applied": bool(custom_colors)},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "THEME_ERROR", "message": str(e)}}


def handle_viewport(params: dict[str, Any]) -> dict[str, Any]:
    """Viewport settings"""
    show_gizmo = params.get("show_gizmo")
    show_floor = params.get("show_floor")
    show_axis_x = params.get("show_axis_x")
    show_axis_y = params.get("show_axis_y")
    show_axis_z = params.get("show_axis_z")
    clip_start = params.get("clip_start")
    clip_end = params.get("clip_end")

    try:
        # Get current 3D viewport
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active

                if show_gizmo is not None:
                    space.show_gizmo = show_gizmo

                overlay = space.overlay

                if show_floor is not None:
                    overlay.show_floor = show_floor

                if show_axis_x is not None:
                    overlay.show_axis_x = show_axis_x

                if show_axis_y is not None:
                    overlay.show_axis_y = show_axis_y

                if show_axis_z is not None:
                    overlay.show_axis_z = show_axis_z

                if clip_start is not None:
                    space.clip_start = clip_start

                if clip_end is not None:
                    space.clip_end = clip_end

                break

        return {"success": True, "data": {"viewport_updated": True}}

    except Exception as e:
        return {"success": False, "error": {"code": "VIEWPORT_ERROR", "message": str(e)}}


def handle_system(params: dict[str, Any]) -> dict[str, Any]:
    """System settings"""
    memory_cache_limit = params.get("memory_cache_limit")
    undo_steps = params.get("undo_steps")
    use_gpu_subdivision = params.get("use_gpu_subdivision")

    try:
        prefs = bpy.context.preferences

        if memory_cache_limit is not None:
            prefs.system.memory_cache_limit = memory_cache_limit

        if undo_steps is not None:
            prefs.edit.undo_steps = undo_steps

        if use_gpu_subdivision is not None:
            prefs.system.use_gpu_subdivision = use_gpu_subdivision

        return {"success": True, "data": {"system_updated": True}}

    except Exception as e:
        return {"success": False, "error": {"code": "SYSTEM_ERROR", "message": str(e)}}


def handle_save(params: dict[str, Any]) -> dict[str, Any]:
    """Save preferences"""
    try:
        bpy.ops.wm.save_userpref()

        return {"success": True, "data": {"saved": True}}

    except Exception as e:
        return {"success": False, "error": {"code": "SAVE_ERROR", "message": str(e)}}


def handle_load_factory(params: dict[str, Any]) -> dict[str, Any]:
    """Load factory settings"""
    try:
        bpy.ops.wm.read_factory_userpref()

        return {"success": True, "data": {"factory_loaded": True}}

    except Exception as e:
        return {"success": False, "error": {"code": "FACTORY_ERROR", "message": str(e)}}
