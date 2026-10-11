"""Enforces the dependency rule: inner layers may only import the standard library
and layers that sit further inside."""

import ast
import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"

ALLOWED_INTERNAL = {
    "domain": ("src.domain",),
    "usecases": ("src.domain", "src.usecases"),
}


def imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.append(node.module)
    return names


def is_allowed(module: str, allowed_internal: tuple[str, ...]) -> bool:
    top_level = module.split(".")[0]
    if top_level in sys.stdlib_module_names:
        return True
    return any(module == prefix or module.startswith(prefix + ".") for prefix in allowed_internal)


@pytest.mark.parametrize("layer", sorted(ALLOWED_INTERNAL))
def test_inner_layer_only_depends_inward(layer: str) -> None:
    violations = [
        f"{path.relative_to(SRC)}: {module}"
        for path in (SRC / layer).rglob("*.py")
        for module in imported_modules(path)
        if not is_allowed(module, ALLOWED_INTERNAL[layer])
    ]

    assert violations == []
