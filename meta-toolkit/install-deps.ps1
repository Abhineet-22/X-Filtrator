# Bootstrap Python dependencies for meta-toolkit on Windows.
param(
    [switch]$Dev
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir = Join-Path $Root ".venv"

function Find-Python {
    # Prefer the Windows py launcher (avoids Microsoft Store alias stubs).
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $version = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Command = "py"; Args = @("-3") }
        }
    }

    foreach ($candidate in @("python3", "python")) {
        if (-not (Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
        $path = (Get-Command $candidate).Source
        # Skip Microsoft Store execution-alias stubs.
        if ($path -match "WindowsApps\\python") { continue }
        $version = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{ Command = $candidate; Args = @() }
        }
    }

    throw @"
Python 3.10+ not found.

Install from https://www.python.org/downloads/ and check 'Add python.exe to PATH'.
Then disable Store aliases:
  Settings > Apps > Advanced app settings > App execution aliases
  Turn OFF 'python.exe' and 'python3.exe' under App Installer.

Reopen your terminal and run:
  .\install-deps.ps1$(if ($Dev) { ' -Dev' })
"@
}

function Invoke-Python {
    param([string[]]$PythonArgs)
    $all = $script:PythonLauncher.Args + $PythonArgs
    & $script:PythonLauncher.Command @all
    if ($LASTEXITCODE -ne 0) { throw "python command failed: $($PythonArgs -join ' ')" }
}

$script:PythonLauncher = Find-Python
Write-Host "==> Using Python via $($script:PythonLauncher.Command) $($script:PythonLauncher.Args -join ' ')"

if (-not (Test-Path $VenvDir)) {
    Write-Host "==> Creating virtual environment at $VenvDir"
    Invoke-Python @("-m", "venv", $VenvDir)
}

$venvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "venv creation failed: $venvPython not found"
}

Write-Host "==> Upgrading pip"
& $venvPython -m pip install --upgrade pip

$requirements = if ($Dev) { "requirements-dev.txt" } else { "requirements.txt" }
Write-Host "==> Installing $requirements"
& $venvPython -m pip install -r (Join-Path $Root $requirements)

Write-Host ""
Write-Host "Done. Activate and run:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python meta_extract -f tests\fixtures\sample.txt --json"
if ($Dev) {
    Write-Host "  pytest -v"
}
