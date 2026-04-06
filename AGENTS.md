# AGENTS.md

这个仓库是一个以 Harness 为先的学习型项目。产品表面上是一个 CLI 学习助手，但首要目标是学习如何为 Agent 搭建一个可控的运行循环，并逐步补上评估、策略和回放能力。

## 优先阅读

请按顺序阅读以下文件：

1. `docs/index.md`
2. `docs/architecture.md`
3. `docs/contracts/cli.md`
4. `docs/workflows/development.md`
5. `docs/adr/0001-repo-shape.md`

## 仓库真相模型

- 代码仓库是唯一真相源。
- 当前最重要的结构是 Harness loop：`observe -> decide -> act -> verify -> update_state -> continue_or_stop`
- 架构规则定义在 `docs/architecture.md`，由 `scripts/check_architecture.py` 强制检查。
- CLI 行为契约定义在 `docs/contracts/cli.md`，实现和测试必须与其保持一致。
- 可重复检查统一通过 `scripts/check.ps1` 运行。

## 渐进式披露

进入仓库后，不要一次性加载全部信息。

- 先看 `docs/index.md` 获取全局地图。
- 如果任务与 loop 相关，优先阅读 `docs/architecture.md`。
- 如果任务与命令入口相关，优先阅读 `docs/contracts/cli.md`。
- 用 `scripts/context.ps1` 获取紧凑版启动上下文。
- 需要结构细节时，再运行 `scripts/tree.ps1`。

## 架构边界

允许的依赖方向：

- `domain` -> 不依赖任何项目层
- `application` -> `domain`
- `infrastructure` -> `domain`
- `harness` -> `domain`
- `runtime` -> `application`、`domain`、`harness`、`infrastructure`
- `interfaces` -> `domain`、`runtime`

## 变更流程

1. 如果行为或结构发生变化，先更新相关契约或 ADR。
2. 只实现满足当前上下文的最小代码变更。
3. 运行 `scripts/check.ps1`。
4. 如果约束检查失败，先修复架构，再继续加功能。
5. 离开仓库前，保证文档、代码和检查结果一致。
