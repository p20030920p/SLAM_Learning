@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0entry.ps1" -Action dynamic_keyboard
if errorlevel 1 pause
