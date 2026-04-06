import argparse
import json
from pathlib import Path

from harness_ai_learning.runtime import UnsupportedFileTypeError, analyze_path, load_run_record, run_learning_loop


JSON_LABELS = {
    "source_path": "来源路径",
    "source_type": "来源类型",
    "extracted_text": "提取文本",
    "summary": "总结",
    "key_concepts": "关键概念",
    "follow_up_questions": "追问问题",
    "extension_ideas": "延伸建议",
}


LOOP_LABELS = {
    "iteration": "当前轮次",
    "latest_step": "最近步骤",
    "should_stop": "是否停止",
    "stop_reason": "停止原因",
    "evaluation": "最近评估",
    "evaluation_criteria": "评估细项",
    "evaluation_issues": "评估问题",
    "evaluation_feedback_tags": "反馈标签",
    "final_output": "最终学习结果",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness-ai-learning",
        description="分析本地学习材料，并通过 Harness loop 生成结构化中文学习辅助结果。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="直接分析单个本地文件。")
    analyze.add_argument("path", help="本地输入文件路径。")
    analyze.add_argument("--format", choices=("text", "json"), default="text", help="选择文本输出或 JSON 输出。")

    run_loop = subparsers.add_parser("run-loop", help="通过 Harness loop 运行一次受控分析。")
    run_loop.add_argument("path", help="本地输入文件路径。")
    run_loop.add_argument("--max-iterations", type=int, default=1, help="允许的最大迭代轮次。")
    run_loop.add_argument("--pass-threshold", type=float, default=0.7, help="评估通过阈值，越高越容易触发下一轮。")
    run_loop.add_argument("--format", choices=("text", "json"), default="text", help="选择文本输出或 JSON 输出。")

    show_run = subparsers.add_parser("show-run", help="查看最近一次或指定的运行记录。")
    show_run.add_argument("--record-id", default=None, help="指定要查看的运行记录 ID。")
    show_run.add_argument("--format", choices=("text", "json"), default="text", help="选择文本输出或 JSON 输出。")
    return parser


def render_text(result) -> str:
    lines = [
        f"来源: {result.source_path}",
        f"类型: {result.source_type}",
        "",
        "总结:",
        result.summary,
        "",
        "关键概念:",
        *[f"- {item}" for item in result.key_concepts],
        "",
        "追问问题:",
        *[f"- {item}" for item in result.follow_up_questions],
        "",
        "延伸建议:",
        *[f"- {item}" for item in result.extension_ideas],
    ]
    return "\n".join(lines)


def render_json(result) -> str:
    payload = result.to_dict()
    localized = {JSON_LABELS[key]: value for key, value in payload.items()}
    return json.dumps(localized, ensure_ascii=False, indent=2)


def render_loop_text(loop_result) -> str:
    evaluation = loop_result.state.latest_evaluation
    output = loop_result.state.final_output
    criteria_lines = []
    issue_lines = []
    feedback_tag_lines = []
    if evaluation is not None:
        criteria_lines = [f"- {name}: {score}" for name, score in evaluation.criteria.items()]
        issue_lines = [f"- {issue}" for issue in evaluation.issues] or ["- 无"]
        feedback_tag_lines = [f"- {tag}" for tag in evaluation.feedback_tags] or ["- 无"]
    lines = [
        f"当前轮次: {loop_result.state.iteration}",
        f"是否停止: {'是' if not loop_result.decision.should_continue else '否'}",
        f"停止原因: {loop_result.decision.reason}",
        f"最近步骤: {loop_result.state.latest_step}",
        f"最近动作模式: {loop_result.state.latest_request.arguments.get('mode') if loop_result.state.latest_request else '无'}",
        "",
        "最近评估:",
        f"- 是否通过: {'是' if evaluation and evaluation.passed else '否'}",
        f"- 分数: {evaluation.score if evaluation else 0.0}",
        f"- 说明: {evaluation.summary if evaluation else '无'}",
        "",
        "评估细项:",
        *(criteria_lines or ["- 无"]),
        "",
        "评估问题:",
        *issue_lines,
        "",
        "反馈标签:",
        *feedback_tag_lines,
        "",
        "最终学习结果:",
        render_text(output) if output is not None else "暂无结果",
    ]
    return "\n".join(lines)


def render_loop_json(loop_result) -> str:
    output = loop_result.state.final_output
    evaluation = loop_result.state.latest_evaluation
    payload = {
        LOOP_LABELS["iteration"]: loop_result.state.iteration,
        LOOP_LABELS["latest_step"]: loop_result.state.latest_step,
        LOOP_LABELS["should_stop"]: not loop_result.decision.should_continue,
        LOOP_LABELS["stop_reason"]: loop_result.decision.reason,
        "动作请求": {
            "名称": loop_result.state.latest_request.action_name if loop_result.state.latest_request else None,
            "参数": loop_result.state.latest_request.arguments if loop_result.state.latest_request else {},
        },
        LOOP_LABELS["evaluation"]: {
            "是否通过": evaluation.passed if evaluation else False,
            "分数": evaluation.score if evaluation else 0.0,
            "说明": evaluation.summary if evaluation else "无",
            LOOP_LABELS["evaluation_criteria"]: evaluation.criteria if evaluation else {},
            LOOP_LABELS["evaluation_issues"]: evaluation.issues if evaluation else [],
            LOOP_LABELS["evaluation_feedback_tags"]: evaluation.feedback_tags if evaluation else [],
        },
        LOOP_LABELS["final_output"]: {JSON_LABELS[key]: value for key, value in output.to_dict().items()} if output else None,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)


def render_record_text(record: dict) -> str:
    lines = [
        f"记录 ID: {record['record_id']}",
        f"创建时间: {record['created_at']}",
        "",
        "运行结果:",
        json.dumps(record["loop_result"], ensure_ascii=False, indent=2),
    ]
    return "\n".join(lines)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "analyze":
            result = analyze_path(Path(args.path))
            print(render_json(result) if args.format == "json" else render_text(result))
            return

        if args.command == "run-loop":
            loop_result, record = run_learning_loop(
                Path(args.path),
                max_iterations=max(args.max_iterations, 1),
                preferred_output_format=args.format,
                pass_threshold=args.pass_threshold,
            )
            if args.format == "json":
                payload = {
                    "运行结果": json.loads(render_loop_json(loop_result)),
                    "记录信息": {
                        "记录ID": record.record_id if record else None,
                        "创建时间": record.created_at if record else None,
                    },
                }
                print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
                return

            print(render_loop_text(loop_result))
            if record is not None:
                print()
                print(f"记录 ID: {record.record_id}")
                print(f"创建时间: {record.created_at}")
            return

        if args.command == "show-run":
            record = load_run_record(record_id=args.record_id)
            print(json.dumps(record, ensure_ascii=False, indent=2, default=str) if args.format == "json" else render_record_text(record))
            return

        parser.error(f"未知命令: {args.command}")
    except (FileNotFoundError, UnsupportedFileTypeError, ValueError) as exc:
        parser.exit(status=2, message=f"错误: {exc}\n")
