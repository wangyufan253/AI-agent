import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        runs_dir = Path("runs")
        if runs_dir.exists():
            shutil.rmtree(runs_dir, ignore_errors=True)
        os.environ["HARNESS_AI_PROVIDER"] = "mock"

    def test_cli_analyze_json_output(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        completed = subprocess.run(
            [sys.executable, "-m", "harness_ai_learning", "analyze", "samples/intro_note.txt", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["来源类型"], "txt")
        self.assertTrue(payload["总结"])

    def test_cli_can_analyze_pdf(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        completed = subprocess.run(
            [sys.executable, "-m", "harness_ai_learning", "analyze", "samples/intro_note.pdf", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["来源类型"], "pdf")
        self.assertTrue(payload["提取文本"])

    def test_cli_run_loop_json_output(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        completed = subprocess.run(
            [sys.executable, "-m", "harness_ai_learning", "run-loop", "samples/intro_note.txt", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["运行结果"]["当前轮次"], 1)
        self.assertTrue(payload["运行结果"]["是否停止"])
        self.assertIn("最终学习结果", payload["运行结果"])
        self.assertIn("评估细项", payload["运行结果"]["最近评估"])
        self.assertTrue(payload["记录信息"]["记录ID"])

    def test_cli_can_trigger_self_refinement(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "harness_ai_learning",
                "run-loop",
                "samples/intro_note.txt",
                "--max-iterations",
                "2",
                "--pass-threshold",
                "0.9",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["运行结果"]["当前轮次"], 2)
        self.assertEqual(payload["运行结果"]["动作请求"]["参数"]["mode"], "grounded_expansion")

    def test_cli_show_run_reads_latest_record(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        subprocess.run(
            [sys.executable, "-m", "harness_ai_learning", "run-loop", "samples/intro_note.txt", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )
        completed = subprocess.run(
            [sys.executable, "-m", "harness_ai_learning", "show-run", "--format", "json"],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertIn("record_id", payload)
        self.assertIn("loop_result", payload)

    def test_cli_reports_unsupported_extension(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        temp_dir = Path("tests/_tmp/cli")
        temp_dir.mkdir(parents=True, exist_ok=True)
        sample = temp_dir / "scan.png"
        sample.write_text("fake image", encoding="utf-8")

        try:
            completed = subprocess.run(
                [sys.executable, "-m", "harness_ai_learning", "analyze", str(sample)],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertEqual(completed.returncode, 2)
        self.assertIn("暂不支持的文件类型", completed.stderr)


if __name__ == "__main__":
    unittest.main()
