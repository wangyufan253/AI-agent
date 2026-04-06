$ErrorActionPreference = "Stop"
$env:PYTHONPATH = "src"

python -m unittest discover -s tests -p "test_*.py"
