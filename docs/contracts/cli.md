# CLI 契约

## 命令

```text
python -m harness_ai_learning analyze <path> [--format text|json]
python -m harness_ai_learning run-loop <path> [--max-iterations N] [--format text|json]
python -m harness_ai_learning show-run [--record-id ID] [--format text|json]
```

## 输入

- `<path>` 必须指向一个存在的本地文件
- 当前支持的后缀是 `.txt`、`.md` 和 `.pdf`
- 遇到不支持的后缀时，必须返回非零退出码，并输出清晰中文错误信息
- `show-run` 默认读取最近一次运行记录，也可通过 `--record-id` 指定记录

## 输出模式

### `analyze --format text`

人类可读输出，按以下顺序输出分段：

1. `来源`
2. `类型`
3. `总结`
4. `关键概念`
5. `追问问题`
6. `延伸建议`

### `analyze --format json`

输出一个 JSON 对象，包含以下中文键：

- `来源路径`
- `来源类型`
- `提取文本`
- `总结`
- `关键概念`
- `追问问题`
- `延伸建议`

### `run-loop`

输出 Harness loop 的运行结果，至少包含：

- 当前轮次
- 是否停止
- 停止原因
- 最近一步名称
- 最近评估结果
- 评估细项
- 最终学习结果
- 记录信息

当前 `run-loop` 使用已注册动作 `analyze_material` 执行实际分析，并默认在 `runs/` 目录下生成一份 JSON 记录。

### `show-run`

显示最近一次或指定 ID 的运行记录内容，用于最小回放视图。

## 退出行为

- 成功时返回 `0`
- 缺失文件、提取后为空、不支持的后缀、找不到运行记录等用户级错误返回 `2`

## 当前非目标

当前 CLI 还不支持：

- 图片处理
- 学习记录持久化以外的数据库存储
- 真实 LLM provider 调用
- 复杂多步规划
- 真正的逐步 replay 执行
- 动作权限授权与重试策略
