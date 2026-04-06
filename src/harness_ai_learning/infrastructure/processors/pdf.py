import re
from pathlib import Path


class PdfProcessor:
    supported_suffixes = {".pdf"}
    _text_pattern = re.compile(rb"\(([^()]*)\)\s*Tj|\[(.*?)\]\s*TJ", re.DOTALL)
    _array_text_pattern = re.compile(rb"\(([^()]*)\)")

    def can_process(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_suffixes

    def extract_text(self, path: Path) -> str:
        data = path.read_bytes()
        chunks: list[str] = []

        for match in self._text_pattern.finditer(data):
            direct_text, array_text = match.groups()
            if direct_text is not None:
                decoded = self._decode_pdf_text(direct_text)
                if decoded:
                    chunks.append(decoded)
                continue

            if array_text is not None:
                parts = [self._decode_pdf_text(item) for item in self._array_text_pattern.findall(array_text)]
                merged = "".join(part for part in parts if part)
                if merged:
                    chunks.append(merged)

        text = "\n".join(chunk.strip() for chunk in chunks if chunk.strip())
        return text.strip()

    def _decode_pdf_text(self, payload: bytes) -> str:
        payload = payload.replace(rb"\(", b"(")
        payload = payload.replace(rb"\)", b")")
        payload = payload.replace(rb"\\", bytes([92]))
        try:
            return payload.decode("utf-8")
        except UnicodeDecodeError:
            return payload.decode("latin-1", errors="ignore")
