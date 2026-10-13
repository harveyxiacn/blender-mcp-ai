#!/usr/bin/env python
"""
Demo script for Smart Tools v2.

Connects to a running Blender instance (with MCP addon enabled on port 9876)
and exercises all new features, leaving demo models and scenes in Blender.

Usage:
    python tests/run_demo.py

Requirements:
    - Blender running with MCP addon enabled (port 9876)
    - `uv run` or activated venv with blender-mcp-ai installed
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from blender_mcp.connection import BlenderConnection

PASS = 0
FAIL = 0


async def send(
    conn: BlenderConnection, category: str, action: str, params: dict | None = None
) -> dict:
    """Send a command to Blender."""
    return await conn.send_command(category, action, params or {})


async def test(
    conn: BlenderConnection,
    name: str,
    category: str,
    action: str,
    params: dict | None = None,
    check_success: bool = True,
) -> dict:
    """Send a command and report pass/fail."""
    global PASS, FAIL
    try:
        result = await send(conn, category, action, params)
        if check_success and not result.get("success"):
            FAIL += 1
            err = result.get("error", {})
            msg = err.get("message", str(err))
            suggestion = err.get("suggestion", "")
            print(f"  FAIL {name}: {msg}")
            if suggestion:
                print(f"       Suggestion: {suggestion}")
            return result
        PASS += 1
        print(f"  PASS {name}")
        return result
    except Exception as e:
        FAIL += 1
        print(f"  ERROR {name}: {e}")
        return {"success": False, "error": {"message": str(e)}}


async def demo_scene_describe(conn: BlenderConnection) -> None:
    """Demo 1: Scene Describe & Hierarchy."""
    print("\n" + "=" * 60)
    print("DEMO 1: Scene Describe & Hierarchy")
    print("=" * 60)

    # First, create some objects for a populated scene
    print("\n--- Setting up demo objects ---")
    await test(
        conn,
        "create.cube",
        "object",
        "create",
        {"type": "CUBE", "name": "Demo_Table", "location": [0, 0, 0.5], "scale": [2, 1, 0.05]},
    )
    await test(
        conn,
        "create.sphere",
        "object",
        "create",
        {
            "type": "UV_SPHERE",
            "name": "Demo_Apple",
            "location": [0.5, 0, 1.0],
            "scale": [0.15, 0.15, 0.15],
        },
    )
    await test(
        conn,
        "create.cylinder",
        "object",
        "create",
        {
            "type": "CYLINDER",
            "name": "Demo_Vase",
            "location": [-0.5, 0, 1.2],
            "scale": [0.2, 0.2, 0.5],
        },
    )
    await test(
        conn,
        "create.light",
        "object",
        "create",
        {"type": "LIGHT", "name": "Demo_Light", "location": [2, -2, 3]},
    )
    await test(
        conn,
        "create.camera",
        "object",
        "create",
        {"type": "CAMERA", "name": "Demo_Camera", "location": [4, -4, 3]},
    )

    # Parent apple and vase to table
    await test(
        conn,
        "parent.apple",
        "object",
        "set_parent",
        {"child_name": "Demo_Apple", "parent_name": "Demo_Table"},
    )
    await test(
        conn,
        "parent.vase",
        "object",
        "set_parent",
        {"child_name": "Demo_Vase", "parent_name": "Demo_Table"},
    )

    # Now test describe tools
    print("\n--- Testing Describe Tools ---")
    result = await test(conn, "describe.scene_md", "describe", "scene", {"format": "markdown"})
    if result.get("success"):
        print("\n  --- Scene Summary ---")
        summary = result.get("data", {}).get("summary", "")
        for line in summary.split("\n")[:20]:
            print(f"  | {line}")

    result = await test(
        conn, "describe.hierarchy_md", "describe", "hierarchy", {"format": "markdown"}
    )
    if result.get("success"):
        print("\n  --- Hierarchy ---")
        tree = result.get("data", {}).get("tree", "")
        for line in tree.split("\n")[:15]:
            print(f"  | {line}")

    result = await test(
        conn, "describe.object", "describe", "object", {"name": "Demo_Table", "format": "markdown"}
    )
    if result.get("success"):
        print("\n  --- Object Deep Inspect ---")
        summary = result.get("data", {}).get("summary", "")
        for line in summary.split("\n")[:15]:
            print(f"  | {line}")

    # Test error suggestion on non-existent object
    print("\n--- Testing Error Suggestions ---")
    result = await test(
        conn,
        "describe.object_missing",
        "describe",
        "object",
        {"name": "NonExistent"},
        check_success=False,
    )
    if not result.get("success"):
        err = result.get("error", {})
        print(f"  | Error: {err.get('message', '')}")
        print(f"  | Suggestion: {err.get('suggestion', '')}")


async def demo_checkpoint(conn: BlenderConnection) -> None:
    """Demo 2: Checkpoint Save/Restore."""
    print("\n" + "=" * 60)
    print("DEMO 2: Checkpoint Save / Restore")
    print("=" * 60)

    # Save checkpoint of current state
    print("\n--- Saving checkpoint ---")
    await test(
        conn,
        "checkpoint.save",
        "checkpoint",
        "save",
        {
            "name": "demo_before_changes",
            "description": "Scene with table, apple, vase before modifications",
        },
    )

    # List checkpoints
    result = await test(conn, "checkpoint.list", "checkpoint", "list")
    if result.get("success"):
        cps = result.get("data", {}).get("checkpoints", [])
        print(f"  | Checkpoints available: {len(cps)}")
        for cp in cps:
            print(f"  |   - {cp['name']} ({cp.get('timestamp', '?')})")

    # Make destructive changes
    print("\n--- Making destructive changes ---")
    await test(conn, "delete.apple", "object", "delete", {"name": "Demo_Apple"})
    await test(conn, "delete.vase", "object", "delete", {"name": "Demo_Vase"})

    # Verify objects are gone
    result = await test(conn, "describe.after_delete", "describe", "scene", {"format": "json"})
    if result.get("success"):
        obj_count = result.get("data", {}).get("object_count", "?")
        print(f"  | Objects after deletion: {obj_count}")

    # Restore checkpoint
    print("\n--- Restoring checkpoint ---")
    await test(conn, "checkpoint.restore", "checkpoint", "restore", {"name": "demo_before_changes"})

    # Verify objects are back
    result = await test(conn, "describe.after_restore", "describe", "scene", {"format": "json"})
    if result.get("success"):
        obj_count = result.get("data", {}).get("object_count", "?")
        print(f"  | Objects after restore: {obj_count}")

    # Clean up checkpoint
    await test(conn, "checkpoint.delete", "checkpoint", "delete", {"name": "demo_before_changes"})


async def demo_product_shot(conn: BlenderConnection) -> None:
    """Demo 3: Quick Product Shot."""
    print("\n" + "=" * 60)
    print("DEMO 3: Quick Product Shot")
    print("=" * 60)

    # Create a hero object (monkey head)
    print("\n--- Creating hero object ---")
    await test(
        conn,
        "create.monkey",
        "object",
        "create",
        {"type": "MONKEY", "name": "Demo_Sculpture", "location": [0, 0, 0]},
    )

    # Apply subdivision for smoothness
    await test(
        conn,
        "add.subsurf",
        "modeling",
        "modifier_add",
        {"object_name": "Demo_Sculpture", "modifier_type": "SUBSURF", "settings": {"levels": 2}},
    )

    # Set up product shot
    print("\n--- Setting up product shot ---")
    result = await test(
        conn,
        "quick.product_shot",
        "quick",
        "product_shot",
        {
            "target_object": "Demo_Sculpture",
            "style": "studio",
            "render_width": 1920,
            "render_height": 1080,
        },
    )
    if result.get("success"):
        data = result.get("data", {})
        print(f"  | Target: {data.get('target', '?')}")
        print(f"  | Style: {data.get('style', '?')}")
        print(f"  | Created: {', '.join(data.get('created_objects', []))}")


async def demo_turntable(conn: BlenderConnection) -> None:
    """Demo 4: Quick Turntable Animation."""
    print("\n" + "=" * 60)
    print("DEMO 4: Quick Turntable Animation")
    print("=" * 60)

    # Create a torus
    print("\n--- Creating demo object ---")
    await test(
        conn,
        "create.torus",
        "object",
        "create",
        {"type": "TORUS", "name": "Demo_Ring", "location": [0, 0, 0]},
    )

    # Set up turntable
    print("\n--- Creating turntable animation ---")
    result = await test(
        conn,
        "quick.turntable",
        "quick",
        "turntable",
        {"target_object": "Demo_Ring", "frames": 120, "axis": "Z"},
    )
    if result.get("success"):
        data = result.get("data", {})
        print(f"  | Target: {data.get('target', '?')}")
        print(f"  | Pivot: {data.get('pivot_empty', '?')}")
        print(f"  | Frames: {data.get('frames', '?')}")


async def demo_scene_setup(conn: BlenderConnection) -> None:
    """Demo 5: Quick Scene Setup (multiple styles)."""
    print("\n" + "=" * 60)
    print("DEMO 5: Quick Scene Setup Styles")
    print("=" * 60)

    for style in ["studio", "dramatic", "outdoor", "minimal"]:
        print(f"\n--- Setting up '{style}' scene ---")
        result = await test(
            conn,
            f"quick.scene_setup.{style}",
            "quick",
            "scene_setup",
            {"style": style, "clear_scene": True},
        )
        if result.get("success"):
            data = result.get("data", {})
            created = data.get("created_objects", [])
            print(f"  | Created: {', '.join(created)}")

        # Add a demo cube to see the lighting
        await test(
            conn,
            f"create.cube.{style}",
            "object",
            "create",
            {"type": "CUBE", "name": f"Demo_{style.title()}_Cube", "location": [0, 0, 0.5]},
        )

    # End with studio style for the final scene
    print("\n--- Final scene: Studio with multiple objects ---")
    await test(
        conn,
        "quick.scene_setup.final",
        "quick",
        "scene_setup",
        {"style": "studio", "clear_scene": True},
    )


async def demo_snapshot(conn: BlenderConnection) -> None:
    """Demo 6: Viewport Snapshot."""
    print("\n" + "=" * 60)
    print("DEMO 6: Viewport Snapshot")
    print("=" * 60)

    # First create something to look at
    await test(
        conn,
        "create.monkey_final",
        "object",
        "create",
        {"type": "MONKEY", "name": "Demo_Final_Head", "location": [0, 0, 0]},
    )
    await test(
        conn,
        "quick.product_shot_final",
        "quick",
        "product_shot",
        {"target_object": "Demo_Final_Head", "style": "dramatic"},
    )

    # Capture viewport
    print("\n--- Capturing viewport snapshot ---")
    result = await test(
        conn, "snapshot.viewport", "snapshot", "viewport", {"width": 1280, "height": 720}
    )
    if result.get("success"):
        path = result.get("data", {}).get("path", "?")
        print(f"  | Snapshot saved: {path}")

    # Capture render preview
    print("\n--- Capturing render preview ---")
    result = await test(
        conn, "snapshot.render_preview", "snapshot", "render_preview", {"width": 640, "samples": 32}
    )
    if result.get("success"):
        path = result.get("data", {}).get("path", "?")
        print(f"  | Render preview saved: {path}")


async def demo_final_showcase(conn: BlenderConnection) -> None:
    """Create a final showcase scene with all elements."""
    print("\n" + "=" * 60)
    print("FINAL SHOWCASE: Complete Scene with All Features")
    print("=" * 60)

    # Clear and set up studio
    await test(
        conn, "setup.studio", "quick", "scene_setup", {"style": "studio", "clear_scene": True}
    )

    # Create a composition of objects
    print("\n--- Creating showcase objects ---")
    await test(
        conn,
        "create.base",
        "object",
        "create",
        {
            "type": "CYLINDER",
            "name": "Showcase_Pedestal",
            "location": [0, 0, 0.3],
            "scale": [1.5, 1.5, 0.3],
        },
    )
    await test(
        conn,
        "create.main",
        "object",
        "create",
        {"type": "MONKEY", "name": "Showcase_Head", "location": [0, 0, 1.2]},
    )
    await test(
        conn,
        "create.accent1",
        "object",
        "create",
        {
            "type": "TORUS",
            "name": "Showcase_Ring",
            "location": [0, 0, 1.2],
            "scale": [0.8, 0.8, 0.8],
        },
    )
    await test(
        conn,
        "create.accent2",
        "object",
        "create",
        {
            "type": "UV_SPHERE",
            "name": "Showcase_Orb",
            "location": [1.5, 0, 1.0],
            "scale": [0.3, 0.3, 0.3],
        },
    )

    # Add subdivision to head
    await test(
        conn,
        "mod.subsurf",
        "modeling",
        "modifier_add",
        {"object_name": "Showcase_Head", "modifier_type": "SUBSURF", "settings": {"levels": 2}},
    )

    # Parent all to pedestal
    for child in ["Showcase_Head", "Showcase_Ring", "Showcase_Orb"]:
        await test(
            conn,
            f"parent.{child}",
            "object",
            "set_parent",
            {"child_name": child, "parent_name": "Showcase_Pedestal"},
        )

    # Save checkpoint of the showcase
    print("\n--- Saving showcase checkpoint ---")
    await test(
        conn,
        "checkpoint.save_showcase",
        "checkpoint",
        "save",
        {
            "name": "showcase_complete",
            "description": "Final showcase with pedestal, monkey head, ring, and orb",
        },
    )

    # Set up product shot
    print("\n--- Setting up product shot ---")
    await test(
        conn,
        "quick.product_shot_showcase",
        "quick",
        "product_shot",
        {"target_object": "Showcase_Head", "style": "dramatic"},
    )

    # Create turntable
    print("\n--- Creating turntable ---")
    await test(
        conn,
        "quick.turntable_showcase",
        "quick",
        "turntable",
        {"target_object": "Showcase_Pedestal", "frames": 180, "axis": "Z"},
    )

    # Describe the final scene
    print("\n--- Final scene description ---")
    result = await test(conn, "describe.final", "describe", "scene", {"format": "markdown"})
    if result.get("success"):
        summary = result.get("data", {}).get("summary", "")
        for line in summary.split("\n"):
            print(f"  | {line}")

    # Show hierarchy
    result = await test(
        conn, "describe.hierarchy_final", "describe", "hierarchy", {"format": "markdown"}
    )
    if result.get("success"):
        tree = result.get("data", {}).get("tree", "")
        for line in tree.split("\n"):
            print(f"  | {line}")

    # Capture snapshots
    print("\n--- Capturing final snapshots ---")
    result = await test(
        conn, "snapshot.final_viewport", "snapshot", "viewport", {"width": 1920, "height": 1080}
    )
    if result.get("success"):
        print(f"  | Viewport: {result.get('data', {}).get('path', '?')}")

    result = await test(
        conn, "snapshot.final_render", "snapshot", "render_preview", {"width": 960, "samples": 64}
    )
    if result.get("success"):
        print(f"  | Render: {result.get('data', {}).get('path', '?')}")


async def main() -> None:
    """Run all demos."""
    global PASS, FAIL

    print("=" * 60)
    print("Blender MCP - Smart Tools v2 Demo")
    print("=" * 60)
    print("Connecting to Blender on localhost:9876...")

    conn = BlenderConnection(host="127.0.0.1", port=9876)
    await conn.connect()
    print("Connected!\n")

    start = time.time()

    try:
        # Demo 1: Scene understanding
        await demo_scene_describe(conn)

        # Demo 2: Checkpoint safety
        await demo_checkpoint(conn)

        # Demo 3: Product shot (clears scene, creates fresh)
        await demo_product_shot(conn)

        # Demo 4: Turntable animation
        await demo_turntable(conn)

        # Demo 5: Scene styles
        await demo_scene_setup(conn)

        # Demo 6: Viewport snapshot
        await demo_snapshot(conn)

        # Final: Showcase scene (left in Blender for inspection)
        await demo_final_showcase(conn)

    finally:
        elapsed = time.time() - start
        await conn.disconnect()

    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"Demo complete: {PASS}/{total} passed, {FAIL} failed ({elapsed:.1f}s)")
    print("=" * 60)
    print("\nThe final showcase scene has been left in Blender for inspection.")
    print("Objects: Showcase_Pedestal, Showcase_Head, Showcase_Ring, Showcase_Orb")
    print("Features: Product shot lighting, turntable animation (180 frames)")
    print("Checkpoint 'showcase_complete' saved for rollback demonstration.")

    if FAIL > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
