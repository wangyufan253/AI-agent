from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from .study_output import StudyOutput

StepName = Literal["observe", "decide", "act", "verify", "update_state", "continue_or_stop"]
ActionStatus = Literal["success", "error"]


@dataclass(slots=True)
class RunContext:
    input_path: Path
    goal: str
    max_iterations: int = 1
    preferred_output_format: str = "text"
    pass_threshold: float = 0.7


@dataclass(slots=True)
class ActionRequest:
    action_name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ActionResult:
    action_name: str
    status: ActionStatus
    message: str
    output: StudyOutput | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StepResult:
    step_name: StepName
    status: Literal["success", "error"]
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class EvaluationResult:
    passed: bool
    score: float
    summary: str
    criteria: dict[str, float] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    feedback_tags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class IterationDecision:
    should_continue: bool
    reason: str


@dataclass(slots=True)
class AgentState:
    iteration: int = 0
    latest_observation: str = ""
    latest_plan: str = ""
    latest_action: str = ""
    latest_step: StepName | None = None
    latest_request: ActionRequest | None = None
    latest_action_result: ActionResult | None = None
    latest_evaluation: EvaluationResult | None = None
    final_output: StudyOutput | None = None
    history: list[StepResult] = field(default_factory=list)


@dataclass(slots=True)
class LoopResult:
    context: RunContext
    state: AgentState
    decision: IterationDecision

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["context"]["input_path"] = str(self.context.input_path)
        if self.state.final_output is not None:
            payload["state"]["final_output"] = self.state.final_output.to_dict()
        return payload


@dataclass(slots=True)
class RunRecord:
    record_id: str
    created_at: str
    loop_result: LoopResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "created_at": self.created_at,
            "loop_result": self.loop_result.to_dict(),
        }
