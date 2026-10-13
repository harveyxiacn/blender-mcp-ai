"""
Generic reference image handlers for reference-driven modeling.
"""

from __future__ import annotations

import json
import math
import os
import re
from pathlib import Path
from typing import Any

import bpy

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
REFERENCE_MANIFEST_NAME = "reference_manifest.json"

ROLE_PATTERNS: dict[str, tuple[str, ...]] = {
    "figure_front": ("figure_front", "figurine_front", "statue_front"),
    "figure_side": ("figure_side", "figure_profile", "figurine_side", "statue_side"),
    "figure_back": ("figure_back", "figurine_back", "statue_back"),
    "weapon": ("weapon", "sword", "blade", "rapier", "gun", "staff", "逐暗者", "闪光"),
    "outfit": (
        "outfit",
        "costume",
        "clothes",
        "uniform",
        "armor",
        "coat",
        "dress",
        "服装",
        "胸甲",
        "肩甲",
        "裙",
    ),
    "hair": ("hair", "bang", "braid", "ponytail", "fringe", "刘海", "发型", "长发", "辫"),
    "face": ("face", "portrait", "close", "closeup", "head", "脸", "面部", "特写"),
    "detail": ("detail", "细节"),
    "pose": ("pose", "action", "stance", "attack", "swing", "姿态", "动作"),
    "three_quarter": ("three_quarter", "threequarter", "3q", "3_4", "34", "3-4", "四分之三"),
    "front": ("front", "正面"),
    "side": ("side", "profile", "侧面"),
    "back": ("back", "rear", "背面"),
}

ROLE_ALIASES = {
    "face_close": "face",
    "hair_detail": "hair",
    "outfit_detail": "outfit",
    "weapon_detail": "weapon",
    "figure": "figure_front",
    "other": "detail",
}

REQUIRED_ROLE_PRESETS: dict[str, list[str]] = {
    "GENERIC": ["front", "side"],
    "ANIME": ["front", "side", "face"],
    "SAO": ["front", "side", "face"],
}

OPTIONAL_ROLE_PRESETS: dict[str, list[str]] = {
    "GENERIC": ["back", "three_quarter", "face", "detail"],
    "ANIME": ["back", "three_quarter", "hair", "outfit", "weapon", "pose"],
    "SAO": [
        "back",
        "three_quarter",
        "hair",
        "outfit",
        "weapon",
        "pose",
        "figure_front",
        "figure_side",
    ],
}

ROLE_ORDER = [
    "front",
    "side",
    "back",
    "three_quarter",
    "face",
    "hair",
    "outfit",
    "weapon",
    "pose",
    "detail",
    "figure_front",
    "figure_side",
    "figure_back",
]


def _ensure_object_mode() -> None:
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def _ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def _clear_collection(collection_name: str) -> None:
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        return
    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def _link_only_to_collection(obj: bpy.types.Object, collection_name: str) -> bpy.types.Collection:
    col = _ensure_collection(collection_name)
    for user_col in list(obj.users_collection):
        user_col.objects.unlink(obj)
    col.objects.link(obj)
    return col


def _normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    normalized = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "_", lowered)
    return normalized.strip("_")


def _match_aliases(stem: str, aliases: list[str]) -> bool:
    if not aliases:
        return True
    normalized_stem = _normalize_text(stem)
    return any(alias and alias in normalized_stem for alias in aliases)


def _canonical_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def _load_reference_manifest(reference_dir: Path) -> dict[str, Any]:
    manifest_path = reference_dir / REFERENCE_MANIFEST_NAME
    if not manifest_path.exists():
        return {}

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    return payload


def _manifest_character_spec(
    manifest: dict[str, Any],
    *,
    character_name: str,
    aliases: list[str],
) -> dict[str, Any] | None:
    if not manifest:
        return None

    characters = manifest.get("characters", manifest)
    if not isinstance(characters, dict):
        return None

    alias_set = {token for token in aliases if token}
    alias_set.add(_normalize_text(character_name))

    for key, spec in characters.items():
        if not isinstance(spec, dict):
            continue
        spec_aliases = [_normalize_text(key)]
        spec_aliases.extend(_normalize_text(str(item)) for item in spec.get("aliases", []) if item)
        if alias_set.intersection(spec_aliases):
            return spec
    return None


