# Changelog

All notable changes to Blender MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.4.0] - 2026-10-13

### Changed

- **The project is now named `blender-mcp-ai`** — the repository moved to
  `github.com/harveyxiacn/blender-mcp-ai` (old links redirect), and both the
  distribution and the console script are now `blender-mcp-ai`. The former name
  collided with an unrelated project that owns `blender-mcp` on PyPI, so
  `pip install blender-mcp` never installed this software. **If your MCP client
  config still runs `blender-mcp`, change it to `blender-mcp-ai`.** There is no
  PyPI release; install from source.
- **Character proportions rewritten** — `blender_character_template_create` now
  derives head, neck, torso, hips and legs from a single skeleton, so the parts
  actually meet. Before this the head floated 0.22 m above the torso, eyes
  pierced out through the face, and arms were buried inside the chest. Generated
  characters will look different from 0.3.1.
- Copyright is attributed to the actual author rather than a non-existent
  "Blender MCP Contributors" entity, and `bl_info` reports the real version
  instead of `(0, 1, 0)`.

### Added

- **`scripts/demo_tour.py`** — builds a demo scene in eight layers over the MCP
  socket, one collection per layer, then prints how to inspect each one. The
  quickest way for a newcomer to confirm an install works end to end.
- **`docs/en/TOUR.md`** / **`docs/zh/TOUR.md`** — the step-by-step walkthrough
  behind that script, with per-layer viewing instructions.
- **Unity / Quest game-engine FBX export** — `blender_export_fbx` now exposes full
  axis/transform control and a `unity_static_preset` flag for non-rigged
  props/environments. The preset applies the settings required for a clean Unity
  import (`axis_forward=-Z`, `axis_up=Y`, `use_space_transform`,
  `bake_space_transform` so the mesh imports with a zeroed Transform / no residual
  -90deg X rotation, `mesh_smooth_type=FACE`, Mesh/Empty object types). New params:
  `axis_forward`, `axis_up`, `use_space_transform`, `bake_space_transform`,
  `apply_unit_scale`, `mesh_smooth_type`, `object_types`, `path_mode`. Defaults are
  backward-compatible (Blender FBX defaults) unless the preset/params are set.
- **docs/UNITY_QUEST_EXPORT.md** — mobile-VR (Quest) export checklist: poly budgets,
  origin/axis rules, the static preset, and tri-count verification.
- **Zero-Transform export guard** — `blender_export_fbx` now auto-zeros each
  exported object's `.location` under `bake_space_transform` (then restores it)
  so props import into Unity at (0,0,0), and warns on unapplied rotation/scale.
  Controlled by `zero_transform_for_export` (default True). The export result
  reports `zeroed_for_export` and `warnings`. Prevents a baked-translation
  defect class where layout-positioned objects imported metres off-origin.
- **`blender_verify_fbx`** — re-imports an exported FBX and asserts game-engine
  readiness: world origin (0,0,0), triangle budget, one-object-per-file,
  material/emissive report. Returns PASS/FAIL so a modeling agent can
  self-verify each export instead of post-hoc bulk QA.
- **`blender_get_object_info(include_transform_check=True)`** — adds a
  `unity_ready` block (world translation, location/rotation/scale identity
  flags, `will_import_at_origin`, notes) that reveals a baked-translation
  footgun `mesh_stats` can't.
- **automation skill** workflow guide: added a "Game-engine export (Unity / Quest VR)"
  section.

### Fixed

