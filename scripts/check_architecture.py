from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "harness_ai_learning"

LAYER_BY_PATH = {
    "domain": "domain",
    "application": "application",
    "infrastructure": "infrastructure",
    "harness": "harness",
    "runtime": "runtime",
    "interfaces": "interfaces",
}

ALLOWED = {
    "domain": set(),
    "application": {"domain"},
    "infrastructure": {"domain"},
    "harness": {"domain"},
    "runtime": {"application", "domain", "infrastructure", "harness"},
    "interfaces": {"domain", "runtime"},
}


def detect_layer(path: Path) -> str | None:
    parts = path.relative_to(SRC).parts
    if not parts:
        return None
    return LAYER_BY_PATH.get(parts[0])


def imported_layers(tree: ast.AST) -> set[str]:
    layers: set[str] = set()
    prefixes = tuple(f"harness_ai_learning.{name}" for name in LAYER_BY_PATH)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(prefixes):
                    layers.add(alias.name.split(".")[1])
        elif isinstance(node, ast.ImportFrom):
            if not node.module:
                continue
            module = node.module
            if module.startswith(prefixes):
                layers.add(module.split(".")[1])
    return layers


def main() -> int:
    violations: list[str] = []
    for path in SRC.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        layer = detect_layer(path)
        if layer is None:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = imported_layers(tree)
        bad = sorted(imports - ALLOWED[layer] - {layer})
        if bad:
            rel = path.relative_to(ROOT)
            violations.append(f"{rel}: 分层 '{layer}' 不能导入 {', '.join(bad)}")

    if violations:
        print("架构检查未通过:")
        for item in violations:
            print(f"- {item}")
        return 1

    print("架构检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