def _collect_manifest_entries(
    reference_dir: Path,
    *,
    manifest: dict[str, Any],
    character_name: str,
    aliases: list[str],
) -> list[dict[str, str]]:
    spec = _manifest_character_spec(manifest, character_name=character_name, aliases=aliases)
    if not spec:
        return []

    entries: list[dict[str, str]] = []
    for item in spec.get("entries", []):
        if not isinstance(item, dict):
            continue

        role = _canonical_role(str(item.get("role", "")).strip())
        file_value = str(item.get("file") or item.get("name") or item.get("path") or "").strip()
        if not role or role not in ROLE_ORDER:
            continue
        if not file_value:
            continue

        path = Path(file_value).expanduser()
        if not path.is_absolute():
            path = reference_dir / path
        try:
            path = path.resolve()
        except OSError:
            path = path.absolute()

        if not path.exists() or not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        entries.append({"name": path.name, "path": str(path), "role": role})

    return entries


def _classify_role(stem: str) -> str:
    normalized_stem = _normalize_text(stem)
    for role, patterns in ROLE_PATTERNS.items():
        if any(pattern in normalized_stem for pattern in patterns):
            return _canonical_role(role)
    return "detail"


def _detect_role(stem: str, aliases: list[str]) -> str | None:
    normalized_stem = _normalize_text(stem)
    for alias in aliases:
        if normalized_stem == alias:
            return "front"

        if normalized_stem.startswith(f"figure_{alias}_"):
            suffix = normalized_stem[len(f"figure_{alias}_") :]
            if suffix == "front":
                return "figure_front"
            if suffix in {"side", "profile"}:
                return "figure_side"
            if suffix == "back":
                return "figure_back"

        if not (normalized_stem == alias or normalized_stem.startswith(f"{alias}_")):
            continue

        suffix = normalized_stem[len(alias) :].strip("_")
        if suffix in {"front", "full_front", "正面"}:
            return "front"
        if suffix in {"side", "profile", "侧面"}:
            return "side"
        if suffix in {"back", "背面"}:
            return "back"
        if suffix in {"three_quarter", "threequarter", "threeq", "3q", "34", "四分之三"}:
            return "three_quarter"
        if suffix in {
            "face",
            "face_close",
            "face_closeup",
            "close_face",
            "bust",
            "面部特写",
            "脸部特写",
        }:
            return "face"
        if suffix.startswith("pose") or "动作" in suffix or "姿态" in suffix:
            return "pose"
        if "weapon" in suffix or suffix in {"逐暗者", "闪光", "武器", "细剑", "佩剑"}:
            return "weapon"
        if suffix.startswith("hair") or "发" in suffix:
            return "hair"
        if suffix.endswith("detail") or suffix.endswith("细节"):
            if any(
                marker in suffix
                for marker in (
                    "coat",
                    "outfit",
                    "armor",
                    "costume",
                    "uniform",
                    "dress",
                    "kob",
                    "服装",
                    "胸甲",
                    "肩甲",
                    "裙",
                )
            ):
                return "outfit"
            return "detail"
    return None


