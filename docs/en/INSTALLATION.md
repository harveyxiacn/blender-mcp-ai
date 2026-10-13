# Blender MCP Installation Guide

## Requirements

| Item | Minimum |
|------|---------|
| Python | 3.10 |
| Blender | 4.0 |
| MCP client | Cursor, Windsurf, Claude Desktop, or compatible |

## 1. Clone And Sync

```bash
git clone https://github.com/harveyxiacn/blender-mcp-ai.git
cd blender-mcp-ai
uv sync
```

Optional development dependencies:

```bash
uv sync --extra dev
```

## 2. Recover From A Stale `.venv`

This repository may be moved between machines. If `.venv/pyvenv.cfg` still points to an interpreter path from another computer, commands such as `uv run` can fail immediately.

Recovery:

```bash
rm -rf .venv   # PowerShell: Remove-Item -Recurse -Force .venv
uv sync
```

## 3. Build Or Install The Blender Addon

Build the zip package:

```bash
python build_addon.py
```

Optional auto-install command after the environment is ready:

```bash
uv run blender-mcp-ai install-addon
```

Manual Blender steps:

1. `Edit -> Preferences -> Add-ons`
2. Click `Install...`
3. Select `dist/blender_mcp_addon.zip`
4. Enable `Blender MCP`
5. Open the `MCP` panel in the 3D View sidebar

## 4. Configure Your Client

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

## 5. Tool Profiles

Current profile sizes are based on the 2026-03-10 code audit:

| Profile | Modules | Startup/User-Facing Tools | Notes |
|---------|---------|---------------------------|-------|
| `minimal` | 4 | 29 | Core scene/object/utility/export only |
| `skill` | 5 | 32 | Default; adds 3 skill meta-tools |
| `focused` | 14 | 108 | Static curated set |
| `standard` | 23 | 165 | Broader daily-use coverage |
| `extended` | 27 | 194 | Adds physics and batch modules |
| `full` | 50 | 356 | All user-facing modules |

The repository contains 380 total tools if you include the 3 skill meta-tools.

## 6. Verify

Basic checks:

```bash
uv run blender-mcp-ai --version
uv run blender-mcp-ai
```

Connection check with Blender open and the addon enabled:

```bash
uv run blender-mcp-ai check
```

## 7. Troubleshooting

| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| `uv run` fails before startup | stale `.venv` | recreate `.venv` with `uv sync` |
| `Connection refused` | addon not running | enable addon and confirm MCP panel status |
| Tools show up but fail with unknown category | server/addon parity gap | avoid experimental automation tools for now |
| Port already in use | duplicate instance | close the extra Blender or server process |
