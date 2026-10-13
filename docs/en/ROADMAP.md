# Blender MCP Roadmap

## Status Date

This roadmap reflects the repository state on 2026-03-10.

## What Is Already In Place

- 51 server-side tool modules
- 380 total tools in source
- skill-based loading with 12 skill groups
- addon hot reload support
- training, sport-character, style preset, and procedural material modules

## Priority 1: Stability And Execution Parity

- finish Blender addon handlers for `pipeline` and `quality_audit`
- add automated parity tests between MCP categories and addon handler categories
- separate stable vs experimental modules in profile defaults
- generate tool/profile inventory docs from source instead of hand-maintained counts

## Priority 2: Production Workflow Hardening

- add queued long-running jobs for bake, render, and export operations
- add progress reporting and cancellation for expensive tasks
- formalize reusable asset build recipes for characters, props, and scenes
- add preset bundles for web, mobile, desktop, and hero-quality outputs

## Priority 3: Audit To Auto-Fix Loop

- turn quality audits into guided repair workflows
- add optional auto-fixes for UV overlap, naming, export settings, and topology hygiene
- add release checks before GLB/FBX export

## Priority 4: Asset And Collaboration Layer

- scene/package diff summaries for review
- richer asset metadata and search flows
- handoff bundles for review, export, and downstream engine ingest
- cloud render / collaboration modules backed by real job orchestration
