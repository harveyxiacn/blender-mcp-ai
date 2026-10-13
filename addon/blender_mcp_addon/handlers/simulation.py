"""
Advanced Simulation Handler

Handles fluid, smoke, ocean and other advanced simulation commands.
"""

from typing import Any

import bpy


def handle_fluid_domain(params: dict[str, Any]) -> dict[str, Any]:
    """Set up fluid domain"""
    object_name = params.get("object_name", "")
    domain_type = params.get("domain_type", "LIQUID")
    resolution = params.get("resolution", 64)
    use_adaptive_domain = params.get("use_adaptive_domain", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add fluid modifier
        mod = obj.modifiers.new(name="Fluid", type="FLUID")
        mod.fluid_type = "DOMAIN"

        settings = mod.domain_settings
        settings.domain_type = domain_type
        settings.resolution_max = resolution
        settings.use_adaptive_domain = use_adaptive_domain

        # Set cache
        settings.cache_frame_start = 1
        settings.cache_frame_end = 250

        return {
            "success": True,
            "data": {"object_name": obj.name, "domain_type": domain_type, "resolution": resolution},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "FLUID_DOMAIN_ERROR", "message": str(e)}}


def handle_fluid_flow(params: dict[str, Any]) -> dict[str, Any]:
    """Set up fluid inflow/outflow"""
    object_name = params.get("object_name", "")
    flow_type = params.get("flow_type", "LIQUID")  # Blender 5.0: SMOKE, BOTH, FIRE, LIQUID
    flow_behavior = params.get("flow_behavior", "INFLOW")  # INFLOW, OUTFLOW, GEOMETRY
    use_initial_velocity = params.get("use_initial_velocity", False)
    velocity = params.get("velocity", [0, 0, 0])

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add fluid modifier
        mod = obj.modifiers.new(name="Fluid", type="FLUID")
        mod.fluid_type = "FLOW"

        settings = mod.flow_settings
        # Blender 5.0: flow_type is substance type (SMOKE, BOTH, FIRE, LIQUID)
        # flow_behavior is behavior (INFLOW, OUTFLOW, GEOMETRY)

        # Map old INFLOW to new API
        if flow_type == "INFLOW":
            settings.flow_type = "LIQUID"
            settings.flow_behavior = "INFLOW"
        elif flow_type == "OUTFLOW":
            settings.flow_type = "LIQUID"
            settings.flow_behavior = "OUTFLOW"
        else:
            settings.flow_type = flow_type
            settings.flow_behavior = flow_behavior

        settings.use_initial_velocity = use_initial_velocity

        if use_initial_velocity:
            settings.velocity_coord = velocity

        return {
            "success": True,
            "data": {
                "object_name": obj.name,
                "flow_type": settings.flow_type,
                "flow_behavior": settings.flow_behavior,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "FLUID_FLOW_ERROR", "message": str(e)}}


def handle_fluid_effector(params: dict[str, Any]) -> dict[str, Any]:
    """Set up fluid effector"""
    object_name = params.get("object_name", "")
    effector_type = params.get("effector_type", "COLLISION")

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add fluid modifier
        mod = obj.modifiers.new(name="Fluid", type="FLUID")
        mod.fluid_type = "EFFECTOR"

        settings = mod.effector_settings
        settings.effector_type = effector_type

        return {"success": True, "data": {"object_name": obj.name, "effector_type": effector_type}}
    except Exception as e:
        return {"success": False, "error": {"code": "FLUID_EFFECTOR_ERROR", "message": str(e)}}


def handle_smoke_domain(params: dict[str, Any]) -> dict[str, Any]:
    """Set up smoke/fire domain"""
    object_name = params.get("object_name", "")
    smoke_type = params.get("smoke_type", "SMOKE")
    resolution = params.get("resolution", 32)
    use_high_resolution = params.get("use_high_resolution", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add fluid modifier (smoke is GAS type fluid)
        mod = obj.modifiers.new(name="Smoke", type="FLUID")
        mod.fluid_type = "DOMAIN"

        settings = mod.domain_settings
        settings.domain_type = "GAS"
        settings.resolution_max = resolution
        settings.use_noise = use_high_resolution

        # Set smoke/fire
        if smoke_type == "FIRE":
            settings.use_flame_smoke = False
        elif smoke_type == "BOTH":
            settings.use_flame_smoke = True

        return {
            "success": True,
            "data": {"object_name": obj.name, "smoke_type": smoke_type, "resolution": resolution},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "SMOKE_DOMAIN_ERROR", "message": str(e)}}


