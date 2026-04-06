$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
$env:PYTHONPATH = "src"

Write-Output "== 仓库 =="
Write-Output $root.Path
Write-Output ""
Write-Output "== 关键文档 =="
Write-Output "- AGENTS.md"
Write-Output "- docs/index.md"
Write-Output "- docs/architecture.md"
Write-Output "- docs/contracts/cli.md"
Write-Output ""
Write-Output "== 常用命令 =="
Write-Output "- python -m harness_ai_learning analyze samples/intro_note.txt"
Write-Output "- python -m unittest discover -s tests -p \"test_*.py\""
Write-Output "- powershell -ExecutionPolicy Bypass -File scripts/check.ps1"
Write-Output ""
Write-Output "== 当前结构快照 =="
powershell -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "tree.ps1")
