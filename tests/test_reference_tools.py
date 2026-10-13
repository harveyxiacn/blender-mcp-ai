"""Tests for reference-driven character tools."""

from __future__ import annotations

from pathlib import Path

import pytest

from blender_mcp.tools.reference import (
    build_reference_brief,
    build_reference_model_audit,
    inspect_reference_pack_data,
)

SAO_EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "刀剑神域"


def _require_sao_examples() -> None:
    """Skip when the SAO examples are absent.

    They were removed from the repository as copyrighted fan-art assets, so the
    tests that use them as a fixture have nothing to assert against.
    """
    if not SAO_EXAMPLES.exists():
        pytest.skip("examples/刀剑神域 is absent (copyrighted examples removed)")


def _touch_image(path: Path) -> None:
    path.write_bytes(b"fake-image")


def test_inspect_reference_pack_data_detects_sao_roles(tmp_path: Path) -> None:
    _touch_image(tmp_path / "kirito_front.png")
    _touch_image(tmp_path / "kirito_side.png")
    _touch_image(tmp_path / "kirito_back.png")
    _touch_image(tmp_path / "kirito_face_close.png")
    _touch_image(tmp_path / "kirito_coat_detail.png")
    _touch_image(tmp_path / "kirito_weapon_elucidator.png")
    _touch_image(tmp_path / "kirito_pose_ref.png")
    _touch_image(tmp_path / "figure_kirito_side.png")

    report = inspect_reference_pack_data(
        reference_dir=str(tmp_path),
        character_name="kirito",
        preset="SAO",
    )

    assert report["status"] == "ready_with_gaps"
    assert report["role_summary"]["front"] == 1
    assert report["role_summary"]["weapon"] == 1
    assert report["role_summary"]["outfit"] == 1
    assert report["role_summary"]["pose"] == 1
    assert report["role_summary"]["figure_side"] == 1


def test_inspect_reference_pack_data_supports_aliases(tmp_path: Path) -> None:
    _touch_image(tmp_path / "桐人_正面.png")
    _touch_image(tmp_path / "桐人_侧面.png")
    _touch_image(tmp_path / "桐人_背面.png")
    _touch_image(tmp_path / "桐人_面部特写.png")
    _touch_image(tmp_path / "桐人_服装细节.png")
    _touch_image(tmp_path / "桐人_逐暗者.png")

    report = inspect_reference_pack_data(
        reference_dir=str(tmp_path),
        character_name="kirito",
        aliases=["桐人"],
        preset="SAO",
    )

    assert report["matched_files_count"] == 6
    assert report["status"] == "ready_with_gaps"
    assert not report["missing_required"]


def test_inspect_reference_pack_data_treats_exact_alias_as_front(tmp_path: Path) -> None:
    _touch_image(tmp_path / "桐人.png")
    _touch_image(tmp_path / "桐人_侧面.png")
    _touch_image(tmp_path / "桐人_面部特写.png")

    report = inspect_reference_pack_data(
        reference_dir=str(tmp_path),
        character_name="kirito",
        aliases=["桐人"],
        preset="SAO",
    )

    assert report["role_summary"]["front"] == 1
    assert not report["missing_required"]


def test_inspect_reference_pack_data_uses_manifest_entries(tmp_path: Path) -> None:
    _touch_image(tmp_path / "asuna.jpg")
    _touch_image(tmp_path / "asuna-side-shot.jpg")
    _touch_image(tmp_path / "asuna-weapon.jpg")
    (tmp_path / "reference_manifest.json").write_text(
        """
        {
          "characters": {
            "asuna": {
              "aliases": ["亚丝娜"],
              "entries": [
                {"file": "asuna.jpg", "role": "front"},
                {"file": "asuna-side-shot.jpg", "role": "side"},
                {"file": "asuna-weapon.jpg", "role": "weapon"}
              ]
            }
          }
        }
        """.strip(),
        encoding="utf-8",
    )

    report = inspect_reference_pack_data(
        reference_dir=str(tmp_path),
        character_name="asuna",
        aliases=["亚丝娜"],
        preset="SAO",
    )

    assert report["manifest_used"] is True
    assert report["matched_files_count"] == 3
    assert report["role_summary"]["side"] == 1
    assert report["role_summary"]["weapon"] == 1
    assert report["missing_required"] == ["face"]


def test_build_reference_brief_without_provider_uses_heuristics(tmp_path: Path) -> None:
    _touch_image(tmp_path / "asuna_front.png")
    _touch_image(tmp_path / "asuna_side.png")
    _touch_image(tmp_path / "asuna_back.png")
    _touch_image(tmp_path / "asuna_face_close.png")
    _touch_image(tmp_path / "asuna_hair_detail.png")
    _touch_image(tmp_path / "asuna_kob_outfit_detail.png")

    brief = build_reference_brief(
        reference_dir=str(tmp_path),
        character_name="asuna",
        preset="SAO",
        franchise="Sword Art Online",
        target_style="anime",
        notes="Keep the KoB silhouette sharp.",
        provider="none",
    )

    assert brief["character_name"] == "asuna"
    assert brief["vision_analysis"] is None
    assert any("face close-up" in item.lower() for item in brief["must_match_features"])
    assert any("KoB silhouette sharp." in item for item in brief["notes"])


class _NoopServer:
    async def execute_command(
        self, category: str, action: str, params: dict[str, object]
    ) -> dict[str, object]:
        raise AssertionError(
            f"Unexpected Blender command during fallback audit: {category}.{action}"
        )


async def test_build_reference_model_audit_without_provider_uses_checklist(tmp_path: Path) -> None:
    _touch_image(tmp_path / "kirito_front.png")
    _touch_image(tmp_path / "kirito_side.png")
    _touch_image(tmp_path / "kirito_face_close.png")
    _touch_image(tmp_path / "kirito_coat_detail.png")
    _touch_image(tmp_path / "kirito_weapon_elucidator.png")
    _touch_image(tmp_path / "review_render.png")

    audit = await build_reference_model_audit(
        _NoopServer(),
        reference_dir=str(tmp_path),
        character_name="kirito",
        preset="SAO",
        provider="none",
        review_image_paths=[str(tmp_path / "review_render.png")],
        capture_viewport=False,
        capture_render_preview=False,
    )

    assert audit["analysis_mode"] == "checklist"
    assert audit["character_name"] == "kirito"
    assert audit["selected_review_images"] == ["review_render.png"]
    assert audit["reference_status"] in {"missing_required", "ready_with_gaps", "ready"}
    assert audit["issues"]


def test_reference_tool_source_registers_model_audit_tool() -> None:
    source = (
        Path(__file__).resolve().parent.parent / "src" / "blender_mcp" / "tools" / "reference.py"
    ).read_text(encoding="utf-8")
    assert 'name="blender_reference_model_audit"' in source


def test_sao_reference_workflow_script_wires_reference_pipeline() -> None:
    _require_sao_examples()
    source = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "刀剑神域"
        / "scripts"
        / "run_reference_workflow.py"
    ).read_text(encoding="utf-8")

    assert "inspect_reference_pack_data" in source
    assert '"reference",' in source and '"setup_pack"' in source
    assert "build_reference_brief" in source
    assert "build_reference_model_audit" in source
    assert "SAO_REFERENCE_BRIEF_PATH" in source


def test_sao_reference_manifest_exists() -> None:
    _require_sao_examples()
    path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "刀剑神域"
        / "references"
        / "reference_manifest.json"
    )
    assert path.exists()
