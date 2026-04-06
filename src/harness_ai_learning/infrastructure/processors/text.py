from pathlib import Path


class TextProcessor:
    supported_suffixes = {".txt", ".md"}

    def can_process(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_suffixes

    def extract_text(self, path: Path) -> str:
        return path.read_text(encoding="utf-8").strip()
