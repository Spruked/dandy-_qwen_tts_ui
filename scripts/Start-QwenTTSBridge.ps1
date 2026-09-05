$ErrorActionPreference = "Stop"

$PackageRoot = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $PackageRoot "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$Port = 8020
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

$env:DANDY_SHOW_ROOT = "C:\dev\Desktop\The Real Dandy\Phil_and_Jim_Dandy_Show"
$env:DANDY_QWEN_BRIDGE_HOST = "0.0.0.0"
$env:DANDY_QWEN_BRIDGE_PORT = "$Port"
$env:DANDY_QWEN_BACKENDS = "http://127.0.0.1:8031,http://127.0.0.1:8032,http://127.0.0.1:8033"
$env:DANDY_FFMPEG = "C:\dev\Desktop\The Real Dandy\Phil_and_Jim_Dandy_Show\staging\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe"
$env:DANDY_FFPROBE = "C:\dev\Desktop\The Real Dandy\Phil_and_Jim_Dandy_Show\staging\ffmpeg\ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe"

$Python = "R:\R_Drive_Substrate\Services\qwen_tts_312\Scripts\python.exe"
$OutLog = Join-Path $LogDir "qwen-bridge-$Port.out.log"
$ErrLog = Join-Path $LogDir "qwen-bridge-$Port.err.log"

$Process = Start-Process `
    -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "bridge:app", "--host", $env:DANDY_QWEN_BRIDGE_HOST, "--port", "$Port") `
    -WorkingDirectory $PackageRoot `
    -WindowStyle Hidden `
    -RedirectStandardOutput $OutLog `
    -RedirectStandardError $ErrLog `
    -PassThru

Write-Output "Started Qwen TTS bridge pid=$($Process.Id)"
Write-Output "Ready target: http://127.0.0.1:$Port"
