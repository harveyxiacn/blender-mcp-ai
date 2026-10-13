"""
Training System Command Handler

Handles training system-related commands on the Blender side.
Primarily responsible for executing scene creation and model operation commands in exercises.
"""

from typing import Any

import bpy


def handle_training(params: dict[str, Any]) -> dict[str, Any]:
    """Handle training system commands"""
    action = params.get("action", "")

    handlers = {
        "setup_penglai_scene": _setup_penglai_scene,
        "setup_fanzhendong_scene": _setup_fanzhendong_scene,
        "create_exercise_scene": _create_exercise_scene,
        "verify_exercise": _verify_exercise,
        "cleanup_scene": _cleanup_scene,
    }

    handler = handlers.get(action)
    if handler:
        return handler(params)
    return {
        "success": False,
        "error": {"code": "UNKNOWN_ACTION", "message": f"Unknown training action: {action}"},
    }


def _setup_penglai_scene(params: dict[str, Any]) -> dict[str, Any]:
    """Set up Penglai Nine Chapters training scene"""
    try:
        scene_name = params.get("scene_name", "PenglaiTraining")
        level = params.get("level", "basic")

        # Create or switch scene
        if scene_name in bpy.data.scenes:
            bpy.context.window.scene = bpy.data.scenes[scene_name]
        else:
            scene = bpy.data.scenes.new(scene_name)
            bpy.context.window.scene = scene

        scene = bpy.context.scene

        # Clear scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

        # Basic scene setup
        if level in ("basic", "full"):
            # Ground
            bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
            ground = bpy.context.active_object
            ground.name = "SM_Ground"

            # Set green material
            mat = bpy.data.materials.new("MAT_Ground_Grass")
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = (0.15, 0.35, 0.1, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.8
            ground.data.materials.append(mat)

        if level in ("intermediate", "full"):
            # Add tree placeholders
            import math

            for i in range(6):
                angle = i * math.pi * 2 / 6
                x = 8 * math.cos(angle)
                y = 8 * math.sin(angle)
                bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=4, location=(x, y, 2))
                trunk = bpy.context.active_object
                trunk.name = f"SM_Tree_Trunk_{i+1:02d}"

                # Tree canopy
                bpy.ops.mesh.primitive_uv_sphere_add(radius=2, location=(x, y, 5))
                canopy = bpy.context.active_object
                canopy.name = f"SM_Tree_Canopy_{i+1:02d}"

        if level == "full":
            # Add moon
            bpy.ops.mesh.primitive_uv_sphere_add(radius=1.5, location=(10, -5, 15))
            moon = bpy.context.active_object
            moon.name = "SM_Moon"
            mat_moon = bpy.data.materials.new("MAT_Moon_Glow")
            mat_moon.use_nodes = True
            bsdf = mat_moon.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Emission Color"].default_value = (1.0, 0.95, 0.8, 1.0)
            bsdf.inputs["Emission Strength"].default_value = 5.0
            moon.data.materials.append(mat_moon)

            # Add fog effect
            bpy.context.scene.world = bpy.data.worlds.new("World_MistyForest")
            bpy.context.scene.world.use_nodes = True

        obj_count = len(scene.objects)
        return {
            "success": True,
            "scene": scene_name,
            "level": level,
            "objects_created": obj_count,
            "message": f"Penglai Nine Chapters training scene created ({level}), {obj_count} objects total",
        }

    except Exception as e:
        return {"success": False, "error": {"code": "SETUP_FAILED", "message": str(e)}}


