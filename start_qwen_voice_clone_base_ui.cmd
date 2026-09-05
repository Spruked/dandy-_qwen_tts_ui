@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-QwenTTSMode.ps1" -Mode clone
if errorlevel 1 pause
