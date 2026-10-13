"""Guard against handlers feeding a ``None`` param into a collection lookup.

``params.get("object_name")`` with no default returns ``None`` when the caller
omits or misspells the key, and ``bpy.data.objects.get(None)`` raises deep
inside bpy. The client then sees an opaque ``SystemError`` rather than a clean
``OBJECT_NOT_FOUND``.

Every handler that passes such a value to a collection ``.get()`` must supply a
default. This scans the source, so it runs in CI without Blender.
"""

import ast
from pathlib import Path

import pytest

HANDLERS = Path(__file__).resolve().parents[1] / "addon" / "blender_mcp_addon" / "handlers"


def _params_get_without_default(fn: ast.FunctionDef) -> dict[str, ast.Call]:
    """Map variable name -> the ``params.get("key")`` call that produced it."""
    assigned: dict[str, ast.Call] = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        value = node.value
        if not isinstance(value, ast.Call):
            continue
        func = value.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "get"
            and isinstance(func.value, ast.Name)
            and func.value.id == "params"
            and len(value.args) == 1
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned[target.id] = value
    return assigned


def _fed_into_a_collection_lookup(fn: ast.FunctionDef, names: set[str]) -> set[str]:
    """Names passed as the first argument of some ``<x>.get(name)`` call."""
    used = set()
    for node in ast.walk(fn):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id in names
        ):
            used.add(node.args[0].id)
    return used


def _offenders() -> list[tuple[str, str, str]]:
    found = []
    for path in sorted(HANDLERS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            assigned = _params_get_without_default(fn)
            if not assigned:
                continue
            for name in _fed_into_a_collection_lookup(fn, set(assigned)):
                key = assigned[name].args[0]
                label = key.value if isinstance(key, ast.Constant) else "?"
                found.append((path.name, fn.name, label))
    return found


def test_handlers_default_params_before_collection_lookups() -> None:
    offenders = _offenders()
    detail = "\n".join(f"  {f}:{fn} -> params.get({k!r}) needs a default" for f, fn, k in offenders)
    assert not offenders, (
        f"{len(offenders)} handler(s) pass a possibly-None param into a collection "
        f"lookup, which raises inside bpy instead of returning a clean error:\n{detail}"
    )


def test_the_scanner_actually_finds_something() -> None:
    """A broken scanner must not look like a clean bill of health."""
    total = 0
    for path in sorted(HANDLERS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
            total += len(_params_get_without_default(fn))
    assert total > 0, "scanner found no params.get() calls at all - it is broken"


@pytest.mark.parametrize("module", ["modeling.py", "uv.py", "object.py", "rigging.py"])
def test_key_modules_present(module: str) -> None:
    assert (HANDLERS / module).exists(), f"{module} missing - handler layout changed"
