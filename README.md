# harness-ai-learning

`harness-ai-learning` 是一个面向中文用户的 CLI 学习助手。用户可以把本地学习材料交给系统，由模型直接读取文件内容，生成结构化的学习结果，并在受控循环下完成最小化的自评估与迭代。

## 项目功能

- 支持分析本地 `.txt`、`.md`、`.pdf` 文件
- 输出中文学习结果，包括：
  - 总结
  - 关键概念
  - 追问问题
  - 延伸建议
- 支持最小 Harness Loop：
  - `observe`
  - `decide`
  - `act`
  - `verify`
  - `update_state`
  - `continue_or_stop`
- 支持运行记录落盘，可查看最近一次或指定一次运行结果
- 支持真实模型与 mock provider 两种模式

## 适用场景

- 快速整理课程笔记
- 阅读论文后生成中文学习摘要
- 从技术文档中提炼关键概念
- 基于原始材料生成追问问题和延伸方向

## 当前支持的命令

### 1. 分析单个文件

```powershell
$env:PYTHONPATH='src'
python -m harness_ai_learning analyze samples/intro_note.txt
python -m harness_ai_learning analyze samples/intro_note.pdf --format json
```

### 2. 运行带评估的学习循环

```powershell
$env:PYTHONPATH='src'
python -m harness_ai_learning run-loop samples/intro_note.txt
python -m harness_ai_learning run-loop samples/intro_note.pdf --max-iterations 2 --pass-threshold 0.9
```

### 3. 查看最近一次运行记录

```powershell
$env:PYTHONPATH='src'
python -m harness_ai_learning show-run
python -m harness_ai_learning show-run --format json
```

## 输出内容

系统当前会返回一组结构化学习结果：

- `总结`
- `关键概念`
- `追问问题`
- `延伸建议`

在 `run-loop` 模式下，还会额外返回：

- 当前轮次
- 动作请求
- 最近评估
- 停止原因
- 记录信息

## 模型配置

项目默认通过 `.env` 或环境变量读取模型配置：

- `HARNESS_AI_PROVIDER`
- `HARNESS_AI_API_KEY`
- `HARNESS_AI_MODEL`
- `HARNESS_AI_BASE_URL`

示例：

```env
HARNESS_AI_PROVIDER=auto
HARNESS_AI_API_KEY=your_api_key
HARNESS_AI_MODEL=qwen-doc-turbo
HARNESS_AI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

如果没有配置真实模型，也可以手动切到 mock：

```powershell
$env:HARNESS_AI_PROVIDER='mock'
```

## 项目结构

```text
src/harness_ai_learning/
  domain/          领域对象与契约
  application/     用例编排
  infrastructure/  provider 与文件处理实现
  harness/         受控执行循环
  runtime/         默认装配与运行时配置
  interfaces/      CLI 入口
```

## 本地验证

```powershell
$env:PYTHONPATH='src'
$env:HARNESS_AI_PROVIDER='mock'
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_architecture.py
python scripts/check_docs.py
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

## 当前状态

当前版本已经可以完成：

- 文件直传模型分析
- 中文学习结果生成
- 最小自循环迭代
- 运行记录查看

后续可以继续扩展：

- 更可信的 evaluator
- 多动作规划
- 更强的 replay / experiment 能力
- 图片输入与更完整的多模态支持
