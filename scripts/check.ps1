$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

python -m unittest discover -s tests -p "test_*.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/check_architecture.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python scripts/check_docs.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
