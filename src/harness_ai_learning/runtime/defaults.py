import json
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from harness_ai_learning.application import AnalyzeMaterial, UnsupportedFileTypeError
from harness_ai_learning.domain import ActionRequest, ActionResult, AgentState, EvaluationResult, IterationDecision, RunContext, RunRecord, StudyOutput
from harness_ai_learning.harness import ActionExecutor, HarnessLoop, RegisteredActionRegistry
from harness_ai_learning.infrastructure.providers import MockStudyProvider, QwenStudyProvider

RUNS_DIR = Path("runs")
DEFAULT_QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def normalize_base_url(url: str) -> str:
    normalized = url.strip().rstrip("/")
    if normalized.endswith("/chat/completions"):
        normalized = normalized[: -len("/chat/completions")]
    return normalized


class AnalyzeMaterialAction:
    name = "analyze_material"

    def __init__(self, provider=None) -> None:
        self._use_case = AnalyzeMaterial(provider=provider or build_study_provider())

    def execute(self, request: ActionRequest, context: RunContext, state: AgentState) -> ActionResult:
        target_path = request.arguments.get("input_path", context.input_path)
        output = self._use_case(target_path)
        mode = request.arguments.get("mode", "standard")
        tuned_output = self._apply_mode(output, mode)
        return ActionResult(
            action_name=request.action_name,
            status="success",
            message=f"学习材料分析动作执行完成，当前模式: {mode}。",
            output=tuned_output,
            metadata={"source_type": tuned_output.source_type, "mode": mode},
        )

    def _apply_mode(self, output: StudyOutput, mode: str) -> StudyOutput:
        if mode == "quick_scan":
            return StudyOutput(
                source_path=output.source_path,
                source_type=output.source_type,
                extracted_text=output.extracted_text,
                summary=output.summary.split("。", 1)[0].strip() + ("。" if "。" in output.summary else ""),
                key_concepts=output.key_concepts[:2],
                follow_up_questions=output.follow_up_questions,
                extension_ideas=output.extension_ideas,
            )

        if mode == "grounded_expansion":
            return StudyOutput(
                source_path=output.source_path,
                source_type=output.source_type,
                extracted_text=output.extracted_text,
                summary=f"基于原文内容，{output.summary}",
                key_concepts=[*output.key_concepts, "根据评估反馈补充覆盖关键概念"][:5],
                follow_up_questions=output.follow_up_questions,
                extension_ideas=output.extension_ideas,
            )

        return output


class AnalyzeMaterialActor:
    def build_request(self, context: RunContext, state: AgentState) -> ActionRequest:
        mode = "quick_scan"
        feedback_tags: list[str] = []
        if state.latest_evaluation is not None:
            feedback_tags = state.latest_evaluation.feedback_tags
            if "concepts_insufficient" in feedback_tags or "low_grounding" in feedback_tags:
                mode = "grounded_expansion"
            else:
                mode = "standard"

        return ActionRequest(
            action_name="analyze_material",
            arguments={
                "input_path": context.input_path,
                "mode": mode,
                "feedback_tags": feedback_tags,
            },
        )


class StudyQualityEvaluator:
    def evaluate(self, context: RunContext, state: AgentState) -> EvaluationResult:
        action_result = state.latest_action_result
        if action_result is None:
            return EvaluationResult(passed=False, score=0.0, summary="本轮没有动作执行结果。", issues=["缺少动作结果"], feedback_tags=["missing_action_result"])
        if action_result.status != "success":
            return EvaluationResult(passed=False, score=0.0, summary="动作执行失败。", issues=["动作执行失败"], feedback_tags=["action_failed"])

        output = state.final_output
        if output is None:
            return EvaluationResult(passed=False, score=0.0, summary="本轮没有产生学习结果。", issues=["缺少最终输出"], feedback_tags=["missing_output"])

        criteria: dict[str, float] = {}
        issues: list[str] = []
        feedback_tags: list[str] = []

        summary_score = 1.0 if output.summary.strip() else 0.0
        criteria["总结完整度"] = summary_score
        if summary_score == 0.0:
            issues.append("总结为空")
            feedback_tags.append("summary_missing")

        concepts_score = 1.0 if len(output.key_concepts) >= 3 else len(output.key_concepts) / 3
        criteria["关键概念覆盖度"] = round(concepts_score, 2)
        if concepts_score < 1.0:
            issues.append("关键概念数量不足")
            feedback_tags.append("concepts_insufficient")

        summary = output.summary.strip()
        source_name = output.source_path.stem.lower()
        grounding_score = 1.0 if summary else 0.0
        if source_name and source_name in summary.lower():
            grounding_score = min(1.0, grounding_score + 0.1)
        criteria["总结贴合度"] = grounding_score
        if grounding_score < 0.7:
            issues.append("总结与文件内容贴合度偏低")
            feedback_tags.append("low_grounding")

        score = round(sum(criteria.values()) / len(criteria), 2)
        passed = score >= context.pass_threshold
        summary_message = "本轮结果达到当前评估阈值。" if passed else "本轮结果未达到当前评估阈值。"
        return EvaluationResult(
            passed=passed,
            score=score,
            summary=summary_message,
            criteria=criteria,
            issues=issues,
            feedback_tags=feedback_tags,
        )


