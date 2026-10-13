"""
Character template handler

Handles character template creation, facial expressions, clothing, hairstyle and related commands.
"""

import math
from typing import Any

import bpy

from .node_utils import find_principled_bsdf as get_principled_bsdf

# ==================== Template Configuration ====================

TEMPLATE_CONFIG = {
    "chibi": {
        "head_scale": [1.0, 1.0, 1.1],
        "body_scale": [0.6, 0.4, 0.7],
        "head_body_ratio": 2.5,
        "eye_size": 1.5,
        "limb_thickness": 0.15,
        "leg_frac": 0.36,
    },
    "realistic": {
        "head_scale": [0.5, 0.5, 0.6],
        "body_scale": [0.8, 0.5, 1.2],
        "head_body_ratio": 7.5,
        "eye_size": 0.8,
        "limb_thickness": 0.12,
        "leg_frac": 0.48,
    },
    "anime": {
        "head_scale": [0.7, 0.7, 0.8],
        "body_scale": [0.7, 0.45, 1.0],
        "head_body_ratio": 5.5,
        "eye_size": 1.3,
        "limb_thickness": 0.1,
        "leg_frac": 0.46,
    },
    "stylized": {
        "head_scale": [0.8, 0.8, 0.9],
        "body_scale": [0.65, 0.45, 0.85],
        "head_body_ratio": 4.0,
        "eye_size": 1.2,
        "limb_thickness": 0.12,
        "leg_frac": 0.43,
    },
    "mascot": {
        "head_scale": [1.2, 1.2, 1.3],
        "body_scale": [0.8, 0.6, 0.6],
        "head_body_ratio": 2.0,
        "eye_size": 1.8,
        "limb_thickness": 0.2,
        "leg_frac": 0.32,
    },
}

SKIN_COLORS = {
    "light": [1.0, 0.9, 0.8, 1.0],
    "medium": [0.9, 0.75, 0.6, 1.0],
    "tan": [0.8, 0.6, 0.45, 1.0],
    "dark": [0.5, 0.35, 0.25, 1.0],
}

EXPRESSION_CONFIG = {
    "neutral": {"eye_scale": 1.0, "mouth_curve": 0, "eyebrow_angle": 0},
    "happy": {"eye_scale": 0.8, "mouth_curve": 0.3, "eyebrow_angle": 0.1},
    "sad": {"eye_scale": 1.0, "mouth_curve": -0.2, "eyebrow_angle": -0.2},
    "angry": {"eye_scale": 0.9, "mouth_curve": -0.1, "eyebrow_angle": -0.3},
    "surprised": {"eye_scale": 1.3, "mouth_curve": 0, "eyebrow_angle": 0.3},
    "wink": {"eye_scale": 0.7, "mouth_curve": 0.2, "eyebrow_angle": 0.1},
    "smile": {"eye_scale": 0.85, "mouth_curve": 0.25, "eyebrow_angle": 0.05},
}