def _scan_reference_pack(
    reference_dir: str,
    character_name: str,
    aliases: list[str] | None,
    preset: str,
) -> dict[str, Any]:
    ref_dir = Path(reference_dir).expanduser()
    if not ref_dir.exists() or not ref_dir.is_dir():
        return {
            "success": False,
            "error": {
                "code": "REFERENCE_DIR_NOT_FOUND",
                "message": f"Reference directory not found: {reference_dir}",
            },
        }

    normalized_aliases = [_normalize_text(character_name)]
    if aliases:
        normalized_aliases.extend(_normalize_text(alias) for alias in aliases if alias)
    normalized_aliases = sorted({alias for alias in normalized_aliases if alias})
    manifest = _load_reference_manifest(ref_dir)

    matched_files_by_path: dict[str, dict[str, str]] = {}
    files_by_role: dict[str, list[dict[str, str]]] = {}

    for path in sorted(ref_dir.iterdir()):
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if not _match_aliases(path.stem, normalized_aliases):
            continue

        normalized_stem = _normalize_text(path.stem)
        role = _detect_role(normalized_stem, normalized_aliases) or _classify_role(normalized_stem)
        role = _canonical_role(role)
        matched_files_by_path[str(path)] = {"name": path.name, "path": str(path), "role": role}

    for item in _collect_manifest_entries(
        ref_dir,
        manifest=manifest,
        character_name=character_name,
        aliases=normalized_aliases,
    ):
        matched_files_by_path[item["path"]] = item

    matched_files = list(matched_files_by_path.values())
    for item in matched_files:
        files_by_role.setdefault(item["role"], []).append(item)

    required_roles = REQUIRED_ROLE_PRESETS.get(preset, REQUIRED_ROLE_PRESETS["ANIME"])
    optional_roles = OPTIONAL_ROLE_PRESETS.get(preset, OPTIONAL_ROLE_PRESETS["ANIME"])
    missing_required = [role for role in required_roles if role not in files_by_role]
    missing_optional = [role for role in optional_roles if role not in files_by_role]

    role_summary = {role: len(files_by_role[role]) for role in ROLE_ORDER if role in files_by_role}
    if not matched_files:
        status = "no_matches"
    elif missing_required:
        status = "missing_required"
    elif missing_optional:
        status = "ready_with_gaps"
    else:
        status = "ready"

    return {
        "success": True,
        "data": {
            "character_name": character_name,
            "aliases": normalized_aliases,
            "preset": preset,
            "reference_dir": str(ref_dir),
            "manifest_used": bool(
                _manifest_character_spec(
                    manifest, character_name=character_name, aliases=normalized_aliases
                )
            ),
            "status": status,
            "matched_files_count": len(matched_files),
            "matched_files": matched_files,
            "files_by_role": files_by_role,
            "role_summary": role_summary,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
        },
    }


