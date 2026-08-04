"""Architectural guard: the core never learns brand or channel identity (spec §3).

This is the constraint that makes "add brand #2 / channel #2" a config-and-adapter job instead of a
rewrite, and it erodes one convenient hardcode at a time. A test catches that; a convention does not.

Docstrings are exempt on purpose. Explaining *why* a module exists by naming the brand it was designed
around is useful documentation; branching on `if brand == "thaiswim"` is the failure this guards
against. So the check inspects identifiers and runtime string literals, and skips prose.
"""

import ast
from pathlib import Path

import pytest

CORE = Path(__file__).resolve().parents[2] / "src" / "brandcortex" / "core"
FORBIDDEN = ("thaiswim", "facebook", "instagram", "graph.facebook.com")


def _docstring_node_ids(tree: ast.AST) -> set[int]:
    """Ids of Constant nodes that are docstrings, so prose can be excluded from the scan."""
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
            body = getattr(node, "body", [])
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def _executable_text(path: Path) -> list[tuple[int, str]]:
    """Every identifier and non-docstring string literal in a module, with line numbers."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = _docstring_node_ids(tree)
    found: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            found.append((node.lineno, node.value))
        elif isinstance(node, ast.Name):
            found.append((node.lineno, node.id))
        elif isinstance(node, ast.Attribute):
            found.append((node.lineno, node.attr))
        elif isinstance(node, ast.alias):
            found.append((getattr(node, "lineno", 0), f"{node.name} {node.asname or ''}"))
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append((node.lineno, node.module))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            found.append((node.lineno, node.name))
    return found


@pytest.mark.parametrize("term", FORBIDDEN)
def test_core_contains_no_brand_or_channel_identifiers(term: str) -> None:
    offenders = [
        f"{path.relative_to(CORE)}:{lineno}"
        for path in sorted(CORE.rglob("*.py"))
        for lineno, text in _executable_text(path)
        if term in text.lower()
    ]
    assert not offenders, f"{term!r} leaked into core/ code: {offenders}"


def test_core_does_not_import_concrete_adapters() -> None:
    """`core` may use the adapter protocols; it may never import an implementation.

    Concrete adapters are resolved at runtime through `adapters.registry`, which is the mechanism that
    keeps the core ignorant of who its brands and channels are.
    """
    offenders: list[str] = []
    for path in sorted(CORE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            module: str | None = None
            if isinstance(node, ast.ImportFrom):
                module = node.module or ""
            elif isinstance(node, ast.Import):
                module = " ".join(a.name for a in node.names)
            if module and (
                "brandcortex.adapters.source" in module or "brandcortex.adapters.channel" in module
            ):
                offenders.append(f"{path.relative_to(CORE)}:{node.lineno} -> {module}")
    assert not offenders, f"core/ imports concrete adapters: {offenders}"