def _create_material(name: str, color: list[float], metallic: float = 0.0, roughness: float = 0.5):
    """Create material"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True

    bsdf = get_principled_bsdf(mat.node_tree.nodes)
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Metallic"].default_value = metallic
        bsdf.inputs["Roughness"].default_value = roughness

    return mat


def _assign_material(obj, material) -> None:
    """Assign material to object"""
    if obj.data.materials:
        obj.data.materials[0] = material
    else:
        obj.data.materials.append(material)


def _character_layout(
    height: float, config: dict[str, Any], location: list[float]
) -> dict[str, float]:
    """Derive one coherent vertical skeleton from the requested height.

    Every part is placed from these numbers, so the head, neck, torso, hips and
    legs always meet exactly. Previously each part used its own magic offset,
    which left the head floating 0.22 m above the torso.
    """
    z0 = location[2]

    head_h = height / config["head_body_ratio"]
    aspect_x = config["head_scale"][0] / config["head_scale"][2]
    aspect_y = config["head_scale"][1] / config["head_scale"][2]
    head_w = head_h * aspect_x
    head_d = head_h * aspect_y

    leg_len = height * config["leg_frac"]
    hip_z = z0 + leg_len

    head_center_z = z0 + height - head_h / 2
    head_bottom_z = z0 + height - head_h

    # A short neck bridges head and torso; both ends overlap it slightly.
    neck_h = head_h * 0.22
    shoulder_z = head_bottom_z - neck_h

    torso_h = max(shoulder_z - hip_z, height * 0.08)

    return {
        "z0": z0,
        "head_h": head_h,
        "head_w": head_w,
        "head_d": head_d,
        "head_center_z": head_center_z,
        "head_bottom_z": head_bottom_z,
        "neck_h": neck_h,
        "shoulder_z": shoulder_z,
        "hip_z": hip_z,
        "leg_len": leg_len,
        "torso_h": torso_h,
        "torso_center_z": hip_z + torso_h / 2,
    }


def handle_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create character from template"""
    template = params.get("template", "chibi")
    name = params.get("name", "Character")
    height = params.get("height", 1.7)
    location = params.get("location", [0, 0, 0])
    skin_color = params.get("skin_color") or SKIN_COLORS["light"]

    config = TEMPLATE_CONFIG.get(template, TEMPLATE_CONFIG["chibi"])

    # Scale factor for widths only; all vertical placement comes from _character_layout.
    scale_factor = height / 1.7
    x0, y0 = location[0], location[1]
    lay = _character_layout(height, config, location)

    created_parts = []

    # Create skin material
    skin_mat = _create_material(f"{name}_Skin", skin_color, roughness=0.8)

    # ========== Head ==========
    # Unit sphere scaled into an ellipsoid: head_scale is applied exactly once.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=[x0, y0, lay["head_center_z"]])
    head = bpy.context.active_object
    head.name = f"{name}_Head"
    head.scale = [lay["head_w"] / 2, lay["head_d"] / 2, lay["head_h"] / 2]
    _assign_material(head, skin_mat)
    created_parts.append(head.name)

    # ========== Neck ==========
    bpy.ops.mesh.primitive_cylinder_add(
        radius=config["limb_thickness"] * scale_factor * 0.35,
        depth=lay["neck_h"] * 1.8,  # overlaps head and torso so nothing gaps
        location=[x0, y0, (lay["head_bottom_z"] + lay["shoulder_z"]) / 2],
    )
    neck = bpy.context.active_object
    neck.name = f"{name}_Neck"
    _assign_material(neck, skin_mat)
    created_parts.append(neck.name)

    # ========== Body ==========
    torso_half_w = config["body_scale"][0] * scale_factor * 0.30
    torso_half_d = config["body_scale"][1] * scale_factor * 0.20
    bpy.ops.mesh.primitive_cube_add(location=[x0, y0, lay["torso_center_z"]])
    body = bpy.context.active_object
    body.name = f"{name}_Body"
    body.scale = [torso_half_w, torso_half_d, lay["torso_h"] / 2]
    _assign_material(body, skin_mat)
    created_parts.append(body.name)

    # ========== Eyes ==========
    eye_mat = _create_material(f"{name}_Eye", [0.05, 0.02, 0.0, 1.0], roughness=0.3)
    eye_highlight_mat = _create_material(
        f"{name}_EyeHighlight", [1.0, 1.0, 1.0, 1.0], roughness=0.2
    )

    # Sized and placed relative to the head ellipsoid, so eyes always sit on
    # the face instead of piercing through it at a fixed offset.
    eye_size = lay["head_w"] * 0.11 * config["eye_size"]
    eye_x = lay["head_w"] * 0.22
    eye_z = lay["head_center_z"] - lay["head_h"] * 0.05
    rx, ry = lay["head_w"] / 2, lay["head_d"] / 2

    for side, sign in (("L", -1.0), ("R", 1.0)):
        # Project onto the ellipsoid's surface at this eye's own x, so the
        # eyeball sits flush on the face for any head shape.
        t = min(1.0, eye_x / rx) if rx > 0 else 0.0
        surface_y = y0 - ry * math.sqrt(max(0.0, 1.0 - t * t))

        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=eye_size, location=[x0 + sign * eye_x, surface_y, eye_z]
        )
        eye = bpy.context.active_object
        eye.name = f"{name}_Eye_{side}"
        eye.scale = [1.0, 0.65, 1.0]
        _assign_material(eye, eye_mat)
        created_parts.append(eye.name)

        # Highlight
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=eye_size * 0.28,
            location=[
                x0 + sign * eye_x + sign * eye_size * 0.30,
                surface_y - eye_size * 0.45,
                eye_z + eye_size * 0.40,
            ],
        )
        highlight = bpy.context.active_object
        highlight.name = f"{name}_EyeHighlight_{side}"
        _assign_material(highlight, eye_highlight_mat)
        created_parts.append(highlight.name)

    # ========== Arms ==========
    # Hung from the shoulder just outside the torso: previously they ran down
    # the body's centre line, burying them inside the chest.
    arm_length = height * 0.26
    arm_radius = config["limb_thickness"] * scale_factor * 0.5
    spread = 0.14  # slight A-pose

    for side, sign in (("L", -1.0), ("R", 1.0)):
        shoulder_x = x0 + sign * (torso_half_w + arm_radius * 0.6)
        # Unit direction the arm hangs in, tilting outward on the way down.
        dir_x = sign * math.sin(spread)
        dir_z = -math.cos(spread)

        bpy.ops.mesh.primitive_cylinder_add(
            radius=arm_radius,
            depth=arm_length,
            location=[
                shoulder_x + dir_x * arm_length / 2,
                y0,
                lay["shoulder_z"] + dir_z * arm_length / 2,
            ],
        )
        arm = bpy.context.active_object
        arm.name = f"{name}_Arm_{side}"
        arm.rotation_euler = [0, -sign * spread, 0]
        _assign_material(arm, skin_mat)
        created_parts.append(arm.name)

        # Hand, at the far end of the arm
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=arm_radius * 1.15,
            location=[
                shoulder_x + dir_x * arm_length,
                y0,
                lay["shoulder_z"] + dir_z * arm_length,
            ],
        )
        hand = bpy.context.active_object
        hand.name = f"{name}_Hand_{side}"
        _assign_material(hand, skin_mat)
        created_parts.append(hand.name)

    # ========== Legs ==========
    leg_radius = config["limb_thickness"] * scale_factor * 0.6
    leg_x = torso_half_w * 0.45
    foot_h = height * 0.025

    for side, sign in (("L", -1.0), ("R", 1.0)):
        bpy.ops.mesh.primitive_cylinder_add(
            radius=leg_radius,
            depth=lay["leg_len"],
            location=[x0 + sign * leg_x, y0, lay["z0"] + lay["leg_len"] / 2],
        )
        leg = bpy.context.active_object
        leg.name = f"{name}_Leg_{side}"
        _assign_material(leg, skin_mat)
        created_parts.append(leg.name)

        # Foot, resting on the ground plane and pointing forward (-Y)
        bpy.ops.mesh.primitive_cube_add(
            location=[x0 + sign * leg_x, y0 - height * 0.03, lay["z0"] + foot_h / 2]
        )
        foot = bpy.context.active_object
        foot.name = f"{name}_Foot_{side}"
        foot.scale = [leg_radius * 1.15, height * 0.055, foot_h / 2]
        _assign_material(foot, skin_mat)
        created_parts.append(foot.name)

    return {
        "success": True,
        "data": {
            "character_name": name,
            "template": template,
            "parts_created": len(created_parts),
            "parts": created_parts,
        },
    }