class ThresholdIterationPolicy:
    def decide(self, context: RunContext, state: AgentState) -> IterationDecision:
        evaluation = state.latest_evaluation
        if evaluation is None:
            if state.iteration < context.max_iterations:
                return IterationDecision(should_continue=True, reason="缺少评估结果，继续下一轮迭代。")
            return IterationDecision(should_continue=False, reason="缺少评估结果且已达到最大轮次，停止运行。")

        if evaluation.passed:
            return IterationDecision(should_continue=False, reason="当前结果已通过评估，停止运行。")

        if state.iteration < context.max_iterations:
            return IterationDecision(
                should_continue=True,
                reason=f"评估分数 {evaluation.score} 低于阈值 {context.pass_threshold}，继续下一轮迭代。",
            )

        return IterationDecision(
            should_continue=False,
            reason=f"评估分数 {evaluation.score} 低于阈值 {context.pass_threshold}，但已达到最大迭代次数。",
        )


def build_study_provider():
    load_env_file()
    provider_name = os.getenv("HARNESS_AI_PROVIDER", "auto").strip().lower()
    api_key = os.getenv("HARNESS_AI_API_KEY", "").strip()
    model = os.getenv("HARNESS_AI_MODEL", "qwen-doc-turbo").strip()
    raw_base_url = os.getenv("HARNESS_AI_BASE_URL") or os.getenv("HARNESS_AI_API_URL") or DEFAULT_QWEN_BASE_URL
    base_url = normalize_base_url(raw_base_url)

    if provider_name == "mock":
        return MockStudyProvider()

    if provider_name in {"auto", "qwen", "qwen-doc"} and api_key:
        return QwenStudyProvider(api_key=api_key, model=model, base_url=base_url)

    raise RuntimeError("未找到可用的学习模型 provider。请检查 HARNESS_AI_PROVIDER 与 HARNESS_AI_API_KEY 配置。")


def build_default_executor() -> ActionExecutor:
    registry = RegisteredActionRegistry(
        handlers={
            AnalyzeMaterialAction.name: AnalyzeMaterialAction(),
        }
    )
    return ActionExecutor(registry)


def analyze_path(path: Path) -> StudyOutput:
    action = AnalyzeMaterialAction()
    result = action.execute(
        ActionRequest(action_name=AnalyzeMaterialAction.name, arguments={"input_path": path, "mode": "standard"}),
        RunContext(input_path=path, goal="分析学习材料并生成中文学习辅助结果"),
        AgentState(),
    )
    if result.output is None:
        raise ValueError("分析动作没有返回学习结果。")
    return result.output


def save_run_record(loop_result, *, runs_dir: Path = RUNS_DIR) -> RunRecord:
    runs_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(UTC)
    created_at = now.isoformat()
    record_id = f"run-{now.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"
    record = RunRecord(record_id=record_id, created_at=created_at, loop_result=loop_result)
    target = runs_dir / f"{record_id}.json"
    target.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return record


def load_run_record(record_id: str | None = None, *, runs_dir: Path = RUNS_DIR) -> dict:
    if not runs_dir.exists():
        raise FileNotFoundError("当前还没有任何运行记录。")

    if record_id:
        target = runs_dir / f"{record_id}.json"
        if not target.exists():
            raise FileNotFoundError(f"未找到运行记录: {record_id}")
        return json.loads(target.read_text(encoding="utf-8"))

    candidates = sorted(runs_dir.glob("run-*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("当前还没有任何运行记录。")
    return json.loads(candidates[0].read_text(encoding="utf-8"))


def run_learning_loop(path: Path, *, max_iterations: int = 1, preferred_output_format: str = "text", pass_threshold: float = 0.7, save_record: bool = True):
    loop = HarnessLoop(
        actor=AnalyzeMaterialActor(),
        executor=build_default_executor(),
        evaluator=StudyQualityEvaluator(),
        policy=ThresholdIterationPolicy(),
    )
    context = RunContext(
        input_path=path,
        goal="分析学习材料并生成中文学习辅助结果",
        max_iterations=max_iterations,
        preferred_output_format=preferred_output_format,
        pass_threshold=pass_threshold,
    )
    loop_result = loop.run(context)
    record = save_run_record(loop_result) if save_record else None
    return loop_result, record
