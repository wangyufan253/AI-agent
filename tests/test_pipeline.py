import os
import shutil
import unittest
from pathlib import Path

from harness_ai_learning.application import AnalyzeMaterial, UnsupportedFileTypeError
from harness_ai_learning.domain import AgentState, EvaluationResult, RunContext
from harness_ai_learning.harness import HarnessLoop
from harness_ai_learning.infrastructure.providers import MockStudyProvider
from harness_ai_learning.runtime.defaults import AnalyzeMaterialActor, StudyQualityEvaluator, ThresholdIterationPolicy, build_default_executor, load_run_record, run_learning_loop


class AlwaysFailEvaluator:
    def evaluate(self, context: RunContext, state: AgentState) -> EvaluationResult:
        return EvaluationResult(
            passed=False,
            score=0.1,
            summary="评估故意失败，用于验证策略分支。",
            criteria={"模拟分数": 0.1},
            issues=["故意失败"],
            feedback_tags=["forced_failure"],
        )


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.use_case = AnalyzeMaterial(provider=MockStudyProvider())
        runs_dir = Path("runs")
        if runs_dir.exists():
            shutil.rmtree(runs_dir, ignore_errors=True)
        os.environ["HARNESS_AI_PROVIDER"] = "mock"

    def test_analyze_text_file_returns_study_output(self):
        result = self.use_case(Path("samples/intro_note.txt"))

        self.assertEqual(result.source_type, "txt")
        self.assertTrue(result.summary)
        self.assertGreaterEqual(len(result.key_concepts), 3)

    def test_analyze_pdf_file_returns_study_output(self):
        result = self.use_case(Path("samples/intro_note.pdf"))

        self.assertEqual(result.source_type, "pdf")
        self.assertTrue(result.extracted_text)
        self.assertTrue(result.summary)

    def test_missing_file_raises_clear_error(self):
        with self.assertRaises(FileNotFoundError):
            self.use_case(Path("samples/missing.txt"))

    def test_unsupported_extension_raises_clear_error(self):
        temp_dir = Path("tests/_tmp/pipeline")
        temp_dir.mkdir(parents=True, exist_ok=True)
        sample = temp_dir / "lesson.png"
        sample.write_text("placeholder", encoding="utf-8")

        try:
            with self.assertRaises(UnsupportedFileTypeError):
                self.use_case(sample)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_harness_loop_runs_single_controlled_iteration(self):
        loop = HarnessLoop(
            actor=AnalyzeMaterialActor(),
            executor=build_default_executor(),
            evaluator=StudyQualityEvaluator(),
            policy=ThresholdIterationPolicy(),
        )
        result = loop.run(
            RunContext(
                input_path=Path("samples/intro_note.txt"),
                goal="分析学习材料并生成中文学习辅助结果",
                max_iterations=1,
            )
        )

        self.assertEqual(result.state.iteration, 1)
        self.assertTrue(result.decision.reason)
        self.assertIsNotNone(result.state.final_output)
        self.assertEqual(result.state.history[-1].step_name, "continue_or_stop")
        self.assertEqual(result.state.latest_request.action_name, "analyze_material")
        self.assertEqual(result.state.latest_action_result.action_name, "analyze_material")
        self.assertTrue(result.state.latest_evaluation.passed)
        self.assertIn("总结完整度", result.state.latest_evaluation.criteria)

    def test_policy_continues_when_score_is_below_threshold(self):
        loop = HarnessLoop(
            actor=AnalyzeMaterialActor(),
            executor=build_default_executor(),
            evaluator=AlwaysFailEvaluator(),
            policy=ThresholdIterationPolicy(),
        )
        result = loop.run(
            RunContext(
                input_path=Path("samples/intro_note.txt"),
                goal="分析学习材料并生成中文学习辅助结果",
                max_iterations=2,
                pass_threshold=0.7,
            )
        )

        self.assertEqual(result.state.iteration, 2)
        self.assertFalse(result.state.latest_evaluation.passed)
        self.assertIn("低于阈值", result.decision.reason)

    def test_actor_changes_request_after_feedback(self):
        loop_result, _ = run_learning_loop(
            Path("samples/intro_note.txt"),
            max_iterations=2,
            pass_threshold=0.9,
            save_record=False,
        )

        decide_steps = [step for step in loop_result.state.history if step.step_name == "decide"]
        self.assertEqual(loop_result.state.iteration, 2)
        self.assertEqual(decide_steps[0].payload["mode"], "quick_scan")
        self.assertEqual(decide_steps[1].payload["mode"], "grounded_expansion")
        self.assertIn("concepts_insufficient", decide_steps[1].payload["feedback_tags"])
        self.assertTrue(loop_result.state.latest_evaluation.passed)

    def test_run_loop_writes_and_loads_record(self):
        loop_result, record = run_learning_loop(Path("samples/intro_note.txt"), save_record=True)

        self.assertIsNotNone(record)
        self.assertTrue((Path("runs") / f"{record.record_id}.json").exists())
        loaded = load_run_record(record.record_id)
        self.assertEqual(loaded["record_id"], record.record_id)
        self.assertEqual(loaded["loop_result"]["state"]["iteration"], loop_result.state.iteration)


if __name__ == "__main__":
    unittest.main()
