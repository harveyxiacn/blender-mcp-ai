# Blender MCP Architecture

## System Summary

As of 2026-03-10, the repository contains:

- 56 server-side tool modules in `src/blender_mcp/tools`
- 380 total `@mcp.tool(...)` registrations in source
- 12 skill groups in `skill_manager.py`
- 6 loading profiles in `tools_config.py`

## Runtime Topology

```text
AI client
  -> MCP stdio / streamable-http
Blender MCP server
  -> TCP JSON messages
Blender addon
  -> Blender Python API
```

## Main Components

### MCP Server

Key files:

- `src/blender_mcp/server.py`
- `src/blender_mcp/connection.py`
- `src/blender_mcp/skill_manager.py`
- `src/blender_mcp/tools_config.py`

Responsibilities:

- register tools for the selected profile
- open and maintain the TCP connection to Blender
- expose `list/activate/deactivate` skill meta-tools
- translate MCP tool calls into addon command payloads

### Blender Addon

Key files:

- `addon/blender_mcp_addon/__init__.py`
- `addon/blender_mcp_addon/server.py`
- `addon/blender_mcp_addon/executor.py`
- `addon/blender_mcp_addon/handlers/__init__.py`

Responsibilities:

- run a socket server inside Blender
- move command execution back onto Blender's main thread
- dispatch by category to handler modules
- expose panel/preferences UI and hot reload helpers

## Profile Inventory

The current profile counts come from a static scan of tool decorators:

| Profile | Modules | Tools | Notes |
|---------|---------|-------|-------|
| `minimal` | 4 | 29 | Core operational surface |
| `skill` | 5 | 32 | Core tools plus 3 skill meta-tools |
| `focused` | 14 | 108 | Static curated workflow set |
| `standard` | 23 | 165 | Broad day-to-day coverage |
| `extended` | 27 | 194 | Adds physics and batch workflows |
| `full` | 50 | 356 | All user-facing modules |

The codebase has 380 total tools if you count the 3 skill meta-tools separately.

## Skill Inventory

| Skill | Estimated Tools | Module Set |
|-------|-----------------|------------|
| `modeling` | ~38 | modeling, curves, uv_mapping |
| `materials` | ~17 | material, procedural_materials |
| `style` | ~8 | style_presets, mesh_edit_advanced |
| `character` | ~23 | character_templates, rigging, auto_rig |
| `animation` | ~17 | animation, animation_presets |
| `scene_setup` | ~18 | lighting, camera, world, render |
| `automation` | ~12 | pipeline, quality_audit, style_presets, procedural_materials |
| `physics` | ~18 | physics, constraints |
| `batch_assets` | ~11 | batch, assets |
| `advanced_3d` | ~32 | nodes, compositor, sculpting, texture_painting |
| `sport_character` | ~7 | sport_character |
| `training` | ~11 | training |

## Command Flow

1. The client invokes an MCP tool on the server.
2. The server converts the tool input into `{category, action, params}`.
3. `BlenderConnection` sends the request over TCP.
4. The addon socket server receives the payload.
5. `CommandExecutor` routes the request to a handler module.
6. The handler executes Blender API calls and returns JSON.

## Current Execution Gap

The most important architecture gap found in the 2026-03 review:

- `pipeline` and `quality_audit` are registered in `src/blender_mcp/tools_config.py`
- those modules are also advertised through the `automation` skill
- but `addon/blender_mcp_addon/handlers/__init__.py` does not map `pipeline` or `quality_audit`

Effect:

- the tools can appear in MCP tool lists
- execution can still fail inside the addon with an unknown category error

Until addon parity is completed, treat automation tools as experimental.

## Extension Rule

When adding a new tool family, update both layers:

1. server tool module and `MODULE_REGISTRY`
2. addon handler module and handler registry
3. profile / skill definitions
4. tests that verify server-to-addon category parity
