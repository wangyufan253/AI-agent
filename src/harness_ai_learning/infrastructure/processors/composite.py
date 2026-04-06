from pathlib import Path

from harness_ai_learning.domain import StudyMaterialProcessor


class CompositeProcessor:
    def __init__(self, processors: list[StudyMaterialProcessor]) -> None:
        self._processors = processors

    def can_process(self, path: Path) -> bool:
        return self._find_processor(path) is not None

    def extract_text(self, path: Path) -> str:
        processor = self._find_processor(path)
        if processor is None:
            raise ValueError(f"没有可用于该文件类型的处理器: {path}")
        return processor.extract_text(path)

    def _find_processor(self, path: Path) -> StudyMaterialProcessor | None:
        for processor in self._processors:
            if processor.can_process(path):
                return processor
        return None
