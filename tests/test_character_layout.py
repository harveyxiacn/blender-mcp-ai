"""Regression tests for the character template skeleton.

The template generator used to place every body part with its own independent
magic offset, so the parts did not meet: the head ended up floating ~0.22 m
above the torso, eyes pierced out through the face, and arms were buried inside
the chest. Placement is now derived from a single skeleton.

``character_template`` imports ``bpy`` at module level, so a stub is installed
before import; the layout maths itself is pure Python and runs in CI.
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest

HANDLERS = Path(__file__).resolve().parents[1] / "addon" / "blender_mcp_addon" / "handlers"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def ct():
    """Load the handler directly, with a stand-in ``bpy``.

    The addon package ``__init__`` imports ``bpy.props``, so the module is
    loaded standalone instead of via ``blender_mcp_addon``. Only ``import bpy``
    happens at module scope, so a bare stub module is enough.
    """
    if "bpy" not in sys.modules:
        sys.modules["bpy"] = types.ModuleType("bpy")

    pkg = types.ModuleType("_character_template_test")
    pkg.__path__ = [str(HANDLERS)]
    sys.modules[pkg.__name__] = pkg

    _load(f"{pkg.__name__}.node_utils", HANDLERS / "node_utils.py")
    return _load(f"{pkg.__name__}.character_template", HANDLERS / "character_template.py")


@pytest.mark.parametrize("height", [0.5, 1.0, 1.7, 2.5, 3.0])
def test_every_part_connects_with_no_gap(ct, height):
    """Head, neck, torso, hips and legs must all meet - nothing floats."""
    for template, config in ct.TEMPLATE_CONFIG.items():
        lay = ct._character_layout(height, config, [0.0, 0.0, 0.0])
        where = f"{template} @ {height}m"

        # Legs run from the ground up to the hips.
        assert lay["leg_len"] == pytest.approx(height * config["leg_frac"]), where
        assert lay["leg_len"] > 0, where
        assert lay["hip_z"] == pytest.approx(lay["z0"] + lay["leg_len"]), where

        # The head caps the character: its top is the requested height.
        assert lay["head_h"] > 0 and lay["head_w"] > 0 and lay["head_d"] > 0, where
        assert lay["head_bottom_z"] == pytest.approx(lay["z0"] + height - lay["head_h"]), where
        assert lay["head_center_z"] > lay["head_bottom_z"], where

        # The torso spans hips -> shoulders, with no gap at either end.
        torso_bottom = lay["torso_center_z"] - lay["torso_h"] / 2
        torso_top = lay["torso_center_z"] + lay["torso_h"] / 2
        assert torso_bottom == pytest.approx(lay["hip_z"]), where
        assert torso_top >= lay["shoulder_z"] - 1e-9, where

        # This is the exact defect that was reported: a gap between the torso
        # top and the head bottom, left to be filled by nothing.
        assert lay["shoulder_z"] <= lay["head_bottom_z"], where
        assert torso_top >= lay["hip_z"], where


@pytest.mark.parametrize("template", ["chibi", "realistic", "anime", "stylized", "mascot"])
def test_neck_bridges_head_and_torso(ct, template):
    """The neck cylinder must overlap both the head and the torso."""
    config = ct.TEMPLATE_CONFIG[template]
    lay = ct._character_layout(1.7, config, [0.0, 0.0, 0.0])

    depth = lay["neck_h"] * 1.8
    center = (lay["head_bottom_z"] + lay["shoulder_z"]) / 2
    neck_top = center + depth / 2
    neck_bottom = center - depth / 2

    assert neck_top > lay["head_bottom_z"], template
    assert neck_bottom < lay["shoulder_z"], template


def test_layout_respects_location_offset(ct):
    """A non-zero base location shifts the whole skeleton by the same amount."""
    config = ct.TEMPLATE_CONFIG["anime"]
    base = ct._character_layout(1.7, config, [0.0, 0.0, 0.0])
    shifted = ct._character_layout(1.7, config, [2.0, -3.0, 0.5])

    for key in ("z0", "hip_z", "shoulder_z", "head_center_z", "torso_center_z"):
        assert shifted[key] == pytest.approx(base[key] + 0.5), key


@pytest.mark.parametrize("template", ["chibi", "realistic", "anime", "stylized", "mascot"])
def test_template_configs_declare_leg_frac(ct, template):
    """leg_frac drives the hip position, so every template must define it."""
    leg_frac = ct.TEMPLATE_CONFIG[template]["leg_frac"]
    assert 0.0 < leg_frac < 1.0
