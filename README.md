# harness-ai-learning

`harness-ai-learning` 是一个面向中文用户的、以 Harness 为先的 Agent 学习系统样板仓库。这里的重点不只是“生成学习结果”，更是学习如何为 Agent 搭建一个可观测、可评估、可迭代的运行 Harness。

## 从这里开始

- 阅读 `AGENTS.md`
- 打开 `docs/index.md`
- 运行 `powershell -ExecutionPolicy Bypass -File scripts/context.ps1`

## 当前学习重点

当前阶段已经完成：

- 受控执行循环
- 动作执行层
- 评估器与策略分离
- 最小运行记录与查看入口
- 真实模型 provider 接口与 mock 回退机制

## 当前产品切片

当前 MVP 可以分析本地 `.txt`、`.md` 和 `.pdf` 文件，并返回结构化学习结果。

同时，系统已经具备最小 Harness loop：

- 固定的 `RunContext`
- 动态的 `AgentState`
- 标准化的 `ActionRequest` / `ActionResult`
- 独立的 `EvaluationResult`
- 独立的 `IterationDecision`
- 落盘到 `runs/` 的 `RunRecord`

## 模型接入

当前 runtime 会优先读取 `.env` 或环境变量：

- `HARNESS_AI_PROVIDER`
- `HARNESS_AI_API_KEY`
- `HARNESS_AI_MODEL`
- `HARNESS_AI_BASE_URL`

如果配置齐全，会优先调用真实模型 provider；如果未配置或你手动指定 `HARNESS_AI_PROVIDER=mock`，系统会回退到 mock provider。

## 这个仓库里的三大支柱

### 上下文工程

- `AGENTS.md` 是给 Agent 的简洁入口
- `docs/` 提供按需打开的中文上下文，而不是一份巨大的说明书
- `scripts/context.ps1` 和 `scripts/tree.ps1` 提供动态上下文入口

### 架构约束

- 源码按 `domain`、`application`、`infrastructure`、`harness`、`runtime`、`interfaces` 分层
- `scripts/check_architecture.py` 自动验证分层导入规则
- `docs/contracts/cli.md` 定义 CLI 行为契约

### 熵管理

- `scripts/check_docs.py` 验证 Markdown 链接有效性
- `scripts/check.ps1` 统一运行可重复验证
- ADR、契约和实现必须同步演进
- `runs/` 记录稳定运行结果，便于后续加入更强 replay 能力

## 快速命令

```powershell
$env:PYTHONPATH='src'
python -m harness_ai_learning analyze samples/intro_note.txt
python -m harness_ai_learning run-loop samples/intro_note.txt
python -m harness_ai_learning run-loop samples/intro_note.txt --max-iterations 2 --pass-threshold 0.9
python -m harness_ai_learning show-run
python -m unittest discover -s tests -p "test_*.py"
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

## 下一步演进方向

- 用更可信的 evaluator 替换当前教学型启发式打分
- 为动作执行层加入参数校验、失败分类和重试入口
- 在已有 `RunRecord` 基础上再引入真正的 replay
