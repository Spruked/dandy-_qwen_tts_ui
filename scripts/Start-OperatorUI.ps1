param(
    [switch]$Restart
)

$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $PackageRoot "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$Port = 7861
$Existing = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($Existing -and -not $Restart) {
    Write-Output "Operator UI already running at http://127.0.0.1:$Port"
    exit 0
}
if ($Existing -and $Restart) {
    $Existing | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 1
}

$env:DANDY_QWEN_UI_HOST = "127.0.0.1"
$env:DANDY_QWEN_UI_PORT = "$Port"
$env:DANDY_QWEN_BACKENDS = "http://127.0.0.1:8031,http://127.0.0.1:8032,http://127.0.0.1:8033"

$Python = if ($env:DANDY_QWEN_PYTHON) {
    $env:DANDY_QWEN_PYTHON
} else {
    "R:\Services\qwen_tts_312\Scripts\python.exe"
}
if (-not (Test-Path $Python)) {
    throw "Python runtime not found: $Python. Set DANDY_QWEN_PYTHON to the Python that has gradio and gradio_client installed."
}

$OutLog = Join-Path $LogDir "operator-ui-$Port.out.log"
$ErrLog = Join-Path $LogDir "operator-ui-$Port.err.log"

$Process = Start-Process `
    -FilePath $Python `
    -ArgumentList @("app.py") `
    -WorkingDirectory $PackageRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -PassThru

Write-Output "Started operator UI pid=$($Process.Id)"

for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 1
    $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($listener) {
        Write-Output "Ready: http://127.0.0.1:$Port"
        exit 0
    }
    if ($Process.HasExited) {
        Write-Output "Operator UI process exited before port $Port became ready."
        if (Test-Path $ErrLog) { Get-Content $ErrLog -Tail 40 | Out-Host }
        exit 1
    }
}

Write-Output "Operator UI not ready yet. Check: $ErrLog"
exit 1