def handle_face_expression(params: dict[str, Any]) -> dict[str, Any]:
    """Set facial expression"""
    character_name = params.get("character_name")
    expression = params.get("expression", "neutral")
    intensity = params.get("intensity", 1.0)

    config = EXPRESSION_CONFIG.get(expression, EXPRESSION_CONFIG["neutral"])

    # Adjust eyes
    for side in ["L", "R"]:
        eye = bpy.data.objects.get(f"{character_name}_Eye_{side}")
        if eye:
            base_scale = eye.scale.copy()
            eye.scale[2] = base_scale[2] * (1.0 + (config["eye_scale"] - 1.0) * intensity)

    # If mouth object exists, adjust it
    mouth = bpy.data.objects.get(f"{character_name}_Mouth")
    if mouth:
        mouth.scale[0] = 1.0 + config["mouth_curve"] * intensity

    return {"success": True, "data": {"expression": expression, "intensity": intensity}}


def handle_face_setup(params: dict[str, Any]) -> dict[str, Any]:
    """Adjust facial features"""
    character_name = params.get("character_name")
    eye_size = params.get("eye_size", 1.0)
    eye_spacing = params.get("eye_spacing", 1.0)

    # Adjust eye size
    for side in ["L", "R"]:
        eye = bpy.data.objects.get(f"{character_name}_Eye_{side}")
        if eye:
            eye.scale *= eye_size

        highlight = bpy.data.objects.get(f"{character_name}_EyeHighlight_{side}")
        if highlight:
            highlight.scale *= eye_size

    # Adjust eye spacing
    eye_l = bpy.data.objects.get(f"{character_name}_Eye_L")
    eye_r = bpy.data.objects.get(f"{character_name}_Eye_R")
    if eye_l and eye_r:
        center_x = (eye_l.location.x + eye_r.location.x) / 2
        offset = abs(eye_l.location.x - center_x) * eye_spacing
        eye_l.location.x = center_x - offset
        eye_r.location.x = center_x + offset

    return {"success": True, "data": {}}


