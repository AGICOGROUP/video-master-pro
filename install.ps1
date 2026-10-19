# video-master-pro - one-shot setup
# Usage:
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File install.ps1 -CheckOnly
#   ... -Src "D:\footage" -Work "D:\work" -Out "D:\out"
#
# Pulls the latest skill when this folder is a git checkout, then runs the
# first-run gate: installs missing Python packages, then checks ffmpeg and fonts.
# ASCII only on purpose - Windows PowerShell 5.1 misreads UTF-8 without BOM.

param(
    [switch]$CheckOnly,
    [string]$Src = "",
    [string]$Work = "",
    [string]$Out = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (Test-Path (Join-Path $Root ".git")) {
    Write-Host "[setup] updating from origin ..."
    try { git pull --ff-only 2>&1 | Out-Host } catch { Write-Host "[setup] git pull skipped" }
}

$FirstRun = Join-Path $Root "video-master-pro\scripts\firstrun.py"
if (-not (Test-Path $FirstRun)) {
    Write-Host "[setup] FAIL: video-master-pro\scripts\firstrun.py not found"
    Write-Host "        clone the whole repository, do not copy a single folder"
    exit 2
}

$Py = Get-Command python -ErrorAction SilentlyContinue
if (-not $Py) { $Py = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $Py) {
    Write-Host "[setup] FAIL: python not on PATH"
    Write-Host "        install Python 3.10+ from python.org and tick 'Add python.exe to PATH'"
    exit 2
}

$PyArgs = @($FirstRun)
if ($CheckOnly) { $PyArgs += "--check" }
if ($Src)  { $PyArgs += @("--src", $Src) }
if ($Work) { $PyArgs += @("--work", $Work) }
if ($Out)  { $PyArgs += @("--out", $Out) }

& $Py.Source @PyArgs
$code = $LASTEXITCODE

Write-Host ""
if ($code -eq 0) {
    Write-Host "[setup] READY - environment is ready, start making films"
} else {
    Write-Host "[setup] NOT READY - fix the FAIL lines above, then run this script again"
}
exit $code
