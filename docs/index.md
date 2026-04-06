# 文档索引

这个仓库按“渐进式披露”组织。先从这里开始，再按需打开更具体的文档。

## 核心上下文

- [Agent 指南](../AGENTS.md)
- [架构说明](architecture.md)
- [CLI 契约](contracts/cli.md)
- [开发工作流](workflows/development.md)
- [ADR 0001：仓库结构](adr/0001-repo-shape.md)

## 动态上下文入口

- `scripts/context.ps1` 输出紧凑版运行时上下文
- `scripts/tree.ps1` 输出当前仓库结构快照
- `scripts/check.ps1` 运行测试与 Harness 检查

## 当前范围

当前 MVP 支持：

- 分析 `.txt`、`.md` 和 `.pdf` 文件
- 通过 mock provider 生成结构化学习结果
- 通过最小 Harness loop 驱动一次受控执行
- 验证架构边界和文档链接有效性

未来新增 OCR、真实 LLM provider、trace/replay 时，必须在不破坏当前架构约束的前提下演进。
