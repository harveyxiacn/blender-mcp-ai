# Blender MCP Guided Tour

## Overview

This is the fastest way to see the project actually working, and to understand
what each part of it does.

`scripts/demo_tour.py` drives the MCP socket to build a small scene in **eight
layers**, then groups each layer into its own collection so you can switch them
on and off and inspect one thing at a time.

Every operation goes through the same socket a real client uses, so if the tour
passes, your install works end to end.

## Prerequisites

- Blender 4.0+ running, with the Blender MCP addon **enabled** (it listens on
  `127.0.0.1:9876`)
- The project installed: `uv sync`
- An empty scene is easiest to reason about — the tour's `--clean` flag handles that

## Run it

```bash
uv run python scripts/demo_tour.py --clean
```

Expected output:

```
Connected to Blender 5.2.2 LTS

Scene cleared.

  L1_场景基础        5/5 ops  [OK]
  L2_建模          9/9 ops  [OK]
  ...
  46/46 operations succeeded
```

If some operations fail, the script prints the error code for each one and exits
non-zero.

> The collection names are Chinese, because that is the language this project's
> demo scene was built in. They are ordinary collection names; rename them freely.

## Blender UI cheat sheet

You will need these four things:

| I want to | Do this |
|---|---|
| Change how the viewport is shaded | Hover the 3D view, press **Z**, pick a mode |
| Select / hide a layer | **Outliner** (top right) → click the eye icon on a collection |
| Read an object's numbers | Select it, press **N** for the sidebar |
| Open a specific properties panel | Right-hand column of tab icons (wrench = modifiers, etc.) |
| Frame the selected object | Select it, press **Numpad .** |
| Show the camera's view | Select the camera, press **Numpad 0** |

The three shading modes you will use most:

- **Solid** — flat grey, fastest, best for shape and topology
- **Material Preview** (press **Z** → Material Preview) — shows materials without
  needing any lights
- **Rendered** — the real render, including lights

## Layer by layer

### `L1_场景基础` — objects and transforms

*What it demonstrates:* creating primitives and moving them (`object.create`,
`object.transform`).

*How to look:* select `L1_Cube` and press **N**. The sidebar shows its Location,
Rotation and Scale.

*What to check:* the cube's scale is **0.6**, because the tour applied
`object.transform` to it after creating it at 1.0.

### `L2_建模` — modifiers

*What it demonstrates:* `Bevel`, `Subdivision` and `Boolean` modifiers, plus the
destructive `subdivide` operation.

*How to look:* select `L2_Bevel`, then open the **wrench** tab in the properties
column. You will see a live `Bevel` modifier.

*What to check:*

- Toggle `L2_Subdiv`'s **Subdivision** modifier off and on — the cube snaps
  between blocky and smooth
- `L2_BoolA` carries a **Boolean** modifier that cut a cylinder-shaped hole
  through it. Hide `L2_BoolB` (the cutter) to see the result clearly
- `L2_Subd` has no modifier: `subdivide` edits the mesh directly

### `L3_材质` — materials

*What it demonstrates:* the material system and Principled BSDF values.

*How to look:* press **Z** → **Material Preview**. This mode lights the scene
with a studio HDRI, so you can judge materials without setting up lights.

*What to check:*

- `L3_Gold` is metallic (metallic 1.0, roughness 0.15) — it mirrors its surroundings
- `L3_Red` is a matte plastic (metallic 0.0, roughness 0.3)
- Select either object and open the **material** tab to read those numbers

### `L4_灯光相机` — three-point lighting and camera

*What it demonstrates:* `lighting.create`, `camera.create`, `camera.look_at`,
and the world background.

*How to look:*

1. Press **Z** → **Rendered**. This is the real thing.
2. Select `L4_Key` and open the **light** tab — its power is 700 W
3. Select `L4_Cam` and press **Numpad 0** to look through it

*What to check:* the three lights are a classic key / fill / rim setup. Try
setting `L4_Key` to 6000 W — the render blows out completely. That is not a bug,
it is what area-light wattage does.

### `L5_UV` — UV unwrapping

*What it demonstrates:* `uv.smart_project`.

*How to look:*

1. Split an area into a **UV Editor** (click the editor-type button in the
   top-left of any area)
2. Select `L5_UVBox`, press **Tab** to enter edit mode, then **A** to select all

*What to check:* the cube's six faces appear as tidy, non-overlapping islands,
because smart project cut it into six.

### `L6_动画` — keyframes

*What it demonstrates:* `animation.keyframe_insert` and the scene frame range.

*How to look:*

1. Move the playhead to frame 1 in the timeline, then press **Space**
2. `L6_Bounce` rises, spins, and lands over 40 frames
3. Open a **Graph Editor** or **Dope Sheet** to see the keyframe diamonds

*What to check:* keys exist on both `location` and `rotation_euler` — that is
why the cube both bounces and spins.

### `L7_角色骨骼` — character and rig

*What it demonstrates:* the character template system and armature creation.

*How to look:*

1. Hide the other layers in the Outliner so the character is not buried
2. Select `L7_Rig`, then switch the mode dropdown (top-left) to **Pose Mode**

*What to check:* the character is built from named parts — `L7_Hero_Head`,
`L7_Hero_Body`, `L7_Hero_Hair`, `L7_Hero_Clothing_jacket` — all generated from
one `height` value, so they meet cleanly rather than floating apart.

### `L8_物理` — physics

*What it demonstrates:* cloth and rigid-body simulation.

*How to look:*

1. Return the playhead to frame 1
2. Press **Space** — the cloth plane falls and drapes

*What to check:* select `L8_Cloth` and open the **physics** tab to see the Cloth
panel; `L8_Rigid` has a Rigid Body panel instead.

## Beyond the tour: rendering and export

The tour builds geometry, materials and lighting, but it does not render.

- **Render:** select `L4_Cam` and press **F12**
- **Export:** any object can be exported with `blender_export_fbx` /
  `blender_export_gltf` / `blender_export_obj`. See
  [UNITY_QUEST_EXPORT.md](../UNITY_QUEST_EXPORT.md) for the game-engine checklist

## Troubleshooting

**"Could not reach Blender"** — Blender is not running, or the addon is not
enabled. Open Blender → `Edit` → `Preferences` → `Add-ons` → enable
**Blender MCP**, then check the MCP panel in the 3D view sidebar.

**Objects are missing, or a layer looks wrong** — you almost certainly ran the
tour twice without `--clean`. The second run creates `L1_Cube.001` while some
operations still target the old `L1_Cube`, so you end up editing last run's
objects. Always pass `--clean`.

**Everything looks flat grey** — you are in Solid shading. Press **Z** and pick
Material Preview or Rendered.

**A render is completely white** — the lights are too strong. Area-light energy
is in watts; 700 W is reasonable, 6000 W is not.

## Automated tests

The tour is a smoke test, but the repository has a much broader live suite:

```bash
python tests/run_live_test.py
```

It drives 121 assertions across 47 modules through the same socket and prints a
pass/fail summary. Like the tour, run it against a clean scene — stale objects
from a previous run cause misleading failures.
