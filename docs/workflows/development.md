# 开发工作流

## 本地迭代循环

1. 先阅读 `AGENTS.md` 和当前任务对应文档。
2. 设置 `PYTHONPATH=src` 以便直接运行模块。
3. 做满足当前契约的最小变更。
4. 运行 `scripts/check.ps1`。
5. 如果结构发生变化，补充对应的 ADR 或架构文档。

## 常用命令

```powershell
$env:PYTHONPATH='src'
python -m harness_ai_learning analyze samples/intro_note.txt
python -m harness_ai_learning run-loop samples/intro_note.txt
python -m unittest discover -s tests -p "test_*.py"
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

## Docker 命令

```powershell
docker compose build
docker compose run --rm app analyze samples/intro_note.txt
docker compose run --rm app run-loop samples/intro_note.txt
docker compose run --rm app python -m unittest discover -s tests -p "test_*.py"
```

## Pre-Commit Hook

示例 pre-commit hook 位于 `.githooks/pre-commit`，启用方式如下：

```powershell
git config core.hooksPath .githooks
```

## 基本原则

如果文档、代码和检查结果不一致，先停下来对齐，再继续开发。
