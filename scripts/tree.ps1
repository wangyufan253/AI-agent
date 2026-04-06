$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Get-ChildItem -Path $root -Recurse -Depth 3 |
    Where-Object {
        $_.FullName -notmatch "\\__pycache__\\" -and
        $_.FullName -notmatch "\\.git\\" -and
        $_.FullName -notmatch "\\tests\\_tmp\\"
    } |
    ForEach-Object {
        $relative = $_.FullName.Substring($root.Path.Length + 1)
        if ($_.PSIsContainer) {
            "[dir]  $relative"
        } else {
            "[file] $relative"
        }
    }
