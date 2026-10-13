"""
Motion capture handler

Handles motion capture data import and processing commands.
"""

import contextlib
import os
from typing import Any

import bpy


def handle_import(params: dict[str, Any]) -> dict[str, Any]:
    """Import motion capture data"""
    filepath = params.get("filepath")
    target_armature = params.get("target_armature", "")
    scale = params.get("scale", 1.0)
    frame_start = params.get("frame_start", 1)
    use_fps_scale = params.get("use_fps_scale", False)

    if not os.path.exists(filepath):
        return {
            "success": False,
            "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {filepath}"},
        }

    try:
        ext = os.path.splitext(filepath)[1].lower()

        if ext == ".bvh":
            # Import BVH
            bpy.ops.import_anim.bvh(
                filepath=filepath,
                filter_glob="*.bvh",
                global_scale=scale,
                frame_start=frame_start,
                use_fps_scale=use_fps_scale,
                use_cyclic=False,
                rotate_mode="NATIVE",
            )

        elif ext == ".fbx":
            # Import FBX animation
            bpy.ops.import_scene.fbx(
                filepath=filepath, use_anim=True, anim_offset=frame_start, global_scale=scale
            )
        else:
            return {
                "success": False,
                "error": {"code": "UNSUPPORTED_FORMAT", "message": f"Unsupported format: {ext}"},
            }

        # Get the imported armature
        imported_armature = None
        for obj in bpy.context.selected_objects:
            if obj.type == "ARMATURE":
                imported_armature = obj
                break

        # If a target armature is specified, attempt retargeting
        if target_armature and imported_armature:
            target = bpy.data.objects.get(target_armature)
            if target and target.type == "ARMATURE":
                # Copy action to target armature
                if imported_armature.animation_data and imported_armature.animation_data.action:
                    action = imported_armature.animation_data.action.copy()
                    if not target.animation_data:
                        target.animation_data_create()
                    target.animation_data.action = action

        return {
            "success": True,
            "data": {
                "filepath": filepath,
                "armature": imported_armature.name if imported_armature else None,
            },
        }

    except Exception as e:
        return {"success": False, "error": {"code": "IMPORT_ERROR", "message": str(e)}}


def handle_retarget(params: dict[str, Any]) -> dict[str, Any]:
    """Retarget action"""
    source_name = params.get("source_armature", "")
    target_name = params.get("target_armature", "")
    bone_mapping = params.get("bone_mapping", {})

    source = bpy.data.objects.get(source_name)
    target = bpy.data.objects.get(target_name)

    if not source or source.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "SOURCE_NOT_FOUND",
                "message": f"Source armature not found: {source_name}",
            },
        }

    if not target or target.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "TARGET_NOT_FOUND",
                "message": f"Target armature not found: {target_name}",
            },
        }

    try:
        # Get source action
        if not source.animation_data or not source.animation_data.action:
            return {
                "success": False,
                "error": {"code": "NO_ACTION", "message": "Source armature has no action data"},
            }

        source_action = source.animation_data.action

        # Create new action
        new_action = bpy.data.actions.new(name=f"{source_action.name}_retargeted")

        # Ensure target has animation data
        if not target.animation_data:
            target.animation_data_create()

        # Auto bone mapping (if not provided)
        if not bone_mapping:
            # Try to match bones with the same name
            for source_bone in source.data.bones:
                if source_bone.name in target.data.bones:
                    bone_mapping[source_bone.name] = source_bone.name

        # Copy FCurves
        for fcurve in source_action.fcurves:
            # Parse data path
            data_path = fcurve.data_path

            # Check if this is a bone-related curve
            if "pose.bones" in data_path:
                # Extract bone name
                try:
                    bone_name = data_path.split('"')[1]

                    # Find mapping
                    target_bone_name = bone_mapping.get(bone_name, bone_name)

                    if target_bone_name in target.data.bones:
                        # Create new data path
                        new_data_path = data_path.replace(f'"{bone_name}"', f'"{target_bone_name}"')

                        # Copy FCurve
                        new_fcurve = new_action.fcurves.new(
                            data_path=new_data_path, index=fcurve.array_index
                        )

                        # Copy keyframes
                        for kp in fcurve.keyframe_points:
                            new_fcurve.keyframe_points.insert(kp.co[0], kp.co[1])
                except:
                    continue

        # Assign new action
        target.animation_data.action = new_action

        return {
            "success": True,
            "data": {"action_name": new_action.name, "bones_mapped": len(bone_mapping)},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "RETARGET_ERROR", "message": str(e)}}