def _setup_fanzhendong_scene(params: dict[str, Any]) -> dict[str, Any]:
    """Set up chibi Fan Zhendong training scene"""
    try:
        scene_name = params.get("scene_name", "FZDTraining")
        level = params.get("level", "basic")

        # Create or switch scene
        if scene_name in bpy.data.scenes:
            bpy.context.window.scene = bpy.data.scenes[scene_name]
        else:
            scene = bpy.data.scenes.new(scene_name)
            bpy.context.window.scene = scene

        scene = bpy.context.scene

        # Clear scene
        for obj in list(scene.objects):
            bpy.data.objects.remove(obj, do_unlink=True)

        if level in ("basic", "full"):
            # Table tennis table
            bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.76))
            table = bpy.context.active_object
            table.name = "TT_Table"
            table.scale = (1.37, 0.7625, 0.025)
            bpy.ops.object.transform_apply(scale=True)

            # Table material
            mat_table = bpy.data.materials.new("MAT_Table_Blue")
            mat_table.use_nodes = True
            bsdf = mat_table.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = (0.0, 0.1, 0.4, 1.0)
            bsdf.inputs["Roughness"].default_value = 0.3
            table.data.materials.append(mat_table)

            # Table legs
            for i, (x, y) in enumerate([(-1.1, -0.55), (1.1, -0.55), (-1.1, 0.55), (1.1, 0.55)]):
                bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 0.37))
                leg = bpy.context.active_object
                leg.name = f"TT_Leg_{i+1}"
                leg.scale = (0.03, 0.03, 0.37)
                bpy.ops.object.transform_apply(scale=True)

            # Net
            bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0, 0.915))
            net = bpy.context.active_object
            net.name = "TT_Net"
            net.scale = (0.01, 0.7625, 0.076)
            bpy.ops.object.transform_apply(scale=True)

        if level in ("intermediate", "full"):
            # Table tennis ball
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(0.3, 0, 0.81))
            ball = bpy.context.active_object
            ball.name = "TT_Ball"
            mat_ball = bpy.data.materials.new("MAT_Ball_Orange")
            mat_ball.use_nodes = True
            bsdf = mat_ball.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = (1.0, 0.55, 0.05, 1.0)
            ball.data.materials.append(mat_ball)

            # Paddle
            bpy.ops.mesh.primitive_cylinder_add(radius=0.08, depth=0.01, location=(-0.5, 0, 0.85))
            paddle = bpy.context.active_object
            paddle.name = "Paddle_Blade"
            mat_paddle = bpy.data.materials.new("MAT_Paddle_Red")
            mat_paddle.use_nodes = True
            bsdf = mat_paddle.node_tree.nodes["Principled BSDF"]
            bsdf.inputs["Base Color"].default_value = (0.8, 0.05, 0.05, 1.0)
            paddle.data.materials.append(mat_paddle)

        if level == "full":
            # Paris Olympic rings
            ring_colors = [
                (0.0, 0.3, 0.7, 1.0),  # Blue
                (0.0, 0.0, 0.0, 1.0),  # Black
                (0.8, 0.1, 0.1, 1.0),  # Red
                (1.0, 0.75, 0.0, 1.0),  # Yellow
                (0.0, 0.5, 0.2, 1.0),  # Green
            ]
            for i, color in enumerate(ring_colors):
                x = (i - 2) * 0.5
                y_offset = 0.2 if i % 2 == 1 else 0
                bpy.ops.mesh.primitive_torus_add(
                    major_radius=0.2, minor_radius=0.02, location=(x, -3, 3 - y_offset)
                )
                ring = bpy.context.active_object
                ring.name = f"Olympic_Ring_{i+1}"
                mat_ring = bpy.data.materials.new(f"MAT_Ring_{i+1}")
                mat_ring.use_nodes = True
                bsdf = mat_ring.node_tree.nodes["Principled BSDF"]
                bsdf.inputs["Base Color"].default_value = color
                bsdf.inputs["Metallic"].default_value = 0.8
                ring.data.materials.append(mat_ring)

            # Lighting
            bpy.ops.object.light_add(type="AREA", location=(0, -2, 4))
            light = bpy.context.active_object
            light.name = "StadiumLight_Key"
            light.data.energy = 500
            light.data.size = 3

        obj_count = len(scene.objects)
        return {
            "success": True,
            "scene": scene_name,
            "level": level,
            "objects_created": obj_count,
            "message": f"Chibi Fan Zhendong training scene created ({level}), {obj_count} objects total",
        }

    except Exception as e:
        return {"success": False, "error": {"code": "SETUP_FAILED", "message": str(e)}}


def _create_exercise_scene(params: dict[str, Any]) -> dict[str, Any]:
    """Create a clean scene for exercises"""
    try:
        exercise_id = params.get("exercise_id", "exercise")
        scene_name = f"Training_{exercise_id}"

        if scene_name in bpy.data.scenes:
            bpy.context.window.scene = bpy.data.scenes[scene_name]
        else:
            scene = bpy.data.scenes.new(scene_name)
            bpy.context.window.scene = scene

        # Add basic lighting and camera
        bpy.ops.object.light_add(type="SUN", location=(5, -5, 10))
        sun = bpy.context.active_object
        sun.name = "Training_Sun"
        sun.data.energy = 3

        bpy.ops.object.camera_add(location=(7, -7, 5))
        cam = bpy.context.active_object
        cam.name = "Training_Camera"
        cam.rotation_euler = (1.1, 0, 0.8)
        bpy.context.scene.camera = cam

        return {
            "success": True,
            "scene": scene_name,
            "message": f"Exercise scene {scene_name} is ready",
        }

    except Exception as e:
        return {"success": False, "error": {"code": "SETUP_FAILED", "message": str(e)}}


def _verify_exercise(params: dict[str, Any]) -> dict[str, Any]:
    """Verify exercise results"""
    try:
        expected_objects = params.get("expected_objects", [])
        scene = bpy.context.scene
        found = []
        missing = []

        for name in expected_objects:
            if name in scene.objects:
                found.append(name)
            else:
                missing.append(name)

        success = len(missing) == 0
        return {
            "success": success,
            "found": found,
            "missing": missing,
            "total_objects": len(scene.objects),
            "message": f"Verification {'passed' if success else 'failed'}: Found {len(found)}/{len(expected_objects)} expected objects",
        }

    except Exception as e:
        return {"success": False, "error": {"code": "VERIFY_FAILED", "message": str(e)}}


def _cleanup_scene(params: dict[str, Any]) -> dict[str, Any]:
    """Clean up training scenes"""
    try:
        keep_scenes = params.get("keep_scenes", ["Scene"])
        removed = 0

        for scene in list(bpy.data.scenes):
            if scene.name.startswith("Training_") and scene.name not in keep_scenes:
                bpy.data.scenes.remove(scene)
                removed += 1

        return {
            "success": True,
            "removed_scenes": removed,
            "remaining_scenes": len(bpy.data.scenes),
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CLEANUP_FAILED", "message": str(e)}}
