"""
VR/AR Scene Handler

Handles VR/AR scene configuration and export commands.
"""

import contextlib
import os
from typing import Any

import bpy

from .node_utils import find_principled_bsdf as get_principled_bsdf


def handle_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Configure VR scene"""
    xr_runtime = params.get("xr_runtime", "OPENXR")
    floor_height = params.get("floor_height", 0.0)

    try:
        scene = bpy.context.scene

        # Set units to meters
        scene.unit_settings.system = "METRIC"
        scene.unit_settings.scale_length = 1.0

        # Create floor
        bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, floor_height))
        floor = bpy.context.active_object
        floor.name = "VR_Floor"

        # Create VR origin marker
        bpy.ops.object.empty_add(type="ARROWS", location=(0, 0, floor_height))
        origin = bpy.context.active_object
        origin.name = "VR_Origin"
        origin.empty_display_size = 0.5

        # Try to enable VR addon
        with contextlib.suppress(BaseException):
            bpy.ops.preferences.addon_enable(module="viewport_vr_preview")

        return {
            "success": True,
            "data": {
                "xr_runtime": xr_runtime,
                "floor_height": floor_height,
                "floor_object": floor.name,
                "origin_object": origin.name,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "VR_SETUP_ERROR", "message": str(e)}}


def handle_camera(params: dict[str, Any]) -> dict[str, Any]:
    """Create VR camera"""
    camera_type = params.get("camera_type", "stereo")
    ipd = params.get("ipd", 0.064)  # 64mm default interpupillary distance
    convergence_distance = params.get("convergence_distance", 1.95)
    location = params.get("location", [0, 0, 1.7])

    try:
        # Create camera
        bpy.ops.object.camera_add(location=location)
        camera = bpy.context.active_object
        camera.name = "VR_Camera"

        cam_data = camera.data

        if camera_type == "panorama":
            # Panorama camera settings
            cam_data.type = "PANO"
            cam_data.cycles.panorama_type = "EQUIRECTANGULAR"
            cam_data.stereo.convergence_distance = convergence_distance
            cam_data.stereo.interocular_distance = ipd
        else:
            # Stereo camera settings
            cam_data.type = "PERSP"
            cam_data.stereo.convergence_mode = "OFFAXIS"
            cam_data.stereo.convergence_distance = convergence_distance
            cam_data.stereo.interocular_distance = ipd

        # Set as active camera
        bpy.context.scene.camera = camera

        # Enable stereo 3D
        bpy.context.scene.render.use_multiview = True
        bpy.context.scene.render.views_format = "STEREO_3D"

        return {
            "success": True,
            "data": {
                "camera_name": camera.name,
                "camera_type": camera_type,
                "ipd": ipd,
                "convergence_distance": convergence_distance,
                "location": location,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "VR_CAMERA_ERROR", "message": str(e)}}


def handle_export(params: dict[str, Any]) -> dict[str, Any]:
    """Export to VR format"""
    filepath = params.get("filepath")
    format = params.get("format", "GLB")
    include_animations = params.get("include_animations", True)
    params.get("compress", True)

    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Ensure correct file extension
        if format == "GLB":
            if not filepath.lower().endswith(".glb"):
                filepath = os.path.splitext(filepath)[0] + ".glb"
            export_format = "GLB"
        else:
            if not filepath.lower().endswith(".gltf"):
                filepath = os.path.splitext(filepath)[0] + ".gltf"
            export_format = "GLTF_SEPARATE"

        # Export glTF
        bpy.ops.export_scene.gltf(
            filepath=filepath,
            export_format=export_format,
            export_animations=include_animations,
            # VR optimized settings
            export_apply=True,
            export_materials="EXPORT",
            export_colors=True,
            export_cameras=True,
            export_lights=True,
            # KHR extensions
            export_extras=True,
            export_yup=True,
        )

        return {
            "success": True,
            "data": {
                "filepath": filepath,
                "format": format,
                "include_animations": include_animations,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "VR_EXPORT_ERROR", "message": str(e)}}


def handle_ar_marker(params: dict[str, Any]) -> dict[str, Any]:
    """Create AR marker point"""
    marker_name = params.get("marker_name")
    marker_type = params.get("marker_type", "image")
    position = params.get("position", [0, 0, 0])
    size = params.get("size", 0.1)

    try:
        # Create marker plane
        bpy.ops.mesh.primitive_plane_add(size=size, location=position)
        marker = bpy.context.active_object
        marker.name = f"AR_Marker_{marker_name}"

        # Add custom properties
        marker["ar_marker_type"] = marker_type
        marker["ar_marker_name"] = marker_name
        marker["ar_marker_size"] = size

        # Create marker material
        mat = bpy.data.materials.new(name=f"AR_Marker_Mat_{marker_name}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        bsdf = get_principled_bsdf(nodes)
        if bsdf:
            # Use prominent colors
            if marker_type == "image":
                bsdf.inputs["Base Color"].default_value = (0, 1, 0, 1)  # Green
            elif marker_type == "qr":
                bsdf.inputs["Base Color"].default_value = (0, 0, 1, 1)  # Blue
            else:
                bsdf.inputs["Base Color"].default_value = (1, 1, 0, 1)  # Yellow

            bsdf.inputs["Alpha"].default_value = 0.5
            mat.blend_method = "BLEND"

        marker.data.materials.append(mat)

        return {
            "success": True,
            "data": {
                "marker_name": marker.name,
                "marker_type": marker_type,
                "position": position,
                "size": size,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "AR_MARKER_ERROR", "message": str(e)}}


def handle_xr_interaction(params: dict[str, Any]) -> dict[str, Any]:
    """Configure XR interaction point"""
    object_name = params.get("object_name", "")
    interaction_type = params.get("interaction_type", "grab")
    highlight_color = params.get("highlight_color", [1, 1, 0, 1])

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add custom properties
        obj["xr_interaction_type"] = interaction_type
        obj["xr_highlight_color"] = highlight_color
        obj["xr_interactable"] = True

        # Create highlight material
        mat_name = f"XR_Highlight_{object_name}"
        mat = bpy.data.materials.new(name=mat_name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes

        bsdf = get_principled_bsdf(nodes)
        if bsdf:
            bsdf.inputs["Emission Color"].default_value = highlight_color[:3] + (1.0,)
            bsdf.inputs["Emission Strength"].default_value = 0.5

        # Store original material references
        if obj.data and hasattr(obj.data, "materials"):
            obj["xr_original_materials"] = [m.name if m else "" for m in obj.data.materials]

        return {
            "success": True,
            "data": {
                "object": object_name,
                "interaction_type": interaction_type,
                "highlight_material": mat_name,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "XR_INTERACTION_ERROR", "message": str(e)}}


def handle_preview_start(params: dict[str, Any]) -> dict[str, Any]:
    """Start VR preview"""
    try:
        # Try to start VR preview
        try:
            bpy.ops.wm.xr_session_toggle()
            return {"success": True, "data": {"status": "VR preview started"}}
        except:
            return {
                "success": False,
                "error": {
                    "code": "VR_NOT_AVAILABLE",
                    "message": "VR preview not available. Please ensure VR addon and XR runtime are installed",
                },
            }

    except Exception as e:
        return {"success": False, "error": {"code": "PREVIEW_START_ERROR", "message": str(e)}}


def handle_preview_stop(params: dict[str, Any]) -> dict[str, Any]:
    """Stop VR preview"""
    try:
        try:
            # If VR session is running, stop it
            if hasattr(bpy.context, "window_manager") and hasattr(
                bpy.context.window_manager, "xr_session_state"
            ):
                if bpy.context.window_manager.xr_session_state:
                    bpy.ops.wm.xr_session_toggle()

            return {"success": True, "data": {"status": "VR preview stopped"}}
        except:
            return {"success": True, "data": {"status": "VR preview was not running"}}

    except Exception as e:
        return {"success": False, "error": {"code": "PREVIEW_STOP_ERROR", "message": str(e)}}


def handle_panorama_render(params: dict[str, Any]) -> dict[str, Any]:
    """Render 360-degree panorama"""
    filepath = params.get("filepath")
    resolution = params.get("resolution", 4096)
    stereo = params.get("stereo", False)

    try:
        scene = bpy.context.scene

        # Save original settings
        original_engine = scene.render.engine
        original_res_x = scene.render.resolution_x
        original_res_y = scene.render.resolution_y
        original_filepath = scene.render.filepath

        # Set up panorama rendering
        scene.render.engine = "CYCLES"
        scene.render.resolution_x = resolution
        scene.render.resolution_y = resolution // 2  # Equirectangular projection 2:1
        scene.render.filepath = filepath

        # Configure camera
        camera = scene.camera
        if camera:
            cam_data = camera.data
            original_type = cam_data.type

            cam_data.type = "PANO"
            cam_data.cycles.panorama_type = "EQUIRECTANGULAR"

            if stereo:
                scene.render.use_multiview = True
                scene.render.views_format = "STEREO_3D"
                cam_data.stereo.interocular_distance = 0.064

        # Render
        bpy.ops.render.render(write_still=True)

        # Restore settings
        scene.render.engine = original_engine
        scene.render.resolution_x = original_res_x
        scene.render.resolution_y = original_res_y
        scene.render.filepath = original_filepath

        if camera:
            cam_data.type = original_type

        return {
            "success": True,
            "data": {
                "filepath": filepath,
                "resolution": [resolution, resolution // 2],
                "stereo": stereo,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "PANORAMA_RENDER_ERROR", "message": str(e)}}
