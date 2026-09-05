param(
    [ValidateSet("custom", "clone", "design")]
    [string]$Mode = "custom",
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $PSScriptRoot
$ModeScript = Join-Path $PSScriptRoot "Start-QwenTTSMode.ps1"
$UiScript = Join-Path $PSScriptRoot "Start-OperatorUI.ps1"

Write-Host "Dandy Qwen TTS" -ForegroundColor Cyan
Write-Host "Starting backend mode: $Mode"

& $ModeScript -Mode $Mode
if ($LASTEXITCODE -ne 0) {
    throw "Qwen backend failed to start."
}

& $UiScript
if ($LASTEXITCODE -ne 0) {
    throw "Dandy operator UI failed to start."
}

$UiUrl = "http://127.0.0.1:7861"
Write-Host ""
Write-Host "Dandy Qwen TTS is ready:" -ForegroundColor Green
Write-Host "  Operator UI: $UiUrl"
Write-Host "  CustomVoice: http://127.0.0.1:8031"
Write-Host "  VoiceClone:  http://127.0.0.1:8032"
Write-Host "  VoiceDesign: http://127.0.0.1:8033"

if (-not $NoBrowser) {
    Start-Process $UiUrl
}
