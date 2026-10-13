@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0entry.ps1" -Action reproduce
if errorlevel 1 pause
