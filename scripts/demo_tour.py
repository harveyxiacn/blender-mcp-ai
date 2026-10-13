"""Build a layered demo scene in a running Blender, then tell you how to inspect it.

Every step goes through the MCP socket, so this exercises the same code path a
real client uses. Each group of objects lands in its own collection (``L1_`` ..
``L9_``) so you can toggle one layer at a time in the Outliner.

Usage::

    1. Open Blender and enable the Blender MCP addon (it listens on :9876)
    2. uv run python scripts/demo_tour.py
    3. Read the walkthrough it prints, and inspect the L1_..L9_ collections

Add ``--clean`` to empty the scene first. Without it the demo is additive.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

# The layer names are Chinese; Windows consoles default to a legacy code page
# and would mangle them.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from blender_mcp.connection import BlenderConnection, BlenderConnectionError  # noqa: E402

# (category, action, params)
Op = tuple[str, str, dict[str, Any]]
Layer = tuple[str, str, list[Op]]

LAYERS: list[Layer] = [
    (
        "L1_场景基础",
        "Objects and transforms - select a cube and press N to read its transform",
        [
            (
                "object",
                "create",
                {"type": "PLANE", "name": "L1_Ground", "mesh_params": {"size": 16}},
            ),
            ("object", "create", {"type": "CUBE", "name": "L1_Cube", "location": [-2.2, 0, 0.5]}),
            ("object", "create", {"type": "SPHERE", "name": "L1_Sphere", "location": [0, 0, 0.6]}),
            ("object", "create", {"type": "CONE", "name": "L1_Cone", "location": [2.2, 0, 0.5]}),
            ("object", "transform", {"name": "L1_Cube", "scale": [0.6, 0.6, 0.6]}),
        ],
    ),
    (
        "L2_建模",
        "Modifiers - open the blue wrench tab and toggle each one off and on",
        [
            (
                "object",
                "create",
                {"type": "CUBE", "name": "L2_Bevel", "location": [-3.0, -2.6, 0.5]},
            ),
            (
                "modeling",
                "modifier_add",
                {
                    "object_name": "L2_Bevel",
                    "modifier_type": "BEVEL",
                    "settings": {"width": 0.12, "segments": 3},
                },
            ),
            (
                "object",
                "create",
                {"type": "CUBE", "name": "L2_Subdiv", "location": [-1.0, -2.6, 0.5]},
            ),
            (
                "modeling",
                "modifier_add",
                {"object_name": "L2_Subdiv", "modifier_type": "SUBSURF", "settings": {"levels": 2}},
            ),
            (
                "object",
                "create",
                {"type": "CUBE", "name": "L2_BoolA", "location": [1.0, -2.6, 0.5]},
            ),
            (
                "object",
                "create",
                {"type": "CYLINDER", "name": "L2_BoolB", "location": [1.0, -2.6, 1.1]},
            ),
            (
                "modeling",
                "boolean",
                {
                    "object_name": "L2_BoolA",
                    "target_name": "L2_BoolB",
                    "operation": "DIFFERENCE",
                    "apply": True,
                },
            ),
            (
                "object",
                "create",
                {"type": "SPHERE", "name": "L2_Subd", "location": [3.0, -2.6, 0.5]},
            ),
            ("modeling", "subdivide", {"object_name": "L2_Subd", "cuts": 2}),
        ],
    ),
    (
        "L3_材质",
        "Materials - press Z and pick Material Preview to see metal vs plastic",
        [
            (
                "object",
                "create",
                {"type": "SPHERE", "name": "L3_Gold", "location": [-3.0, 2.6, 0.6]},
            ),
            (
                "material",
                "create",
                {
                    "name": "M_Gold",
                    "color": [0.95, 0.77, 0.28, 1.0],
                    "metallic": 1.0,
                    "roughness": 0.15,
                },
            ),
            ("material", "assign", {"object_name": "L3_Gold", "material_name": "M_Gold"}),
            (
                "object",
                "create",
                {"type": "SPHERE", "name": "L3_Red", "location": [-1.0, 2.6, 0.6]},
            ),
            (
                "material",
                "create",
                {
                    "name": "M_Red",
                    "color": [0.85, 0.12, 0.16, 1.0],
                    "metallic": 0.0,
                    "roughness": 0.3,
                },
            ),
            ("material", "assign", {"object_name": "L3_Red", "material_name": "M_Red"}),
        ],
    ),
    (
        "L4_灯光相机",
        "Three-point lighting - press Z and pick Rendered, then select the lights",
        [
            (
                "lighting",
                "create",
                {
                    "type": "AREA",
                    "name": "L4_Key",
                    "location": [4, -5, 6],
                    "energy": 700,
                    "radius": 3,
                },
            ),
            (
                "lighting",
                "create",
                {
                    "type": "AREA",
                    "name": "L4_Fill",
                    "location": [-5, -3, 3],
                    "energy": 220,
                    "radius": 5,
                },
            ),
            (
                "lighting",
                "create",
                {
                    "type": "AREA",
                    "name": "L4_Rim",
                    "location": [-2, 5, 4],
                    "energy": 450,
                    "radius": 2,
                },
            ),
            ("camera", "create", {"name": "L4_Cam", "location": [8.5, -12.5, 6.0], "lens": 45}),
            ("camera", "look_at", {"camera_name": "L4_Cam", "target": [0, 0.5, 0.9]}),
            ("world", "background", {"color": [0.05, 0.06, 0.08, 1.0]}),
        ],
    ),
    (
        "L5_UV",
        "UV unwrap - open a UV Editor, select the box, Tab + A to show the layout",
        [
            ("object", "create", {"type": "CUBE", "name": "L5_UVBox", "location": [0, -5.4, 0.7]}),
            (
                "uv",
                "smart_project",
                {"object_name": "L5_UVBox", "angle_limit": 66.0, "island_margin": 0.02},
            ),
        ],
    ),
    (
        "L6_动画",
        "Animation - scrub to frame 1 and press Space to play",
        [
            (
                "object",
                "create",
                {"type": "CUBE", "name": "L6_Bounce", "location": [-2.2, 4.6, 0.5]},
            ),
            (
                "material",
                "create",
                {
                    "name": "M_Anim",
                    "color": [0.15, 0.55, 0.85, 1.0],
                    "metallic": 0.2,
                    "roughness": 0.3,
                },
            ),
            ("material", "assign", {"object_name": "L6_Bounce", "material_name": "M_Anim"}),
            (
                "animation",
                "keyframe_insert",
                {
                    "object_name": "L6_Bounce",
                    "data_path": "location",
                    "frame": 1,
                    "value": [-2.2, 4.6, 0.5],
                },
            ),
            (
                "animation",
                "keyframe_insert",
                {
                    "object_name": "L6_Bounce",
                    "data_path": "location",
                    "frame": 20,
                    "value": [-2.2, 4.6, 3.0],
                },
            ),
            (
                "animation",
                "keyframe_insert",
                {
                    "object_name": "L6_Bounce",
                    "data_path": "location",
                    "frame": 40,
                    "value": [-2.2, 4.6, 0.5],
                },
            ),
            (
                "animation",
                "keyframe_insert",
                {
                    "object_name": "L6_Bounce",
                    "data_path": "rotation_euler",
                    "frame": 1,
                    "value": [0, 0, 0],
                },
            ),
            (
                "animation",
                "keyframe_insert",
                {
                    "object_name": "L6_Bounce",
                    "data_path": "rotation_euler",
                    "frame": 40,
                    "value": [0, 0, 6.283],
                },
            ),
            (
                "scene",
                "set_settings",
                {"scene_name": "Scene", "settings": {"frame_start": 1, "frame_end": 60}},
            ),
        ],
    ),
    (
        "L7_角色骨骼",
        "Character + rig - hide the other layers, then try Pose Mode on L7_Rig",
        [
            (
                "character_template",
                "create",
                {"template": "anime", "name": "L7_Hero", "height": 1.7, "location": [0, 5.0, 0]},
            ),
            (
                "character_template",
                "hair_create",
                {
                    "character_name": "L7_Hero",
                    "hair_style": "medium",
                    "color": [0.22, 0.13, 0.08, 1.0],
                },
            ),
            (
                "character_template",
                "clothing_add",
                {
                    "character_name": "L7_Hero",
                    "clothing_type": "jacket",
                    "color": [0.16, 0.26, 0.46, 1.0],
                },
            ),
            ("rigging", "armature_create", {"name": "L7_Rig", "location": [0, 5.0, 0]}),
            (
                "rigging",
                "bone_add",
                {
                    "armature_name": "L7_Rig",
                    "bone_name": "Spine",
                    "head": [0, 5.0, 0.85],
                    "tail": [0, 5.0, 1.55],
                },
            ),
        ],
    ),
    (
        "L8_物理",
        "Physics - play the timeline to watch the cloth fall",
        [
            (
                "object",
                "create",
                {
                    "type": "PLANE",
                    "name": "L8_Cloth",
                    "location": [-4.0, 5.0, 2.2],
                    "mesh_params": {"size": 2},
                },
            ),
            ("physics", "cloth_add", {"object_name": "L8_Cloth", "preset": "cotton"}),
            (
                "object",
                "create",
                {"type": "CUBE", "name": "L8_Rigid", "location": [-4.0, 5.0, 0.5]},
            ),
            ("physics", "rigid_body_add", {"object_name": "L8_Rigid"}),
        ],
    ),
]

CLEAN_PY = """
import bpy
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
print("cleaned")
"""

NAMES_PY = """
import bpy, json
print(json.dumps([o.name for o in bpy.data.objects]))
"""

ORGANISE_PY = """
import bpy, json
names = json.loads(%r)
coll = bpy.data.collections.get(%r) or bpy.data.collections.new(%r)
if coll.name not in [c.name for c in bpy.context.scene.collection.children]:
    bpy.context.scene.collection.children.link(coll)
