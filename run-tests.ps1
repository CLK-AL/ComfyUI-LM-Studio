# Run the ComfyUI-LM-Studio unit test suite against the ComfyUI virtualenv.
# Searches (in order):
#   .\venv, .\.venv                 # local to this custom node
#   ..\venv, ..\.venv               # parent folder
#   ..\..\venv, ..\..\.venv         # ComfyUI root (typical layout)
# Override with $env:COMFYUI_VENV = 'C:\path\to\venv'.
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Find-Venv {
    if ($env:COMFYUI_VENV) {
        if (-not (Test-Path $env:COMFYUI_VENV)) {
            throw "COMFYUI_VENV is set but does not exist: $env:COMFYUI_VENV"
        }
        return (Resolve-Path $env:COMFYUI_VENV).Path
    }
    $candidates = @(
        '.\venv', '.\.venv',
        '..\venv', '..\.venv',
        '..\..\venv', '..\..\.venv'
    )
    foreach ($c in $candidates) {
        if (-not (Test-Path $c)) { continue }
        $winPy   = Join-Path $c 'Scripts\python.exe'
        $unixPy  = Join-Path $c 'bin\python'
        if ((Test-Path $winPy) -or (Test-Path $unixPy)) {
            return (Resolve-Path $c).Path
        }
    }
    throw "No ComfyUI venv found. Set `$env:COMFYUI_VENV or create one of: $($candidates -join ', ')"
}

$venv = Find-Venv
$winPy  = Join-Path $venv 'Scripts\python.exe'
$unixPy = Join-Path $venv 'bin\python'
if (Test-Path $winPy) { $py = $winPy } else { $py = $unixPy }

Write-Host "[run-tests] using venv: $venv"
Write-Host "[run-tests] python   : $py"

# Install test-only deps if missing. Node runtime deps (requests, numpy,
# Pillow) should already be in the ComfyUI venv.
& $py -m pip install -q pytest wiremock 2>&1 | Out-Null

# pytest forwards remaining args.
& $py -m pytest @args
exit $LASTEXITCODE
