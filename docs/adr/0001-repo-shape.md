# ADR 0001：仓库结构

## 状态

已接受

## 背景

这个项目的目标不只是交付一个 CLI，更是学习 Harness Engineering。因此仓库结构必须天然支持上下文发现、架构约束执行和漂移可见性。

## 决策

采用以下顶层结构：

- `AGENTS.md` 作为面向 Agent 的入口索引
- `docs/` 存放架构、契约、工作流和 ADR
- `src/harness_ai_learning/domain/` 存放核心模型和 Harness 基础协议
- `src/harness_ai_learning/application/` 存放动作逻辑
- `src/harness_ai_learning/infrastructure/` 存放处理器和 provider 实现
- `src/harness_ai_learning/harness/` 存放受控执行循环
- `src/harness_ai_learning/runtime/` 存放组合根和默认装配
- `src/harness_ai_learning/interfaces/` 存放 CLI 等交付层逻辑
- `scripts/` 存放可重复检查和上下文工具
- `tests/` 存放回归测试和契约验证

## 影响

正面影响：

- Agent 可以按需获取上下文，而不是一次读完整个仓库
- 架构边界可以通过简单脚本自动验证
- Harness loop 有了独立位置，不再和业务动作混在一起

代价：

- 对一个小 MVP 来说会显得更有仪式感
- 某些模块在早期会比较薄，但随着能力增长，这种结构会持续带来收益