moved = 0
for n in names:
    o = bpy.data.objects.get(n)
    if o is None:
        continue
    for c in list(o.users_collection):
        c.objects.unlink(o)
    coll.objects.link(o)
    moved += 1
print("moved", moved)
"""


async def _py(conn: BlenderConnection, code: str, timeout: float = 60.0) -> str:
    """Run Python in Blender and return its captured stdout."""
    result = await conn.send_command(
        "utility", "execute_python", {"code": code, "timeout": timeout}
    )
    if not result.get("success"):
        raise RuntimeError(result.get("error"))
    return (result.get("data") or {}).get("output", "").strip()


async def _names(conn: BlenderConnection) -> set[str]:
    output = await _py(conn, NAMES_PY)
    return set(json.loads(output.splitlines()[-1]))


async def _run_layer(conn: BlenderConnection, name: str, ops: list[Op]) -> tuple[int, list[str]]:
    before = await _names(conn)
    failures: list[str] = []
    ok = 0
    for category, action, params in ops:
        result = await conn.send_command(category, action, params)
        if result.get("success"):
            ok += 1
        else:
            err = result.get("error", {})
            message = err.get("message", err) if isinstance(err, dict) else err
            failures.append(f"{category}.{action}: {message}")

    created = sorted(await _names(conn) - before)
    if created:
        await _py(conn, ORGANISE_PY % (json.dumps(created), name, name))
    return ok, failures


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="empty the scene before building")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9876)
    args = parser.parse_args()

    conn = BlenderConnection(host=args.host, port=args.port, timeout=180.0)
    try:
        await conn.connect()
    except BlenderConnectionError as exc:
        print(f"Could not reach Blender on {args.host}:{args.port} - {exc}")
        print("Start Blender and enable the Blender MCP addon first.")
        return 1

    info = await conn.send_command("system", "get_info", {})
    version = (info.get("data") or {}).get("version_string", "?")
    print(f"Connected to Blender {version}\n")

    if args.clean:
        await _py(conn, CLEAN_PY)
        print("Scene cleared.\n")

    total_ok = total_ops = 0
    all_failures: list[str] = []
    for name, _hint, ops in LAYERS:
        ok, failures = await _run_layer(conn, name, ops)
        total_ok += ok
        total_ops += len(ops)
        all_failures += failures
        status = "OK" if not failures else f"{len(failures)} FAILED"
        print(f"  {name:14} {ok}/{len(ops)} ops  [{status}]")
        for f in failures:
            print(f"      {f}")

    await conn.disconnect()

    print(f"\n{'=' * 68}")
    print(f"{total_ok}/{total_ops} operations succeeded")
    print("=" * 68)
    print("\nIn Blender, open the Outliner (top right). Each layer is a collection:")
    for name, hint, _ in LAYERS:
        print(f"  {name:14} {hint}")
    print("\n  Tip: press Z in the 3D view to switch Solid / Material Preview / Rendered.")
    print("  Tip: click the eye icon on a collection to hide it and isolate another layer.")
    return 1 if all_failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