def handle_smoke_flow(params: dict[str, Any]) -> dict[str, Any]:
    """Set up smoke/fire emitter"""
    object_name = params.get("object_name", "")
    flow_type = params.get("flow_type", "SMOKE")
    temperature = params.get("temperature", 1.0)
    density = params.get("density", 1.0)
    smoke_color = params.get("smoke_color", [1, 1, 1])

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add fluid modifier
        mod = obj.modifiers.new(name="SmokeFlow", type="FLUID")
        mod.fluid_type = "FLOW"

        settings = mod.flow_settings
        settings.flow_type = flow_type
        settings.flow_behavior = "INFLOW"
        settings.temperature = temperature
        settings.density = density
        settings.smoke_color = smoke_color[:3]

        return {"success": True, "data": {"object_name": obj.name, "flow_type": flow_type}}
    except Exception as e:
        return {"success": False, "error": {"code": "SMOKE_FLOW_ERROR", "message": str(e)}}


def handle_ocean(params: dict[str, Any]) -> dict[str, Any]:
    """Add ocean modifier"""
    object_name = params.get("object_name", "")
    resolution = params.get("resolution", 7)
    spatial_size = params.get("spatial_size", 50)
    wave_scale = params.get("wave_scale", 1.0)
    choppiness = params.get("choppiness", 1.0)
    wind_velocity = params.get("wind_velocity", 30.0)
    use_foam = params.get("use_foam", False)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add ocean modifier
        mod = obj.modifiers.new(name="Ocean", type="OCEAN")
        mod.resolution = resolution
        mod.spatial_size = spatial_size
        mod.wave_scale = wave_scale
        mod.choppiness = choppiness
        mod.wind_velocity = wind_velocity
        mod.use_foam = use_foam

        # Use generated geometry
        mod.geometry_mode = "GENERATE"

        return {
            "success": True,
            "data": {
                "object_name": obj.name,
                "resolution": resolution,
                "spatial_size": spatial_size,
            },
        }
    except Exception as e:
        return {"success": False, "error": {"code": "OCEAN_ERROR", "message": str(e)}}


def handle_dynamic_paint_canvas(params: dict[str, Any]) -> dict[str, Any]:
    """Set up dynamic paint canvas"""
    object_name = params.get("object_name", "")
    surface_type = params.get("surface_type", "PAINT")
    use_dissolve = params.get("use_dissolve", False)
    dissolve_speed = params.get("dissolve_speed", 80)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add dynamic paint modifier
        mod = obj.modifiers.new(name="DynamicPaint", type="DYNAMIC_PAINT")
        mod.ui_type = "CANVAS"

        # Add canvas surface
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.dpaint.surface_slot_add()

        canvas = mod.canvas_settings
        if canvas and canvas.canvas_surfaces:
            surface = canvas.canvas_surfaces.active
            surface.surface_type = surface_type
            surface.use_dissolve = use_dissolve
            if use_dissolve:
                surface.dissolve_speed = dissolve_speed

        return {"success": True, "data": {"object_name": obj.name, "surface_type": surface_type}}
    except Exception as e:
        return {
            "success": False,
            "error": {"code": "DYNAMIC_PAINT_CANVAS_ERROR", "message": str(e)},
        }


def handle_dynamic_paint_brush(params: dict[str, Any]) -> dict[str, Any]:
    """Set up dynamic paint brush"""
    object_name = params.get("object_name", "")
    paint_color = params.get("paint_color", [1, 0, 0])
    paint_alpha = params.get("paint_alpha", 1.0)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Add dynamic paint modifier
        mod = obj.modifiers.new(name="DynamicPaint", type="DYNAMIC_PAINT")
        mod.ui_type = "BRUSH"

        brush = mod.brush_settings
        brush.paint_color = paint_color[:3]
        brush.paint_alpha = paint_alpha

        return {"success": True, "data": {"object_name": obj.name, "paint_color": paint_color}}
    except Exception as e:
        return {"success": False, "error": {"code": "DYNAMIC_PAINT_BRUSH_ERROR", "message": str(e)}}


def handle_bake(params: dict[str, Any]) -> dict[str, Any]:
    """Bake simulation"""
    object_name = params.get("object_name", "")
    frame_start = params.get("frame_start", 1)
    frame_end = params.get("frame_end", 250)

    obj = bpy.data.objects.get(object_name)
    if not obj:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }

    try:
        # Set frame range
        bpy.context.scene.frame_start = frame_start
        bpy.context.scene.frame_end = frame_end

        # Select object
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # Find fluid modifier and bake
        for mod in obj.modifiers:
            if mod.type == "FLUID" and mod.fluid_type == "DOMAIN":
                # Note: Actual baking may take a long time
                # Only setting parameters here, user needs to bake manually or use background task
                mod.domain_settings.cache_frame_start = frame_start
                mod.domain_settings.cache_frame_end = frame_end

                return {
                    "success": True,
                    "data": {
                        "object_name": obj.name,
                        "frame_start": frame_start,
                        "frame_end": frame_end,
                        "note": "Cache settings configured. Use Blender UI to bake.",
                    },
                }

        return {
            "success": False,
            "error": {"code": "NO_FLUID_DOMAIN", "message": "No fluid domain modifier found"},
        }
    except Exception as e:
        return {"success": False, "error": {"code": "BAKE_ERROR", "message": str(e)}}
