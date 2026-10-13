"""
Render Handler

Handles rendering-related commands.
"""

import os
import tempfile
from typing import Any

import bpy

from .compat import is_eevee_engine, normalize_engine_name


def handle_settings(params: dict[str, Any]) -> dict[str, Any]:
    """Set render parameters"""
    scene = bpy.context.scene
    render = scene.render

    if "engine" in params:
        render.engine = params["engine"]

    if "resolution_x" in params:
        render.resolution_x = params["resolution_x"]

    if "resolution_y" in params:
        render.resolution_y = params["resolution_y"]

    if "resolution_percentage" in params:
        render.resolution_percentage = params["resolution_percentage"]

    if "samples" in params:
        if render.engine == "CYCLES":
            scene.cycles.samples = params["samples"]
        elif is_eevee_engine(render.engine):
            scene.eevee.taa_render_samples = params["samples"]

    if "use_denoising" in params and render.engine == "CYCLES":
        scene.cycles.use_denoising = params["use_denoising"]

    if "file_format" in params:
        render.image_settings.file_format = params["file_format"]

    if "output_path" in params:
        render.filepath = params["output_path"]

    return {"success": True, "data": {}}


def handle_image(params: dict[str, Any]) -> dict[str, Any]:
    """Render image"""
    output_path = params.get("output_path")
    frame = params.get("frame")
    camera = params.get("camera", "")
    write_still = params.get("write_still", True)

    scene = bpy.context.scene

    # Set frame
    if frame is not None:
        scene.frame_set(frame)

    # Set camera
    if camera:
        cam_obj = bpy.data.objects.get(camera)
        if cam_obj and cam_obj.type == "CAMERA":
            scene.camera = cam_obj

    # Set output path
    if output_path:
        scene.render.filepath = output_path
    elif not scene.render.filepath:
        scene.render.filepath = os.path.join(tempfile.gettempdir(), "render.png")

    # Render
    import time

    start_time = time.time()

    bpy.ops.render.render(write_still=write_still)

    render_time = time.time() - start_time

    return {
        "success": True,
        "data": {
            "output_path": scene.render.filepath,
            "render_time": round(render_time, 2),
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
        },
    }


def handle_animation(params: dict[str, Any]) -> dict[str, Any]:
    """Render animation"""
    output_path = params.get("output_path")
    frame_start = params.get("frame_start")
    frame_end = params.get("frame_end")
    frame_step = params.get("frame_step", 1)

    scene = bpy.context.scene

    # Set frame range
    if frame_start is not None:
        scene.frame_start = frame_start
    if frame_end is not None:
        scene.frame_end = frame_end

    scene.frame_step = frame_step

    # Set output path
    if output_path:
        scene.render.filepath = output_path

    # Render animation
    bpy.ops.render.render(animation=True)

    frames_rendered = (scene.frame_end - scene.frame_start + 1) // frame_step

    return {
        "success": True,
        "data": {"output_path": scene.render.filepath, "frames_rendered": frames_rendered},
    }


def handle_preview(params: dict[str, Any]) -> dict[str, Any]:
    """Render preview"""
    resolution_percentage = params.get("resolution_percentage", 50)
    samples = params.get("samples", 32)

    scene = bpy.context.scene
    render = scene.render

    # Save original settings
    orig_res_pct = render.resolution_percentage
    orig_samples = None

    if render.engine == "CYCLES":
        orig_samples = scene.cycles.samples
        scene.cycles.samples = samples

    # Set preview parameters
    render.resolution_percentage = resolution_percentage

    # Render
    bpy.ops.render.render()

    # Restore settings
    render.resolution_percentage = orig_res_pct
    if orig_samples is not None:
        scene.cycles.samples = orig_samples

    return {"success": True, "data": {}}


def handle_set_engine(params: dict[str, Any]) -> dict[str, Any]:
    """Set render engine"""
    engine = params.get("engine", "CYCLES")

    scene = bpy.context.scene

    # Accept both BLENDER_EEVEE and BLENDER_EEVEE_NEXT and map to the
    # correct name for the running Blender version.
    engine = normalize_engine_name(engine)

    # Valid engine list
    valid_engines = ["CYCLES", "BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"]

    if engine not in valid_engines:
        return {
            "success": False,
            "error": {
                "code": "INVALID_ENGINE",
                "message": f"Invalid render engine: {engine}. Valid values: {valid_engines}",
            },
        }

    scene.render.engine = engine

    return {"success": True, "data": {"engine": scene.render.engine}}


def handle_set_resolution(params: dict[str, Any]) -> dict[str, Any]:
    """Set render resolution"""
    width = params.get("width", 1920)
    height = params.get("height", 1080)
    percentage = params.get("percentage", 100)

    scene = bpy.context.scene
    render = scene.render

    render.resolution_x = width
    render.resolution_y = height
    render.resolution_percentage = percentage

    return {
        "success": True,
        "data": {
            "width": render.resolution_x,
            "height": render.resolution_y,
            "percentage": render.resolution_percentage,
        },
    }


