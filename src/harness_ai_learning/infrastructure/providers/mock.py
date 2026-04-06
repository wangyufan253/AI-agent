from pathlib import Path
from textwrap import shorten

from harness_ai_learning.domain import StudyOutput
from harness_ai_learning.infrastructure.processors import PdfProcessor, TextProcessor


class MockStudyProvider:
    name = "mock"

    def __init__(self) -> None:
        self._text_processor = TextProcessor()
        self._pdf_processor = PdfProcessor()

    def generate(self, *, source_path: Path, source_type: str) -> StudyOutput:
        extracted_text = self._extract_text(source_path)
        summary = shorten(extracted_text.replace("\n", " "), width=140, placeholder="...")
        return StudyOutput(
            source_path=source_path,
            source_type=source_type,
            extracted_text=extracted_text,
            summary=summary,
            key_concepts=[
                "尽早定义期望行为",
                "保持反馈回路足够短",
                "把验证系统视为产品的一部分",
            ],
            follow_up_questions=[
                "这个工具到底要为学习者稳定保证什么结果？",
                "哪些边界情况应该单独拥有自己的验收测试？",
            ],
            extension_ideas=[
                "加入 PDF 解析，对比不同来源格式的学习效果",
                "把学习输出保存成可复用的笔记",
            ],
        )

    def _extract_text(self, source_path: Path) -> str:
        suffix = source_path.suffix.lower()
        if suffix in {".txt", ".md"}:
            return self._text_processor.extract_text(source_path)
        if suffix == ".pdf":
            text = self._pdf_processor.extract_text(source_path)
            if text:
                return text
        return f"这是来自文件 {source_path.name} 的模拟学习材料内容。"