def handle_clothing_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add clothing"""
    character_name = params.get("character_name")
    clothing_type = params.get("clothing_type", "shirt")
    color = params.get("color") or [0.2, 0.4, 0.8, 1.0]
    params.get("style", "casual")

    body = bpy.data.objects.get(f"{character_name}_Body")
    if not body:
        return {
            "success": False,
            "error": {
                "code": "BODY_NOT_FOUND",
                "message": f"Character body not found: {character_name}_Body",
            },
        }

    clothing_mat = _create_material(f"{character_name}_{clothing_type}", color, roughness=0.6)

    if clothing_type in ["shirt", "jacket", "uniform", "sportswear"]:
        # Top - wraps body
        bpy.ops.mesh.primitive_cube_add(location=body.location)
        clothing = bpy.context.active_object
        clothing.name = f"{character_name}_Clothing_{clothing_type}"
        clothing.scale = [body.scale[0] * 1.1, body.scale[1] * 1.1, body.scale[2] * 0.7]
        _assign_material(clothing, clothing_mat)

    elif clothing_type == "pants":
        # Pants - wraps legs
        for side in ["L", "R"]:
            leg = bpy.data.objects.get(f"{character_name}_Leg_{side}")
            if leg:
                bpy.ops.mesh.primitive_cylinder_add(
                    radius=leg.dimensions[0] * 0.6,
                    depth=leg.dimensions[2] * 1.05,
                    location=leg.location,
                )
                pants = bpy.context.active_object
                pants.name = f"{character_name}_Pants_{side}"
                _assign_material(pants, clothing_mat)

    elif clothing_type == "dress":
        # Dress
        bpy.ops.mesh.primitive_cone_add(
            radius1=body.scale[0] * 2,
            radius2=body.scale[0] * 0.8,
            depth=body.scale[2] * 2,
            location=[body.location[0], body.location[1], body.location[2] - body.scale[2] * 0.5],
        )
        dress = bpy.context.active_object
        dress.name = f"{character_name}_Clothing_dress"
        _assign_material(dress, clothing_mat)

    return {"success": True, "data": {"clothing_type": clothing_type}}


def handle_hair_create(params: dict[str, Any]) -> dict[str, Any]:
    """Create hairstyle"""
    character_name = params.get("character_name")
    hair_style = params.get("hair_style", "short")
    color = params.get("color") or [0.05, 0.03, 0.02, 1.0]
    volume = params.get("volume", 1.0)

    head = bpy.data.objects.get(f"{character_name}_Head")
    if not head:
        return {
            "success": False,
            "error": {
                "code": "HEAD_NOT_FOUND",
                "message": f"Character head not found: {character_name}_Head",
            },
        }

    hair_mat = _create_material(f"{character_name}_Hair", color, roughness=0.7)

    # Sit the hair as a cap over the crown, nudged back so it clears the face.
    hair_r = head.dimensions[0] * 0.58 * volume
    hair_z = head.location.z + head.dimensions[2] * 0.16
    hair_y = head.location[1] + head.dimensions[1] * 0.06

    if hair_style == "short":
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=hair_r,
            location=[head.location[0], hair_y, hair_z],
        )
        hair = bpy.context.active_object
        hair.name = f"{character_name}_Hair"
        hair.scale = [1.0, 1.0, 0.72]
        _assign_material(hair, hair_mat)

    elif hair_style == "medium":
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=hair_r,
            location=[head.location[0], hair_y, hair_z],
        )
        hair = bpy.context.active_object
        hair.name = f"{character_name}_Hair"
        hair.scale = [1.0, 1.08, 0.85]
        _assign_material(hair, hair_mat)

    elif hair_style == "long":
        # Top of head
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=hair_r,
            location=[head.location[0], hair_y, hair_z],
        )
        hair_top = bpy.context.active_object
        hair_top.name = f"{character_name}_Hair_Top"
        hair_top.scale = [1.0, 1.0, 0.72]
        _assign_material(hair_top, hair_mat)

        # Long hair at the back
        bpy.ops.mesh.primitive_cylinder_add(
            radius=head.dimensions[0] * 0.4 * volume,
            depth=head.dimensions[2] * 1.5,
            location=[
                head.location[0],
                head.location[1] + head.dimensions[1] * 0.3,
                head.location[2] - head.dimensions[2] * 0.5,
            ],
        )
        hair_back = bpy.context.active_object
        hair_back.name = f"{character_name}_Hair_Back"
        _assign_material(hair_back, hair_mat)

    elif hair_style == "ponytail":
        # Top of head
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=hair_r,
            location=[head.location[0], hair_y, hair_z],
        )
        hair_top = bpy.context.active_object
        hair_top.name = f"{character_name}_Hair_Top"
        hair_top.scale = [1.0, 1.0, 0.72]
        _assign_material(hair_top, hair_mat)

        # Ponytail
        bpy.ops.mesh.primitive_cylinder_add(
            radius=head.dimensions[0] * 0.15 * volume,
            depth=head.dimensions[2] * 1.2,
            location=[
                head.location[0],
                head.location[1] + head.dimensions[1] * 0.4,
                head.location[2],
            ],
        )
        ponytail = bpy.context.active_object
        ponytail.name = f"{character_name}_Hair_Ponytail"
        ponytail.rotation_euler = [0.5, 0, 0]
        _assign_material(ponytail, hair_mat)

    elif hair_style == "spiky":
        # Spiky hairstyle
        for i in range(8):
            angle = i * (2 * math.pi / 8)
            x = head.location[0] + math.cos(angle) * head.dimensions[0] * 0.3
            y = head.location[1] + math.sin(angle) * head.dimensions[1] * 0.3

            bpy.ops.mesh.primitive_cone_add(
                radius1=head.dimensions[0] * 0.1 * volume,
                radius2=0,
                depth=head.dimensions[2] * 0.4 * volume,
                location=[x, y, hair_z + head.dimensions[2] * 0.1],
            )
            spike = bpy.context.active_object
            spike.name = f"{character_name}_Hair_Spike_{i}"
            spike.rotation_euler = [math.cos(angle) * 0.3, math.sin(angle) * 0.3, 0]
            _assign_material(spike, hair_mat)

    elif hair_style == "bald":
        # Bald - no hair needed
        pass

    return {"success": True, "data": {"hair_style": hair_style}}


def handle_accessory_add(params: dict[str, Any]) -> dict[str, Any]:
    """Add accessory"""
    character_name = params.get("character_name")
    accessory_type = params.get("accessory_type", "glasses")
    color = params.get("color") or [0.1, 0.1, 0.1, 1.0]
    params.get("location", "auto")

    head = bpy.data.objects.get(f"{character_name}_Head")
    body = bpy.data.objects.get(f"{character_name}_Body")

    accessory_mat = _create_material(
        f"{character_name}_{accessory_type}", color, metallic=0.5, roughness=0.3
    )

    if accessory_type == "glasses" and head:
        # Glasses frame
        for side, x_offset in [("L", -0.08), ("R", 0.08)]:
            bpy.ops.mesh.primitive_torus_add(
                major_radius=0.04,
                minor_radius=0.005,
                location=[
                    head.location[0] + x_offset,
                    head.location[1] - head.dimensions[1] * 0.45,
                    head.location[2] + 0.02,
                ],
            )
            frame = bpy.context.active_object
            frame.name = f"{character_name}_Glasses_Frame_{side}"
            frame.rotation_euler = [1.57, 0, 0]
            _assign_material(frame, accessory_mat)

        # Glasses bridge
        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.003,
            depth=0.15,
            location=[
                head.location[0],
                head.location[1] - head.dimensions[1] * 0.35,
                head.location[2] + 0.02,
            ],
        )
        bridge = bpy.context.active_object
        bridge.name = f"{character_name}_Glasses_Bridge"
        bridge.rotation_euler = [0, 1.57, 0]
        _assign_material(bridge, accessory_mat)

    elif accessory_type == "hat" and head:
        # Hat
        bpy.ops.mesh.primitive_cylinder_add(
            radius=head.dimensions[0] * 0.6,
            depth=head.dimensions[2] * 0.3,
            location=[
                head.location[0],
                head.location[1],
                head.location[2] + head.dimensions[2] * 0.5,
            ],
        )
        hat = bpy.context.active_object
        hat.name = f"{character_name}_Hat"
        _assign_material(hat, accessory_mat)

        # Hat brim
        bpy.ops.mesh.primitive_cylinder_add(
            radius=head.dimensions[0] * 0.8,
            depth=0.02,
            location=[
                head.location[0],
                head.location[1] - head.dimensions[1] * 0.2,
                head.location[2] + head.dimensions[2] * 0.35,
            ],
        )
        brim = bpy.context.active_object
        brim.name = f"{character_name}_Hat_Brim"
        _assign_material(brim, accessory_mat)

    elif accessory_type == "medal" and body:
        # Medal
        gold_mat = _create_material(
            f"{character_name}_Medal_Gold", [1.0, 0.85, 0.0, 1.0], metallic=1.0, roughness=0.2
        )

        bpy.ops.mesh.primitive_cylinder_add(
            radius=0.04,
            depth=0.005,
            location=[
                body.location[0],
                body.location[1] - body.dimensions[1] * 0.6,
                body.location[2] + body.dimensions[2] * 0.3,
            ],
        )
        medal = bpy.context.active_object
        medal.name = f"{character_name}_Medal"
        medal.rotation_euler = [1.57, 0, 0]
        _assign_material(medal, gold_mat)

        # Ribbon
        ribbon_mat = _create_material(
            f"{character_name}_Medal_Ribbon", [0.8, 0.1, 0.1, 1.0], roughness=0.7
        )
        bpy.ops.mesh.primitive_cube_add(
            location=[
                body.location[0],
                body.location[1] - body.dimensions[1] * 0.5,
                body.location[2] + body.dimensions[2] * 0.5,
            ]
        )
        ribbon = bpy.context.active_object
        ribbon.name = f"{character_name}_Medal_Ribbon"
        ribbon.scale = [0.01, 0.005, 0.1]
        _assign_material(ribbon, ribbon_mat)

    elif accessory_type == "necklace" and body:
        # Sit the ring around the base of the neck. Blender's torus already lies
        # flat in XY, which is how a necklace sits - the previous 90-degree X
        # rotation stood it up into a vertical hoop hanging in mid-air.
        neck = bpy.data.objects.get(f"{character_name}_Neck")
        if neck:
            ring_r = max(neck.dimensions[0], 1e-4) * 0.9
            ring_z = neck.location.z - neck.dimensions[2] * 0.30
        else:
            ring_r = body.dimensions[0] * 0.22
            ring_z = body.location.z + body.dimensions[2] * 0.5

        bpy.ops.mesh.primitive_torus_add(
            major_radius=ring_r,
            minor_radius=ring_r * 0.16,
            location=[body.location[0], body.location[1], ring_z],
        )
        necklace = bpy.context.active_object
        necklace.name = f"{character_name}_Necklace"
        # Follow the torso's depth so the ring hugs the body, not a circle.
        necklace.scale = [1.0, body.dimensions[1] / max(body.dimensions[0], 1e-6), 1.0]
        _assign_material(necklace, accessory_mat)

    return {"success": True, "data": {"accessory_type": accessory_type}}
