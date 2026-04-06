from pathlib import Path

from harness_ai_learning.domain import StudyOutput, StudyProvider


class UnsupportedFileTypeError(ValueError):
    """在没有可支持的文件类型时抛出。"""


class AnalyzeMaterial:
    supported_suffixes = {".txt", ".md", ".pdf"}

    def __init__(self, *, provider: StudyProvider) -> None:
        self._provider = provider

    def __call__(self, path: str | Path) -> StudyOutput:
        source_path = Path(path)
        if not source_path.exists():
            raise FileNotFoundError(f"输入文件不存在: {source_path}")

        suffix = source_path.suffix.lower()
        if suffix not in self.supported_suffixes:
            raise UnsupportedFileTypeError(
                f"暂不支持的文件类型: '{source_path.suffix or '<无后缀>'}'。"
                "当前主路径仅支持 .txt、.md 和 .pdf 文件直传。"
            )

        return self._provider.generate(
            source_path=source_path,
            source_type=suffix.lstrip("."),
        )
