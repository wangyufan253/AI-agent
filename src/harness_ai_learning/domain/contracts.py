from pathlib import Path
from typing import Protocol

from .harness import ActionRequest, ActionResult, AgentState, EvaluationResult, IterationDecision, RunContext
from .study_output import StudyOutput


class StudyProvider(Protocol):
    def generate(self, *, source_path: Path, source_type: str) -> StudyOutput: ...


class LoopActor(Protocol):
    def build_request(self, context: RunContext, state: AgentState) -> ActionRequest: ...


class ActionHandler(Protocol):
    def execute(self, request: ActionRequest, context: RunContext, state: AgentState) -> ActionResult: ...


class ActionRegistry(Protocol):
    def get(self, action_name: str) -> ActionHandler: ...


class LoopEvaluator(Protocol):
    def evaluate(self, context: RunContext, state: AgentState) -> EvaluationResult: ...


class IterationPolicy(Protocol):
    def decide(self, context: RunContext, state: AgentState) -> IterationDecision: ...
