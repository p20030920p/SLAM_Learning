param([int]$Seconds = 60, [string]$Session = 'static')
$ErrorActionPreference = 'Stop'
if ($Seconds -le 0 -or $Session -notmatch '^[a-zA-Z0-9_-]+$') { throw 'Use positive seconds and an ASCII session label.' }
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$taskOutput = Join-Path $taskRoot "data\$Session-$taskStamp"
# Find the CH343 hardware port, then bypass a colliding virtual DOS COM name.
$taskDevice = @(Get-PnpDevice -PresentOnly -Class Ports | Where-Object { $_.InstanceId -like 'USB\VID_1A86&PID_55D3*' })
if ($taskDevice.Count -ne 1) { throw 'Expected one physical CH343 adapter. Inspect Get-PnpDevice -PresentOnly -Class Ports.' }
$taskCom = [regex]::Match($taskDevice[0].FriendlyName, 'COM\d+').Value
$taskMap = Get-ItemProperty -LiteralPath 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM'
$taskNt = @($taskMap.PSObject.Properties | Where-Object { $_.Name -match '^\\Device\\Serial\d+$' -and $_.Value -eq $taskCom })
if ($taskNt.Count -ne 1) { throw 'Physical serial path is ambiguous. Inspect SERIALCOMM mapping.' }
$taskPort = '\\?\GLOBALROOT' + $taskNt[0].Name
$taskJobs = @()
try {
    $taskJobs += Start-Job -ScriptBlock { param($p,$root,$out,$n) Set-Location -LiteralPath $root; & $p scripts\capture_camera.py --seconds $n --record-raw --output $out; if ($LASTEXITCODE) { throw "Camera exit $LASTEXITCODE" } } -ArgumentList $taskPython,$taskRoot,(Join-Path $taskOutput 'camera'),$Seconds
    $taskJobs += Start-Job -ScriptBlock { param($p,$root,$out,$n,$port) Set-Location -LiteralPath $root; & $p scripts\capture_l2.py --seconds $n --query-version --output $out --port $port; if ($LASTEXITCODE) { throw "L2 exit $LASTEXITCODE" } } -ArgumentList $taskPython,$taskRoot,(Join-Path $taskOutput 'l2'),$Seconds,$taskPort
    $taskJobs | Wait-Job | Receive-Job
    if (@($taskJobs | Where-Object State -ne 'Completed').Count) { throw 'A capture job failed. Inspect capture.json.' }
    & $taskPython (Join-Path $PSScriptRoot 'audit_l2.py') (Join-Path $taskOutput 'l2')
    Write-Output "Saved $taskOutput. Simultaneous capture is not clock synchronization."
} finally {
    $taskJobs | Stop-Job -ErrorAction SilentlyContinue
    $taskJobs | Remove-Job -Force -ErrorAction SilentlyContinue
}
