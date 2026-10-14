@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0entry.ps1" -Action benchmark
if errorlevel 1 pause