def _view_transform(
    view: str, offset_x: float, offset_y: float, offset_z: float
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    if view == "FRONT":
        return (offset_x, -2.0 + offset_y, offset_z), (math.pi / 2, 0.0, 0.0)
    if view == "SIDE":
        return (2.0 + offset_x, offset_y, offset_z), (math.pi / 2, 0.0, math.pi / 2)
    if view == "BACK":
        return (offset_x, 2.0 + offset_y, offset_z), (math.pi / 2, 0.0, math.pi)
    if view == "THREE_QUARTER":
        return (1.4 + offset_x, -1.4 + offset_y, offset_z), (math.pi / 2, 0.0, math.pi / 4)
    if view == "FACE":
        return (-3.5 + offset_x, -1.6 + offset_y, 1.4 + offset_z), (math.pi / 2, 0.0, 0.0)
    if view == "DETAIL":
        return (-3.5 + offset_x, 0.8 + offset_y, 1.0 + offset_z), (math.pi / 2, 0.0, 0.0)
    return (offset_x, -2.0 + offset_y, offset_z), (math.pi / 2, 0.0, 0.0)


def _pack_role_layout(
    role: str,
    index: int,
    primary_scale: float,
    detail_scale: float,
    origin: tuple[float, float, float],
) -> tuple[str, float, float, float, float]:
    origin_x, origin_y, origin_z = origin

    if role == "front":
        return "FRONT", origin_x, origin_y, origin_z + index * 0.9, primary_scale
    if role == "side":
        return "SIDE", origin_x, origin_y, origin_z + index * 0.9, primary_scale
    if role == "back":
        return "BACK", origin_x, origin_y, origin_z + index * 0.9, primary_scale
    if role == "three_quarter":
        return "THREE_QUARTER", origin_x, origin_y, origin_z + index * 0.9, primary_scale * 0.95

    detail_positions = {
        "face": (0.0, -2.4, 0.75),
        "hair": (0.0, -1.1, 0.55),
        "outfit": (0.0, 0.3, 0.2),
        "weapon": (7.0, -2.0, 0.2),
        "pose": (7.0, -0.2, 0.35),
        "detail": (3.5, 2.4, 0.2),
        "figure_front": (7.0, 1.55, 0.15),
        "figure_side": (7.0, 3.05, 0.15),
        "figure_back": (7.0, 4.55, 0.15),
    }
    offset_x, offset_y, offset_z = detail_positions.get(role, detail_positions["detail"])
    return (
        "DETAIL",
        origin_x + offset_x,
        origin_y + offset_y + index * 1.0,
        origin_z + offset_z,
        detail_scale,
    )


def _create_reference_object(
    *,
    image_path: str,
    view: str,
    name: str | None,
    collection_name: str,
    opacity: float,
    scale: float,
    offset_x: float,
    offset_y: float,
    offset_z: float,
    hide_select: bool,
) -> dict[str, Any]:
    if not os.path.exists(image_path):
        return {
            "success": False,
            "error": {"code": "FILE_NOT_FOUND", "message": f"File not found: {image_path}"},
        }

    try:
        image = bpy.data.images.load(image_path, check_existing=True)
    except Exception as exc:
        return {
            "success": False,
            "error": {"code": "LOAD_ERROR", "message": f"Failed to load image: {exc}"},
        }

    location, rotation = _view_transform(view, offset_x, offset_y, offset_z)
    image_name = Path(image_path).name
    object_name = name or f"Ref_{view}_{Path(image_name).stem}"

    bpy.ops.object.empty_add(type="IMAGE", location=location)
    ref_obj = bpy.context.active_object
    ref_obj.name = object_name
    ref_obj.data = image
    ref_obj.empty_display_size = scale
    ref_obj.empty_image_depth = "BACK"
    ref_obj.rotation_euler = rotation
    ref_obj.color[3] = opacity
    ref_obj.hide_select = hide_select

    _link_only_to_collection(ref_obj, collection_name)

    return {
        "success": True,
        "data": {
            "image_name": image_name,
            "object_name": ref_obj.name,
            "collection_name": collection_name,
            "view": view,
            "opacity": opacity,
        },
    }


def _create_proportion_guides(
    subject_name: str,
    collection_name: str,
    target_height: float,
    head_body_ratio: float,
    origin: tuple[float, float, float],
) -> list[str]:
    guide_x = origin[0] - 1.2
    guide_y = origin[1] - 2.6
    guide_z = origin[2]
    created: list[str] = []

    root = bpy.data.objects.new(f"Guide_{subject_name}_Root", None)
    root.empty_display_type = "ARROWS"
    root.empty_display_size = 0.12
    root.location = (guide_x, guide_y, guide_z)
    bpy.context.scene.collection.objects.link(root)
    _link_only_to_collection(root, collection_name)
    root.hide_select = True
    created.append(root.name)

    bpy.ops.mesh.primitive_cube_add(
        size=1.0, location=(guide_x, guide_y, guide_z + target_height * 0.5)
    )
    height_line = bpy.context.active_object
    height_line.name = f"Guide_{subject_name}_Height"
    height_line.scale = (0.008, 0.008, target_height * 0.5)
    height_line.parent = root
    height_line.hide_select = True
    _link_only_to_collection(height_line, collection_name)
    created.append(height_line.name)

    head_unit = target_height / max(head_body_ratio, 1.0)
    divisions = max(2, int(round(head_body_ratio)))
    for idx in range(divisions + 1):
        z = guide_z + head_unit * idx
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(guide_x, guide_y, z))
        marker = bpy.context.active_object
        marker.name = f"Guide_{subject_name}_Head_{idx}"
        marker.scale = (0.18, 0.004, 0.004)
        marker.parent = root
        marker.hide_select = True
        _link_only_to_collection(marker, collection_name)
        created.append(marker.name)

    return created


def handle_load_image(params: dict[str, Any]) -> dict[str, Any]:
    """Load one reference image into the scene."""
    _ensure_object_mode()

    return _create_reference_object(
        image_path=params.get("image_path", ""),
        view=params.get("view", "FRONT"),
        name=params.get("name"),
        collection_name=params.get("collection_name", "References"),
        opacity=params.get("opacity", 0.5),
        scale=params.get("scale", 1.0),
        offset_x=params.get("offset_x", 0.0),
        offset_y=params.get("offset_y", 0.0),
        offset_z=params.get("offset_z", 0.0),
        hide_select=params.get("hide_select", True),
    )


