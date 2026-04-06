# 架构说明

## 目标

`harness-ai-learning` 是一个以 Harness 为先的样板仓库，用来学习如何在明确的上下文、约束和熵管理规则下开发面向 Agent 的系统。

## 分层模型

代码库目前分成六层。

### Domain

位置：`src/harness_ai_learning/domain/`

职责：

- 核心数据结构
- 领域术语
- 不依赖交付方式或外部工具的逻辑
- Harness 的基础协议、状态对象和动作请求/结果模型
- 运行记录模型

规则：

- 不能导入 `application`、`infrastructure`、`harness`、`runtime` 或 `interfaces`
- 应尽量保持稳定，不因交互方式变化而变化

### Application

位置：`src/harness_ai_learning/application/`

职责：

- 编排用例
- 定义满足用户请求所需的动作逻辑
- 依赖领域概念和抽象契约

规则：

- 可以导入 `domain`
- 不能导入 `infrastructure`、`harness`、`runtime` 或 `interfaces`
- 不应直接处理 CLI 展示格式或具体 provider

### Infrastructure

位置：`src/harness_ai_learning/infrastructure/`

职责：

- 文件提取实现
- provider 集成
- 文件系统和外部运行时细节

规则：

- 可以导入 `domain`
- 不能导入 `application`、`harness`、`runtime` 或 `interfaces`
- 应提供可复用实现，而不是夹带 CLI 逻辑

### Harness

位置：`src/harness_ai_learning/harness/`

职责：

- 定义受控执行循环
- 组织动作执行器、动作注册表与标准化动作结果
- 在 observe、decide、act、verify、update_state、continue_or_stop 之间组织调度

规则：

- 可以导入 `domain`
- 不能导入 `application`、`infrastructure`、`runtime` 或 `interfaces`
- 不直接绑定具体工具或交付方式

### Runtime

位置：`src/harness_ai_learning/runtime/`

职责：

- 为本地运行装配具体实现
- 作为抽象与实现之间的组合根
- 把实际动作能力注册到 Harness 执行层
- 提供评估器与策略的默认实现
- 负责把稳定 loop 的结果落盘到 `runs/`

规则：

- 可以导入 `application`、`domain`、`infrastructure` 和 `harness`
- 不能导入 `interfaces`

### Interfaces

位置：`src/harness_ai_learning/interfaces/`

职责：

- CLI 参数解析
- 展示格式化
- 进程退出行为与契约对齐

规则：

- 可以导入 `domain`、`runtime`
- 不能直接包含提取逻辑、provider 逻辑或 Harness 核心逻辑

## 当前 Harness Loop

当前最小 loop 明确包含这些步骤：

1. observe
2. decide
3. act
4. verify
5. update_state
6. continue_or_stop

其中：

- `Evaluator` 负责给出结构化质量判断，包括分数、细项和问题列表
- `IterationPolicy` 只负责根据评估结果和轮次限制决定继续还是停止
- `run record` 在 loop 稳定结束后落盘，而不是在系统尚未稳定时过早引入复杂 replay

## 约束执行

下面这些自动检查用于保护架构：

- `scripts/check_architecture.py`
- `scripts/check_docs.py`
- 基于 `python -m unittest` 的单元测试

统一通过 `scripts/check.ps1` 运行。