def handle_clean(params: dict[str, Any]) -> dict[str, Any]:
    """Clean action data"""
    armature_name = params.get("armature_name", "")
    action_name = params.get("action_name", "")
    threshold = params.get("threshold", 0.001)
    remove_noise = params.get("remove_noise", True)

    armature = bpy.data.objects.get(armature_name)
    if not armature or armature.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    try:
        # Get action
        action = None
        if action_name:
            action = bpy.data.actions.get(action_name)
        elif armature.animation_data and armature.animation_data.action:
            action = armature.animation_data.action

        if not action:
            return {
                "success": False,
                "error": {"code": "NO_ACTION", "message": "No action data found"},
            }

        cleaned_count = 0

        if remove_noise:
            # Select armature
            bpy.ops.object.select_all(action="DESELECT")
            armature.select_set(True)
            bpy.context.view_layer.objects.active = armature

            # Enter pose mode
            bpy.ops.object.mode_set(mode="POSE")

            # Select all bones
            bpy.ops.pose.select_all(action="SELECT")

            # Clean keyframes
            try:
                bpy.ops.action.clean(threshold=threshold)
                cleaned_count = 1
            except:
                pass

            # Return to object mode
            bpy.ops.object.mode_set(mode="OBJECT")

        # Remove redundant keyframes
        for fcurve in action.fcurves:
            # Remove nearly identical consecutive keyframes
            points_to_remove = []
            prev_value = None

            for i, kp in enumerate(fcurve.keyframe_points):
                if prev_value is not None:
                    if abs(kp.co[1] - prev_value) < threshold:
                        points_to_remove.append(i)
                prev_value = kp.co[1]

            # Delete from back to front
            for i in reversed(points_to_remove):
                if 0 < i < len(fcurve.keyframe_points) - 1:  # Keep first and last
                    fcurve.keyframe_points.remove(fcurve.keyframe_points[i])
                    cleaned_count += 1

        return {
            "success": True,
            "data": {"action_name": action.name, "cleaned_keyframes": cleaned_count},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "CLEAN_ERROR", "message": str(e)}}


def handle_blend(params: dict[str, Any]) -> dict[str, Any]:
    """Blend actions"""
    armature_name = params.get("armature_name", "")
    action1_name = params.get("action1", "")
    action2_name = params.get("action2", "")
    blend_factor = params.get("blend_factor", 0.5)
    output_name = params.get("output_name", "BlendedAction")

    armature = bpy.data.objects.get(armature_name)
    if not armature or armature.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    action1 = bpy.data.actions.get(action1_name)
    action2 = bpy.data.actions.get(action2_name)

    if not action1:
        return {
            "success": False,
            "error": {"code": "ACTION_NOT_FOUND", "message": f"Action 1 not found: {action1_name}"},
        }

    if not action2:
        return {
            "success": False,
            "error": {"code": "ACTION_NOT_FOUND", "message": f"Action 2 not found: {action2_name}"},
        }

    try:
        # Create new action
        blended_action = bpy.data.actions.new(name=output_name)

        # Get all data paths
        all_paths = set()
        for fc in action1.fcurves:
            all_paths.add((fc.data_path, fc.array_index))
        for fc in action2.fcurves:
            all_paths.add((fc.data_path, fc.array_index))

        # Blend each FCurve
        for data_path, array_index in all_paths:
            fc1 = action1.fcurves.find(data_path, index=array_index)
            fc2 = action2.fcurves.find(data_path, index=array_index)

            if fc1 or fc2:
                new_fc = blended_action.fcurves.new(data_path=data_path, index=array_index)

                # Get all keyframe time points
                frames = set()
                if fc1:
                    for kp in fc1.keyframe_points:
                        frames.add(int(kp.co[0]))
                if fc2:
                    for kp in fc2.keyframe_points:
                        frames.add(int(kp.co[0]))

                # Blend values at each frame
                for frame in sorted(frames):
                    val1 = fc1.evaluate(frame) if fc1 else 0
                    val2 = fc2.evaluate(frame) if fc2 else 0

                    blended_value = val1 * (1 - blend_factor) + val2 * blend_factor
                    new_fc.keyframe_points.insert(frame, blended_value)

        # Assign blended action
        if not armature.animation_data:
            armature.animation_data_create()
        armature.animation_data.action = blended_action

        return {
            "success": True,
            "data": {"action_name": blended_action.name, "blend_factor": blend_factor},
        }

    except Exception as e:
        return {"success": False, "error": {"code": "BLEND_ERROR", "message": str(e)}}


def handle_bake(params: dict[str, Any]) -> dict[str, Any]:
    """Bake action"""
    armature_name = params.get("armature_name", "")
    frame_start = params.get("frame_start", 1)
    frame_end = params.get("frame_end", 250)
    only_selected = params.get("only_selected", False)
    visual_keying = params.get("visual_keying", True)

    armature = bpy.data.objects.get(armature_name)
    if not armature or armature.type != "ARMATURE":
        return {
            "success": False,
            "error": {
                "code": "ARMATURE_NOT_FOUND",
                "message": f"Armature not found: {armature_name}",
            },
        }

    try:
        # Select armature
        bpy.ops.object.select_all(action="DESELECT")
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature

        # Enter pose mode
        bpy.ops.object.mode_set(mode="POSE")

        # Select bones
        if not only_selected:
            bpy.ops.pose.select_all(action="SELECT")

        # Bake action
        bpy.ops.nla.bake(
            frame_start=frame_start,
            frame_end=frame_end,
            only_selected=only_selected,
            visual_keying=visual_keying,
            clear_constraints=False,
            clear_parents=False,
            use_current_action=True,
            bake_types={"POSE"},
        )

        # Return to object mode
        bpy.ops.object.mode_set(mode="OBJECT")

        return {
            "success": True,
            "data": {"armature": armature_name, "frame_range": [frame_start, frame_end]},
        }

    except Exception as e:
        # Ensure return to object mode
        with contextlib.suppress(BaseException):
            bpy.ops.object.mode_set(mode="OBJECT")

        return {"success": False, "error": {"code": "BAKE_ERROR", "message": str(e)}}
