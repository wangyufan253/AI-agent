from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = [ROOT / "README.md", ROOT / "AGENTS.md", *ROOT.joinpath("docs").rglob("*.md")]
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def normalize(source: Path, target: str) -> Path | None:
    if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
        return None
    clean = target.split("#", 1)[0]
    if not clean:
        return None
    return (source.parent / clean).resolve()


def main() -> int:
    missing: list[str] = []
    for doc in DOCS:
        text = doc.read_text(encoding="utf-8")
        for match in LINK_PATTERN.findall(text):
            resolved = normalize(doc, match)
            if resolved is None:
                continue
            if not resolved.exists():
                missing.append(f"{doc.relative_to(ROOT)} -> {match}")

    if missing:
        print("文档链接检查未通过:")
        for item in missing:
            print(f"- {item}")
        return 1

    print("文档链接检查通过。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
