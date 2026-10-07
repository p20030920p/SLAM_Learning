[CmdletBinding()]
param([switch]$EnablePlatform, [switch]$InstallUbuntu)
$ErrorActionPreference = 'Stop'
$taskElevated = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($EnablePlatform -and $InstallUbuntu) { throw 'Run the platform and Ubuntu steps separately, with a reboot between them if required.' }
if ($EnablePlatform) {
    if (-not $taskElevated) { throw 'EnablePlatform requires an administrator PowerShell. This script does not elevate or restart Windows.' }
    & dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    if ($LASTEXITCODE -notin @(0, 3010)) { throw "Feature activation failed: $LASTEXITCODE" }
    Write-Output 'Platform feature requested. Restart Windows yourself if required, then install Ubuntu.'
} elseif ($InstallUbuntu) {
    & wsl.exe --install -d Ubuntu-22.04 --no-launch
    if ($LASTEXITCODE -ne 0) { throw "Ubuntu installation failed: $LASTEXITCODE" }
    Write-Output 'Launch wsl -d Ubuntu-22.04 interactively to create your Linux account.'
} else {
    & wsl.exe --version
    & wsl.exe --list --verbose
    & wsl.exe --status
    [pscustomobject]@{Elevated=$taskElevated; HypervisorPresent=(Get-CimInstance Win32_ComputerSystem).HypervisorPresent} | Format-List
    Write-Output 'Read-only check. See docs/WSL.zh-CN.md for the next step.'
}