def handle_load_sheet(params: dict[str, Any]) -> dict[str, Any]:
    """Load a multi-view reference board for one subject."""
    _ensure_object_mode()

    subject_name = params.get("subject_name", "Subject")
    collection_name = params.get("collection_name") or f"References_{subject_name}"
    opacity = params.get("opacity", 0.5)
    scale = params.get("scale", 1.0)
    hide_select = params.get("hide_select", True)

    views = [
        ("front_image", "FRONT", f"Ref_{subject_name}_Front"),
        ("side_image", "SIDE", f"Ref_{subject_name}_Side"),
        ("back_image", "BACK", f"Ref_{subject_name}_Back"),
        ("face_image", "FACE", f"Ref_{subject_name}_Face"),
    ]

    loaded_objects: list[str] = []
    missing_required = True

    for key, view, name in views:
        image_path = params.get(key)
        if not image_path:
            continue
        missing_required = False
        result = _create_reference_object(
            image_path=image_path,
            view=view,
            name=name,
            collection_name=collection_name,
            opacity=opacity,
            scale=scale,
            offset_x=0.0,
            offset_y=0.0,
            offset_z=0.0,
            hide_select=hide_select,
        )
        if not result.get("success"):
            return result
        loaded_objects.append(result["data"]["object_name"])

    detail_images = params.get("detail_images") or []
    for index, image_path in enumerate(detail_images):
        result = _create_reference_object(
            image_path=image_path,
            view="DETAIL",
            name=f"Ref_{subject_name}_Detail_{index + 1}",
            collection_name=collection_name,
            opacity=opacity,
            scale=max(0.5, scale * 0.8),
            offset_x=0.0,
            offset_y=index * 1.3,
            offset_z=0.0,
            hide_select=hide_select,
        )
        if not result.get("success"):
            return result
        loaded_objects.append(result["data"]["object_name"])

    if missing_required and not detail_images:
        return {
            "success": False,
            "error": {
                "code": "MISSING_INPUT",
                "message": "No reference images were provided for the sheet.",
            },
        }

    return {
        "success": True,
        "data": {
            "subject_name": subject_name,
            "collection_name": collection_name,
            "loaded_objects": loaded_objects,
        },
    }


def handle_inspect_pack(params: dict[str, Any]) -> dict[str, Any]:
    """Inspect a character reference directory."""
    return _scan_reference_pack(
        params.get("reference_dir", ""),
        params.get("character_name", "Character"),
        params.get("aliases"),
        params.get("preset", "ANIME"),
    )


def handle_setup_pack(params: dict[str, Any]) -> dict[str, Any]:
    """Inspect and load a character reference pack into Blender."""
    _ensure_object_mode()

    if params.get("matched_files"):
        matched_files = []
        for item in params.get("matched_files", []):
            canonical_item = dict(item)
            canonical_item["role"] = _canonical_role(str(item.get("role", "detail")))
            matched_files.append(canonical_item)

        scan_data = {
            "character_name": params.get("character_name", "Character"),
            "preset": params.get("preset", "ANIME"),
            "reference_dir": params.get("reference_dir", ""),
            "matched_files": matched_files,
            "matched_files_count": len(matched_files),
            "missing_required": [
                _canonical_role(str(role)) for role in params.get("missing_required", [])
            ],
            "missing_optional": [
                _canonical_role(str(role)) for role in params.get("missing_optional", [])
            ],
            "status": (
                "missing_required"
                if params.get("missing_required")
                else "ready_with_gaps" if params.get("missing_optional") else "ready"
            ),
        }
        files_by_role: dict[str, list[dict[str, str]]] = {}
        for item in scan_data["matched_files"]:
            files_by_role.setdefault(item["role"], []).append(item)
        scan_data["files_by_role"] = files_by_role
        scan_data["role_summary"] = {
            role: len(files_by_role[role]) for role in ROLE_ORDER if role in files_by_role
        }
    else:
        scan_result = _scan_reference_pack(
            params.get("reference_dir", ""),
            params.get("character_name", "Character"),
            params.get("aliases"),
            params.get("preset", "ANIME"),
        )
        if not scan_result.get("success"):
            return scan_result
        scan_data = scan_result.get("data", {})

    if scan_data.get("matched_files_count", 0) == 0:
        return {
            "success": False,
            "error": {
                "code": "NO_REFERENCES_FOUND",
                "message": "No matching reference images found for the requested character",
            },
        }

    subject_name = scan_data.get("character_name", "Character")
    collection_name = params.get("collection_name") or f"References_{subject_name}"
    opacity = params.get("opacity", 0.55)
    primary_scale = params.get("primary_scale", 1.6)
    detail_scale = params.get("detail_scale", 0.95)
    hide_select = params.get("hide_select", True)
    origin_list = params.get("origin", [0.0, 0.0, 0.0])
    origin = (
        float(origin_list[0]) if len(origin_list) > 0 else 0.0,
        float(origin_list[1]) if len(origin_list) > 1 else 0.0,
        float(origin_list[2]) if len(origin_list) > 2 else 0.0,
    )

    if params.get("replace_existing", True):
        _clear_collection(collection_name)

    loaded_objects: list[str] = []
    loaded_roles: dict[str, int] = {}
    files_by_role = scan_data.get("files_by_role", {})

    for role in ROLE_ORDER:
        for index, item in enumerate(files_by_role.get(role, [])):
            view, offset_x, offset_y, offset_z, scale = _pack_role_layout(
                role, index, primary_scale, detail_scale, origin
            )
            result = _create_reference_object(
                image_path=item["path"],
                view=view,
                name=f"Ref_{subject_name}_{role}_{index + 1}",
                collection_name=collection_name,
                opacity=opacity,
                scale=scale,
                offset_x=offset_x,
                offset_y=offset_y,
                offset_z=offset_z,
                hide_select=hide_select,
            )
            if not result.get("success"):
                return result
            loaded_objects.append(result["data"]["object_name"])
            loaded_roles[role] = loaded_roles.get(role, 0) + 1

    guide_objects: list[str] = []
    if params.get("create_proportion_guides", True):
        guide_objects = _create_proportion_guides(
            subject_name,
            collection_name,
            float(params.get("target_height", 1.7)),
            float(params.get("head_body_ratio", 5.5)),
            origin,
        )

    return {
        "success": True,
        "data": {
            **scan_data,
            "collection_name": collection_name,
            "loaded_count": len(loaded_objects),
            "loaded_objects": loaded_objects,
            "loaded_roles": loaded_roles,
            "guide_objects": guide_objects,
            "target_height": float(params.get("target_height", 1.7)),
            "head_body_ratio": float(params.get("head_body_ratio", 5.5)),
        },
    }