- **Multibyte UTF-8 payloads no longer drop the connection (issue #2)** — the
  addon decoded each `recv()` chunk on arrival, so a multi-byte character split
  across a read raised `UnicodeDecodeError` and the message was dropped without
  ever executing. Frames are now buffered as bytes and decoded only on complete
  lines. Two related defects in the same function: `send()` could partially
  write a large reply and desync the framing (now `sendall()`), and a protocol
  error now returns a `PROTOCOL_ERROR` response instead of a silent disconnect.
- **Long operations no longer tear down a healthy connection** — a render or
  export blocks Blender's main thread, so the addon cannot answer
  `system.get_info` until it returns. The client probed anyway, timed out after
  5 s, and reconnected mid-command. The heartbeat is now skipped while a command
  is outstanding. Verified: a 25 s command completes with 0 reconnects, and
  fails with "Connection closed" when the guard is removed.
- **Handlers no longer leak edit mode — this was silent data loss.** Seven
  handlers entered EDIT mode and never returned, so the session stayed in
  `EDIT_MESH`. The next `object.create` then replaced the object being edited:
  in EDIT mode three consecutive creates leave one object and destroy the
  edited one; in OBJECT mode all three survive. Fixed in `modeling.select`,
  `extrude`, `subdivide`, `bevel` and `mesh_edit_advanced.edit`, `edge_mark`,
  `select_by_trait` via the existing (previously unused) `ensure_object_mode()`.
- **Missing parameters return a clean error instead of raising inside bpy** —
  handlers read names with `params.get("object_name")` and passed the result
  straight to `bpy.data.objects.get(...)`. A missing or misspelled key produced
  `None`, and `bpy.data.objects.get(None)` raised inside bpy: callers saw
  "SystemError: ... returned a result with an exception set" instead of
  `OBJECT_NOT_FOUND`. 240 call sites across 38 modules now supply a default.
- **Malformed error envelopes no longer crash the call** — `training.py`
  returned `"error": "<string>"` from six sites, but every consumer expects the
  `{code, message}` envelope, so an unknown action failed with
  "'str' object has no attribute 'get'". `enrich_error()` now normalises a
  non-dict error rather than falling over.
- **Modifiers are no longer named after the raw enum** — adding a bevel without
  naming it produced a modifier literally called `BEVEL`, which also made
  `modifier_apply` unable to find it by name. Lighting and grease-pencil had the
  same pattern.
- Stale tool counts corrected throughout the docs and the GitHub description
  (380 tools across 56 modules, and the per-profile counts).

### Removed

- **`examples/刀剑神域/`** — third-party copyrighted character art does not
  belong in an MIT-licensed repository. The six tests that used it as a fixture
  now skip when the directory is absent.
- **The Discord community links** — the invite had gone stale
  (`discord.gg/rurjWE45` now returns "Unknown Invite"), so the badge and links
  are removed rather than left pointing at a dead invite. GitHub Discussions is
  the community channel, and the automatic release announcement is disabled.

## [0.3.1] - 2026-06-02

### Fixed

- **Blender 5.x hard-crash and view-layer fixes** (verified: live suite now 121/121 against Blender 5.0.1)
  - `modifier_apply`, `boolean`, decimate: replaced `bpy.ops.object.modifier_apply`
    (hard-crashes from the addon server thread in 5.x) with a depsgraph
    `new_from_object` data-API helper
  - `boolean`: BOOLEAN modifier now added with viewport display off by default
    to avoid crash-on-redraw in heavy scenes; depsgraph apply when `apply=True`
  - `set_origin` and `apply_transform`: rewritten to pure vertex/matrix math
    (no `bpy.ops`), fixing crashes and view-layer errors
  - Added `select_only()` / `ensure_object_mode()` helpers in `handlers/compat.py`
    that link objects to the scene master collection and select via the data
    API; applied across `uv`, `physics`, `rigging`, `modeling` handlers
  - `armature_create` and object `duplicate` now link to the scene master
    collection so new objects are always in the active view layer

## [0.3.0] - 2026-05-31

### Added

- **Smart Tools v2 — Visual Feedback & Workflow Safety**
  - `blender_snapshot_viewport` — capture the 3D viewport as PNG for multimodal AI review loops
  - `blender_snapshot_render_preview` — quick low-sample render preview (maintains aspect ratio)
  - `blender_describe_scene` — structured scene summary (object counts, materials, camera, render settings)
  - `blender_describe_hierarchy` — full parent-child object tree as markdown or JSON
  - `blender_describe_object` — deep object inspection (topology stats, modifier stack, constraints, bbox)
  - `blender_checkpoint_save` — named save-point before risky operations
  - `blender_checkpoint_restore` — restore scene from a named checkpoint
  - `blender_checkpoint_list` — list all checkpoints with timestamps and object counts
  - `blender_checkpoint_delete` — delete a checkpoint to free disk space
  - `blender_quick_product_shot` — one-call product visualization (3-point lighting + camera + backdrop)
  - `blender_quick_turntable` — one-call 360° rotation animation
  - `blender_quick_scene_setup` — one-click scene setup with style presets (studio/outdoor/dramatic/minimal)

- **Error suggestions system**
  - `addon/blender_mcp_addon/handlers/error_suggestions.py` — `enrich_error()` enriches all error responses with actionable fix suggestions
  - All executor error paths now route through `enrich_error()`

- **Project logo and branding**
  - Added official Blender MCP logo (`docs/assets/logo.jpg`)
  - Logo embedded in README header

- **Comprehensive live integration test suite**
  - `tests/run_live_test.py`: 121 tests covering all 50+ handler categories against live Blender
  - `tests/create_style_scenes.py`: 264-command demo creating 3 complete scenes (AAA Gaming, Anime, Pixel Art)
  - `tests/test_new_tools.py`: unit tests for Smart Tools v2 imports, handler actions, and config integration

- **Community infrastructure**
  - GitHub Discussions enabled
  - GitHub Topics added for discoverability
  - FUNDING.yml for GitHub Sponsors
  - CODEOWNERS for PR reviewer assignment

### Changed

- **Version bump**: 0.1.0 → 0.3.0, Development Status Alpha → Beta
- **Blender 5.x compatibility fixes (50+ handler files)**
  - Fixed EEVEE engine name: `BLENDER_EEVEE_NEXT` → `BLENDER_EEVEE` with version-aware compat layer (`handlers/compat.py`)
  - Fixed `bpy.data.objects.get(None)` crash in object, lighting, camera handlers
  - Fixed `Action.fcurves` removal in animation handler (layered action system in 5.x)
  - Fixed `ClothSettings.collision_settings` relocation in physics handler
  - Fixed `bpy_prop_collection.__contains__` type check in nodes handler
  - Added default points for curve creation; added None key handling in preferences handler
  - Black-formatted 151 files for consistency
- **tools/__init__.py**: added missing exports for `snapshot`, `describe`, `checkpoint`, `quick`

### Fixed

- **CI pipeline fully green**
  - Fixed 6696 ruff lint errors, 141 black formatting issues, 414 mypy type errors
  - Excluded live test files from pytest collection (require running Blender)
  - Removed deprecated ruff rules (ANN101, ANN102)

## [0.2.1] - 2026-03-04

### Added

- **Automation pipeline tools**
  - Added `blender_pipeline_generate_character` for end-to-end character generation (template + hair/clothing/accessory + auto-rig + style)
  - Added `blender_pipeline_generate_prop` for prop generation (primitive + style + procedural material + auto UV)
  - Added `blender_pipeline_assemble_scene` for one-click scene assembly (environment, ground, lights, camera, render settings)

- **Quality audit tools**
  - Added `blender_quality_audit_topology` for topology checks (N-gons, non-manifold edges, loose verts)
  - Added `blender_quality_audit_uv` for UV checks (space usage, stretch, overlaps)
  - Added `blender_quality_audit_performance` for platform budget checks (triangles, estimated draw calls)
  - Added `blender_quality_audit_full` for aggregated quality scoring and grade output

- **Automation skill group**
  - Added `automation` skill combining `pipeline`, `quality_audit`, `style_presets`, and `procedural_materials`
  - Enables an end-to-end "auto-generate + auto-audit" workflow

- **Shared node utility**
  - Added `addon/blender_mcp_addon/handlers/node_utils.py`
  - Introduced shared `find_principled_bsdf()` helper for safer material node lookup

- **Expanded tests**
  - Added tests for connection, config, tool profile config, skill manager, server compatibility alias, top-level tool exports, and Principled BSDF regression
  - Test suite expanded from 27 to 34 tests

- **Connection status tool**
  - Added `blender_connection_status` to inspect MCP-Blender health, reconnect count, failed commands, and pending requests

- **Centralized runtime config**
  - Added `src/blender_mcp/config.py`
  - Runtime defaults can now be overridden via environment variables (host, port, timeout, reconnect, log level)

### Changed

- **SkillManager compatibility update**
  - Updated dynamic skill activation/deactivation internals to work with newer FastMCP tool management APIs

- **Tool profile expansion**
  - Added `AUTOMATION_MODULES` in `tools_config.py`
  - Included `pipeline` and `quality_audit` in `focused`, `standard`, and `full` profiles

- **Tool registration/export integration**
  - Wired `pipeline` and `quality_audit` into module registry and top-level tool exports

- **Blender 5.0.1 integration verification**
  - Regression suites passed: `test_comprehensive.py` 133/133, `test_all_tools.py` 23/23
  - New automation flow verified: character/prop/scene pipelines + full quality audit

- **Connection reliability improvements**
  - `BlenderConnection` now supports auto-reconnect and heartbeat checks
  - Command send path retries once after reconnect on transient failures
  - Increased read buffer size and improved UTF-8 decode fault tolerance
  - Added connection stats (total commands, failed commands, reconnect count)

- **Addon main-thread wait optimization**
  - Replaced sleep-based polling with `threading.Event.wait()` to reduce busy waiting

- **Unified CLI defaults**
  - `__main__.py` and `server.py` now read defaults from centralized config

### Fixed

- **Principled BSDF recursive helper bug**
  - Fixed recursive helper misuse in `ai_generation`, `character_template`, `substance`, `vr_ar`, and `zbrush`
  - Replaced with shared helper to prevent runtime recursion failures

- **Server backward compatibility**
  - Added `send_command()` alias in `BlenderMCPServer` for modules still using legacy call sites

- **Pipeline registration and parameter compatibility**
  - Fixed `pipeline/quality_audit` registration errors under FastMCP
  - Improved camera activation compatibility by passing both `camera_name` and `name`

- **Addon server startup parameter bug**
  - Fixed `start_server()` not passing through the `host` parameter

- **Python execution safety**
  - Added empty-code validation, code size limit, and dangerous-pattern checks for `execute_python`

## [0.2.0] - 2026-02-24

### Added

- **Skill System (Dynamic Tool Loading)**
  - `SkillManager` for on-demand tool group activation/deactivation
  - 3 meta-tools: `blender_list_skills`, `blender_activate_skill`, `blender_deactivate_skill`
  - 11 skill groups covering all 200+ tools
  - `tools/list_changed` MCP notification for client-side refresh
  - Workflow guides returned on skill activation
  - New `"skill"` tool profile (recommended, ~31 startup tools)

- **Advanced Mesh Editing** (5 tools)
  - `blender_mesh_edit_advanced` — inset, bridge, spin, knife, fill, symmetrize, etc.
  - `blender_mesh_edge_mark` — crease, sharp, seam, bevel weight
  - `blender_mesh_select_by_trait` — non-manifold, loose, boundary, etc.
  - `blender_vertex_group` — vertex group management
  - `blender_vertex_color` — vertex color painting

- **Style Presets** (3 tools)
  - `blender_style_setup` — one-click style config (Pixel → AAA, 8 presets)
  - `blender_outline_effect` — outline via Solidify/Freestyle/Grease Pencil
  - `blender_bake_maps` — high-to-low poly baking workflow

- **Procedural Materials** (2 tools)
  - `blender_procedural_material` — 67 presets across 8 categories
  - `blender_material_wear` — wear effects (edge wear, scratches, rust, dirt, etc.)

- **Enhanced Object Creation**
  - `mesh_params` support for parametric mesh creation (segments, radius, depth, etc.)
  - Full control for all mesh primitive types

- **Expanded Modifier Support**
  - 45 modifier types (up from 12)
  - Added: Screw, Wireframe, Weld, Remesh, Build, Multires, Cast, Curve, Lattice, and more

### Changed

- Default `TOOL_PROFILE` changed from `"focused"` to `"skill"`
- Startup tool count reduced from ~100 to ~31 (69% reduction)

## [0.1.0] - 2026-01-15

### Added

- Initial release
- MCP Server with FastMCP framework
- Blender Addon with TCP server
- Core tool modules: scene, object, modeling, material, lighting, camera, animation, render, utility, export
- Extended modules: character templates, rigging, auto-rig, physics, constraints, nodes, compositor, sculpting, texture painting, batch, assets, animation presets, world, versioning, AI generation, VR/AR, Substance, ZBrush, cloud render, collaboration, training
- Multi-IDE support: Cursor, Windsurf, Claude Desktop
- Hot reload for addon development
- Tool profiles: minimal, focused, standard, full
