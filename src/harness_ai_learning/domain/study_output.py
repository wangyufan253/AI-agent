from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class StudyOutput:
    source_path: Path
    source_type: str
    extracted_text: str
    summary: str
    key_concepts: list[str]
    follow_up_questions: list[str]
    extension_ideas: list[str]

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["source_path"] = str(self.source_path)
        return payload