def handle_update_image(params: dict[str, Any]) -> dict[str, Any]:
    """Update properties of an existing reference object."""
    _ensure_object_mode()

    object_name = params.get("object_name", "")
    obj = bpy.data.objects.get(object_name)
    if obj is None:
        return {
            "success": False,
            "error": {"code": "OBJECT_NOT_FOUND", "message": f"Object not found: {object_name}"},
        }
    if obj.type != "EMPTY":
        return {
            "success": False,
            "error": {
                "code": "INVALID_OBJECT_TYPE",
                "message": f"Object is not a reference Empty: {object_name}",
            },
        }

    opacity = params.get("opacity")
    scale = params.get("scale")
    hide_select = params.get("hide_select")
    hide_render = params.get("hide_render")

    if opacity is not None:
        obj.color[3] = opacity
    if scale is not None:
        obj.empty_display_size = scale
    if hide_select is not None:
        obj.hide_select = hide_select
    if hide_render is not None:
        obj.hide_render = hide_render

    return {"success": True, "data": {"object_name": object_name}}


def handle_clear(params: dict[str, Any]) -> dict[str, Any]:
    """Remove reference image objects from the scene."""
    _ensure_object_mode()

    collection_name = params.get("collection_name", "")
    name_prefix = params.get("name_prefix", "Ref_")
    remove_collection_if_empty = params.get("remove_collection_if_empty", True)

    target_collection = bpy.data.collections.get(collection_name) if collection_name else None

    objects_to_remove: list[bpy.types.Object] = []
    for obj in list(bpy.data.objects):
        if obj.type != "EMPTY" or not obj.name.startswith(name_prefix):
            continue
        if target_collection is not None and target_collection.objects.get(obj.name) is None:
            continue
        objects_to_remove.append(obj)

    removed_count = 0
    for obj in objects_to_remove:
        bpy.data.objects.remove(obj, do_unlink=True)
        removed_count += 1

    if target_collection and remove_collection_if_empty and len(target_collection.objects) == 0:
        bpy.data.collections.remove(target_collection)

    return {
        "success": True,
        "data": {
            "removed_count": removed_count,
            "collection_name": collection_name,
        },
    }
