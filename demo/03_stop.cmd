@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0entry.ps1" -Action stop
if errorlevel 1 pause
