"""Tests for the SAO reference-brief runtime helpers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def _load_runtime_module():
    module_path = (
        Path(__file__).resolve().parent.parent
        / "examples"
        / "刀剑神域"
        / "scripts"
        / "reference_brief_runtime.py"
    )
    if not module_path.exists():
        pytest.skip("examples/刀剑神域 is absent (copyrighted examples removed)")
    spec = importlib.util.spec_from_file_location("reference_brief_runtime", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_get_reference_tuning_uses_brief_keywords(tmp_path: Path, monkeypatch) -> None:
    runtime = _load_runtime_module()

    brief_path = tmp_path / "brief.json"
    brief_path.write_text(
        json.dumps(
            {
                "status": "ready_with_gaps",
                "must_match_features": [
                    "Protect the long hair flow and the KoB armor silhouette.",
                    "Keep the pleated skirt readable.",
                ],
                "notes": ["Long hair over waist and large anime eyes."],
                "vision_analysis": {
                    "body": {"build": "slender athletic"},
                    "hair": {"cut": "very long flowing hair"},
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SAO_REFERENCE_BRIEF_PATH", str(brief_path))

    tuning = runtime.get_reference_tuning("asuna")

    assert tuning["brief_path"] == str(brief_path.resolve())
    assert tuning["eye_scale"] > runtime.CHARACTER_DEFAULTS["asuna"]["eye_scale"]
    assert (
        tuning["back_hair_length_scale"]
        > runtime.CHARACTER_DEFAULTS["asuna"]["back_hair_length_scale"]
    )
    assert tuning["armor_width_scale"] > runtime.CHARACTER_DEFAULTS["asuna"]["armor_width_scale"]
    assert tuning["skirt_flare_scale"] > runtime.CHARACTER_DEFAULTS["asuna"]["skirt_flare_scale"]
    assert tuning["torso_width_scale"] < runtime.CHARACTER_DEFAULTS["asuna"]["torso_width_scale"]


def test_scale_loft_profiles_keeps_top_anchor() -> None:
    runtime = _load_runtime_module()

    profiles = [
        (1.6, 0.1, 0.1, 0.0, 0.0),
        (1.2, 0.2, 0.2, 0.0, 0.0),
        (0.8, 0.3, 0.3, 0.0, 0.0),
    ]
    scaled = runtime.scale_loft_profiles(
        profiles,
        radius_x=1.1,
        radius_y=0.9,
        span_scale=1.5,
        anchor="top",
    )

    assert scaled[0][0] == profiles[0][0]
    assert scaled[-1][0] < profiles[-1][0]
    assert scaled[-1][1] == profiles[-1][1] * 1.1
    assert scaled[-1][2] == profiles[-1][2] * 0.9


def test_scale_hair_entries_updates_lengths_and_widths() -> None:
    runtime = _load_runtime_module()

    entries = [
        (0.0, 0.0, 1.0, (60, 0, 0), 0.2, 0.04, 0.01),
        (0.1, 0.0, 1.0, (65, 0, 5), 0.15, 0.03, 0.008),
    ]
    scaled = runtime.scale_hair_entries(entries, length_scale=1.2, width_scale=1.1)

    assert scaled[0][4] == pytest.approx(0.24)
    assert scaled[0][5] == pytest.approx(0.044)
    assert scaled[1][6] == pytest.approx(0.0088)