def handle_set_samples(params: dict[str, Any]) -> dict[str, Any]:
    """Set render samples"""
    samples = params.get("samples", 128)

    scene = bpy.context.scene
    render = scene.render

    if render.engine == "CYCLES":
        scene.cycles.samples = samples
        actual_samples = scene.cycles.samples
    elif is_eevee_engine(render.engine):
        scene.eevee.taa_render_samples = samples
        actual_samples = scene.eevee.taa_render_samples
    else:
        actual_samples = samples

    return {"success": True, "data": {"samples": actual_samples, "engine": render.engine}}


def handle_get_viewport_screenshot(params: dict[str, Any]) -> dict[str, Any]:
    """Get viewport screenshot

    Uses offscreen rendering or direct viewport rendering.
    Optimized implementation for Blender 5.0+.

    Args:
        params:
            - output_path: Output path (optional, uses temp directory if not provided)
            - width: Screenshot width (default 800)
            - height: Screenshot height (default 600)
            - view_type: View type ('PERSP', 'FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM')

    Returns:
        Screenshot file path and information
    """
    import base64

    output_path = params.get("output_path")
    width = params.get("width", 800)
    height = params.get("height", 600)
    view_type = params.get("view_type")
    return_base64 = params.get("return_base64", False)

    # Determine output path
    if not output_path:
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(tempfile.gettempdir(), f"blender_viewport_{timestamp}.png")

    scene = bpy.context.scene

    # Save original settings
    orig_res_x = scene.render.resolution_x
    orig_res_y = scene.render.resolution_y
    orig_res_pct = scene.render.resolution_percentage
    orig_filepath = scene.render.filepath
    orig_file_format = scene.render.image_settings.file_format

    try:
        # Set render resolution
        scene.render.resolution_x = width
        scene.render.resolution_y = height
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = output_path

        # Method 1: Try to get 3D viewport directly from screen.areas
        area = None
        region = None

        # Prefer using current screen's areas
        if hasattr(bpy.context, "screen") and bpy.context.screen:
            for a in bpy.context.screen.areas:
                if a.type == "VIEW_3D":
                    area = a
                    for r in a.regions:
                        if r.type == "WINDOW":
                            region = r
                            break
                    break

        # If not found, iterate through all windows
        if not area:
            for window in bpy.context.window_manager.windows:
                for a in window.screen.areas:
                    if a.type == "VIEW_3D":
                        area = a
                        for r in a.regions:
                            if r.type == "WINDOW":
                                region = r
                                break
                        break
                if area:
                    break

        if not area or not region:
            return {
                "success": False,
                "error": {"code": "NO_3D_VIEW", "message": "3D viewport not found"},
            }

        # If view type specified, switch view
        if view_type:
            for space in area.spaces:
                if space.type == "VIEW_3D":
                    region_3d = space.region_3d

                    view_types_map = {
                        "PERSP": "PERSP",
                        "FRONT": "ORTHO",
                        "BACK": "ORTHO",
                        "LEFT": "ORTHO",
                        "RIGHT": "ORTHO",
                        "TOP": "ORTHO",
                        "BOTTOM": "ORTHO",
                    }

                    if view_type.upper() in view_types_map:
                        region_3d.view_perspective = view_types_map[view_type.upper()]
                    break

        # Try multiple methods to take screenshot
        success = False
        error_msg = ""

        # Method 1: Use temp_override (Blender 3.2+)
        try:
            with bpy.context.temp_override(area=area, region=region):
                bpy.ops.render.opengl(write_still=True)
            success = True
        except Exception as e1:
            error_msg = f"temp_override method failed: {str(e1)}"

            # Method 2: Use standard render instead of viewport render
            try:
                # Use Workbench engine for fast render
                orig_engine = scene.render.engine
                scene.render.engine = "BLENDER_WORKBENCH"
                bpy.ops.render.render(write_still=True)
                scene.render.engine = orig_engine
                success = True
            except Exception as e2:
                error_msg += f"; Standard render method failed: {str(e2)}"

                # Method 3: Save render result image
                try:
                    if "Render Result" in bpy.data.images:
                        bpy.data.images["Render Result"].save_render(output_path)
                        success = True
                except Exception as e3:
                    error_msg += f"; Save render result failed: {str(e3)}"

        # Check if file was created
        if success and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)

            screenshot_base64 = None
            if return_base64:
                with open(output_path, "rb") as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode("utf-8")

            return {
                "success": True,
                "data": {
                    "output_path": output_path,
                    "width": width,
                    "height": height,
                    "file_size": file_size,
                    "base64": screenshot_base64,
                },
            }
        else:
            return {
                "success": False,
                "error": {
                    "code": "SCREENSHOT_FAILED",
                    "message": (
                        f"Screenshot failed: {error_msg}"
                        if error_msg
                        else "Screenshot file was not created"
                    ),
                },
            }

    except Exception as e:
        return {"success": False, "error": {"code": "SCREENSHOT_ERROR", "message": str(e)}}

    finally:
        # Restore original settings
        scene.render.resolution_x = orig_res_x
        scene.render.resolution_y = orig_res_y
        scene.render.resolution_percentage = orig_res_pct
        scene.render.filepath = orig_filepath
        scene.render.image_settings.file_format = orig_file_format
