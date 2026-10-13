"""Smoke tests for the SAO reference workflow example script."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_sao_reference_workflow_script_uses_reference_pipeline() -> None:
    script_path = REPO_ROOT / "examples" / "刀剑神域" / "scripts" / "run_reference_workflow.py"
    if not script_path.exists():
        pytest.skip("examples/刀剑神域 is absent (copyrighted examples removed)")
    source = script_path.read_text(encoding="utf-8")

    assert "inspect_reference_pack_data" in source
    assert "build_reference_brief" in source
    assert "build_reference_model_audit" in source
    assert '"reference"' in source
    assert '"setup_pack"' in source
    assert "--skip-build" in source


def test_addon_reference_handler_supports_exact_alias_front_files() -> None:
    handler_path = REPO_ROOT / "addon" / "blender_mcp_addon" / "handlers" / "reference.py"
    source = handler_path.read_text(encoding="utf-8")

    assert "normalized_stem == alias" in source
    assert "_detect_role(normalized_stem, normalized_aliases)" in source
