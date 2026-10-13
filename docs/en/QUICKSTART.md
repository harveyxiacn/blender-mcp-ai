# Blender MCP Quick Start

## Overview

This quick start matches the repository state on 2026-03-10:

- 380 tools across 51 server-side tool modules
- 32 startup tools under the default `skill` profile
- 12 skill groups that can be activated on demand

## Prerequisites

- Blender 4.0+
- Python 3.10+
- `uv`
- An MCP-compatible client such as Cursor or Windsurf

## 1. Install From Source

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
uv sync
```

If `uv run` later fails because `.venv` points to a missing interpreter, delete `.venv` and run `uv sync` again.

## 2. Build And Install The Blender Addon

```bash
python build_addon.py
```

In Blender:

1. Open `Edit -> Preferences -> Add-ons`
2. Click `Install...`
3. Select `dist/blender_mcp_addon.zip`
4. Enable `Blender MCP`
5. Open the `MCP` panel from the 3D View sidebar

## 3. Configure Your MCP Client

Example `mcp.json`:

```json
{
  "mcpServers": {
    "blender": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/blender-mcp-ai", "blender-mcp-ai"]
    }
  }
}
```

## 4. Start The Server

```bash
uv run blender-mcp-ai
```

## 5. First Session

Start with a core request that works in the default profile:

```text
List all objects in the current Blender scene.
```

Then try an on-demand workflow:

```text
Activate the materials skill, create a sphere, and assign a red metallic material.
```

## Skill Groups

| Skill | Estimated Tools | Notes |
|-------|-----------------|-------|
| `modeling` | ~38 | Mesh editing, modifiers, curves, UV |
| `materials` | ~17 | Standard + procedural materials |
| `style` | ~8 | Style presets, outlines, baking |
| `character` | ~23 | Templates, rigging, auto-rig |
| `animation` | ~17 | Keyframes, animation presets |
| `scene_setup` | ~18 | Lighting, camera, world, render |
| `automation` | ~12 | Experimental until addon handler parity is finished |
| `physics` | ~18 | Physics and constraints |
| `batch_assets` | ~11 | Batch ops and asset helpers |
| `advanced_3d` | ~32 | Nodes, compositor, sculpt, paint |
| `sport_character` | ~7 | Athlete-oriented workflows |
| `training` | ~11 | Learning and guided practice |

## Known Limits

- `automation` currently exposes server-side tools, but `pipeline` and `quality_audit` are not yet wired into the Blender addon handler registry.
- The API reference is still strongest on stable/core modules; use the project review for the latest inventory snapshot.

## Next Reading

- [INSTALLATION](./INSTALLATION.md)
- [ARCHITECTURE](./ARCHITECTURE.md)
- [API_REFERENCE](./API_REFERENCE.md)
- [ROADMAP](./ROADMAP.md)
- [PROJECT_REVIEW_2026-03](./PROJECT_REVIEW_2026-03.md)
