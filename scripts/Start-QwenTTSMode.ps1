param(
    [ValidateSet("custom", "clone", "design")]
    [string]$Mode = "custom",
    [switch]$NoStopExisting
)

$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $PackageRoot "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$QwenVenv = if ($env:DANDY_QWEN_VENV) { $env:DANDY_QWEN_VENV } else { "R:\Services\qwen_tts_312" }
$QwenEngine = if ($env:DANDY_QWEN_ENGINE) { $env:DANDY_QWEN_ENGINE } else { "R:\Services\qwen_engine" }
$Python = if ($env:DANDY_QWEN_PYTHON) { $env:DANDY_QWEN_PYTHON } else { Join-Path $QwenVenv "Scripts\python.exe" }

$SoxDir = "C:\Users\bryan\AppData\Local\Microsoft\WinGet\Packages\ChrisBagwell.SoX_Microsoft.Winget.Source_8wekyb3d8bbwe\sox-14.4.2"
if (Test-Path $SoxDir) {
    $env:PATH = "$SoxDir;$env:PATH"
}

$Modes = @{
    custom = @{
        Port = 8031
        Checkpoint = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
        Description = "Built-in Qwen speakers with instruction control."
    }
    clone = @{
        Port = 8032
        Checkpoint = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        Description = "Voice clone plus save/load reusable voice prompts."
    }
    design = @{
        Port = 8033
        Checkpoint = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        Description = "Natural-language voice design."
    }
}

$Selected = $Modes[$Mode]
$Port = [int]$Selected.Port
$Checkpoint = [string]$Selected.Checkpoint

if (-not (Test-Path $Python)) {
    throw "Python runtime not found: $Python"
}
if (-not (Test-Path $QwenEngine)) {
    throw "Qwen engine not found: $QwenEngine"
}

$Existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($Existing) {
    Write-Output "Qwen TTS mode=$Mode already listening on port $Port"
    Write-Output "Ready: http://127.0.0.1:$Port"
    exit 0
}

if (-not $NoStopExisting) {
    & (Join-Path $PSScriptRoot "Stop-QwenTTSModels.ps1") | Out-Host
}

$OutLog = Join-Path $LogDir "qwen-$Mode-$Port.out.log"
$ErrLog = Join-Path $LogDir "qwen-$Mode-$Port.err.log"

$Args = @(
    "-m", "qwen_tts.cli.demo",
    $Checkpoint,
    "--ip", "127.0.0.1",
    "--port", "$Port",
    "--device", "cuda:0",
    "--dtype", "float16",
    "--flash-attn",
    "--concurrency", "1",
    "--no-share"
)

$Process = Start-Process `
    -FilePath $Python `
    -ArgumentList $Args `
    -WorkingDirectory $QwenEngine `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -PassThru

Write-Output "Started Qwen TTS mode=$Mode pid=$($Process.Id) port=$Port"
Write-Output "Checkpoint=$Checkpoint"
Write-Output "Description=$($Selected.Description)"
Write-Output "Logs:"
Write-Output "  $OutLog"
Write-Output "  $ErrLog"

for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep -Seconds 2
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Output "Ready: http://127.0.0.1:$Port"
        exit 0
    }
    if ($Process.HasExited) {
        Write-Output "Qwen process exited before port $Port became ready."
        if (Test-Path $ErrLog) { Get-Content $ErrLog -Tail 40 | Out-Host }
        exit 1
    }
}

Write-Output "Not ready yet after wait. Check logs:"
Write-Output "  $ErrLog"
exit 1
