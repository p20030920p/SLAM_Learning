param(
    [ValidateSet('camera','lidar')][string]$Sensor = 'camera',
    [ValidateSet('sensor','stereo','rgbd','rgbd-slam','icp','kiss')][string]$Algorithm = 'sensor',
    [ValidateSet('preview','stationary','motion')][string]$SessionType = 'preview',
    [ValidateSet('default','on','off')][string]$Emitter = 'default',
    [ValidateRange(0,86400)][int]$Seconds = 0,
    [ValidateRange(1,30)][int]$FPS = 10,
    [ValidateRange(1,200)][int]$Lines = 50,
    [switch]$Record, [switch]$NoGui, [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
if (($Sensor -eq 'camera' -and $Algorithm -in @('icp','kiss')) -or
    ($Sensor -eq 'lidar' -and $Algorithm -in @('stereo','rgbd','rgbd-slam'))) {
    throw 'Select camera: sensor/stereo/rgbd/rgbd-slam; lidar: sensor/icp/kiss.'
}
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw "Missing environment: $taskPython" }
$taskLinuxRoot = (& wsl.exe -d Ubuntu-22.04 -- wslpath -u $taskRoot.Replace('\','/') | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $taskLinuxRoot.StartsWith('/') -or $taskLinuxRoot.Contains("'")) {
    throw 'Cannot resolve the workspace in Ubuntu-22.04, or its path contains an apostrophe.'
}
$taskCache = Join-Path $taskRoot '.cache'
[void][System.IO.Directory]::CreateDirectory($taskCache)
$taskCheckName = 'live-check-' + [guid]::NewGuid().ToString('N') + '.sh'
$taskCheckPath = Join-Path $taskCache $taskCheckName
$taskCheck = @"
set -e
source /opt/ros/humble/setup.bash
cd '$taskLinuxRoot'
python3 -c 'import rclpy,cv2,numpy,scipy; from rtabmap_msgs.msg import OdomInfo; print(""ROS_BRIDGE_READY"")'
ros2 pkg prefix rtabmap_odom
ros2 pkg prefix rtabmap_slam
command -v rviz2
"@
# A file avoids PowerShell 5.1 multiline/native-argument quoting differences.
$taskCheck = $taskCheck.Replace('""ROS_BRIDGE_READY""','"ROS_BRIDGE_READY"')
if ($Algorithm -eq 'kiss') {
    $taskCheck += "`n.cache/kiss-venv/bin/python -c 'import kiss_icp; print(1)'`n"
}
[System.IO.File]::WriteAllText($taskCheckPath,$taskCheck.Replace("`r`n","`n"),[System.Text.UTF8Encoding]::new($false))
try {
    & wsl.exe -d Ubuntu-22.04 -- bash "$taskLinuxRoot/.cache/$taskCheckName"
    $taskExit = $LASTEXITCODE
} finally { Remove-Item -LiteralPath $taskCheckPath -ErrorAction SilentlyContinue }
if ($taskExit -ne 0) { throw 'WSL ROS dependencies are not ready; sensor was not opened.' }
& $taskPython -c "import numpy,pyrealsense2,serial; print('WINDOWS_SENSOR_READY')"
if ($LASTEXITCODE -ne 0) { throw 'Windows sensor dependencies are not ready.' }
if ($CheckOnly) { Write-Output 'Environment check passed. Sensors were not opened.'; return }
$taskPort = $null
if ($Sensor -eq 'lidar') {
    $taskDevice = @(Get-PnpDevice -PresentOnly -Class Ports | Where-Object { $_.InstanceId -like 'USB\VID_1A86&PID_55D3*' })
    if ($taskDevice.Count -ne 1) { throw 'Expected one physical CH343 USB serial adapter.' }
    $taskCom = [regex]::Match($taskDevice[0].FriendlyName,'COM\d+').Value
    $taskMap = Get-ItemProperty -LiteralPath 'HKLM:\HARDWARE\DEVICEMAP\SERIALCOMM'
    $taskNt = @($taskMap.PSObject.Properties | Where-Object { $_.Name -match '^\\Device\\Serial\d+$' -and $_.Value -eq $taskCom })
    if ($taskNt.Count -ne 1) { throw 'Physical serial path is ambiguous; inspect SERIALCOMM.' }
    $taskPort = '\\?\GLOBALROOT' + $taskNt[0].Name
}
$taskName = 'live-' + $Sensor + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$taskOutput = Join-Path $taskRoot "data\$taskName"
[void][System.IO.Directory]::CreateDirectory($taskOutput)
$taskLinuxSession = "$taskLinuxRoot/data/$taskName"
$taskConfig = @{
    sensor=$Sensor; algorithm=$Algorithm; session_type=$SessionType; seconds=$Seconds
    fps=$FPS; lines=$Lines; emitter=$Emitter; record=[bool]$Record; no_gui=[bool]$NoGui
    serial_port=$taskPort; port=17635; domain=83
    windows_session=$taskOutput; linux_session=$taskLinuxSession
    token=[guid]::NewGuid().ToString('N')
}
if ($Sensor -eq 'lidar') { $taskConfig.port=17636; $taskConfig.domain=84 }
$taskConfigPath = Join-Path $taskOutput 'config.json'
[System.IO.File]::WriteAllText($taskConfigPath,($taskConfig | ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
$taskHashes = @{}
foreach ($taskSource in @('start_live.ps1','live_windows.py','live_ros.py','live_transport.py','live_metrics.py','live_kiss_worker.py','protocol_l2.py')) {
    $taskHashes["scripts/$taskSource"] = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $taskSource) -Algorithm SHA256).Hash.ToLowerInvariant()
}
foreach ($taskView in Get-ChildItem -LiteralPath (Join-Path $taskRoot 'configs\rviz') -Filter '*.rviz') {
    $taskHashes["configs/rviz/$($taskView.Name)"] = (Get-FileHash -LiteralPath $taskView.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
}
[System.IO.File]::WriteAllText((Join-Path $taskOutput 'code-hashes.json'),($taskHashes | ConvertTo-Json),[System.Text.UTF8Encoding]::new($false))
$taskScript = @"
set -e
source /opt/ros/humble/setup.bash
cd '$taskLinuxRoot'
exec python3 -u scripts/live_ros.py '$taskLinuxSession/config.json'
"@
[System.IO.File]::WriteAllText((Join-Path $taskOutput 'run-live.sh'),$taskScript.Replace("`r`n","`n"),[System.Text.UTF8Encoding]::new($false))
$taskHelper = $null
try {
    $taskHelper = Start-Process -FilePath 'wsl.exe' -ArgumentList @('-d','Ubuntu-22.04','--','bash',"$taskLinuxSession/run-live.sh") -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $taskOutput 'bridge.stdout.log') -RedirectStandardError (Join-Path $taskOutput 'bridge.stderr.log')
    Write-Output "LIVE $Sensor / $Algorithm. Ctrl+C to stop; close this session before changing algorithms."
    Write-Output "Session: $taskOutput"
    & $taskPython (Join-Path $PSScriptRoot 'live_windows.py') $taskConfigPath
    $taskCaptureExit = $LASTEXITCODE
    if (-not $taskHelper.WaitForExit(20000)) { throw 'Bridge shutdown timed out; inspect session logs.' }
    if ($taskCaptureExit -ne 0) { throw "Capture failed; inspect $taskOutput\live-capture.json" }
    $taskResult = Get-Content -LiteralPath (Join-Path $taskOutput 'live-result.json') -Raw | ConvertFrom-Json
    if ($taskResult.status -eq 'failed') { throw "Bridge failed; inspect $taskOutput\live-result.json and bridge.stderr.log" }
    Write-Output "ROS observations=$($taskResult.source_observations), poses=$($taskResult.odometry_messages), lost fraction=$($taskResult.lost_status_fraction)"
    Write-Output 'This receipt is not a precision acceptance. Use the declared stationary/motion protocol in docs/TEST_PLAN.zh-CN.md.'
} finally {
    if ($taskHelper -and -not $taskHelper.HasExited) {
        # Only the helper we launched; never stop another WSL/ROS session.
        if (-not $taskHelper.WaitForExit(12000)) { Stop-Process -Id $taskHelper.Id -ErrorAction SilentlyContinue }
    }
    Write-Output "Saved session: $taskOutput"
}
