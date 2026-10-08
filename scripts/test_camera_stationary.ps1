param([int]$Seconds = 20, [switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
if ($Seconds -lt 10) { throw 'Use at least 10 seconds for this stationary camera test.' }
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw "Python environment missing: $taskPython" }
$taskWindowsRoot = $taskRoot.Replace('\','/')
$taskLinuxRoot = (& wsl.exe -d Ubuntu-22.04 -- wslpath -u $taskWindowsRoot | Out-String).Trim()
if ($LASTEXITCODE -ne 0 -or -not $taskLinuxRoot.StartsWith('/')) { throw 'Could not resolve the workspace in Ubuntu-22.04.' }
if ($taskLinuxRoot.Contains("'")) { throw 'This launcher requires a workspace path without apostrophes.' }
$taskReady = @'
set -e
source /opt/ros/humble/setup.bash
ros2 pkg prefix rtabmap_odom
python3 -c 'import rclpy,cv2,numpy; print("CAMERA_ALGORITHM_READY")'
command -v ffmpeg
'@
$taskCache = Join-Path $taskRoot '.cache'
[void][System.IO.Directory]::CreateDirectory($taskCache)
$taskCheckName = 'camera-check-' + [guid]::NewGuid().ToString('N') + '.sh'
$taskCheckPath = Join-Path $taskCache $taskCheckName
[System.IO.File]::WriteAllText($taskCheckPath,$taskReady.Replace("`r`n","`n"),[System.Text.UTF8Encoding]::new($false))
try {
    & wsl.exe -d Ubuntu-22.04 -- bash "$taskLinuxRoot/.cache/$taskCheckName"
    $taskReadyExit = $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $taskCheckPath -ErrorAction SilentlyContinue
}
if ($taskReadyExit -ne 0) { throw 'WSL algorithm environment is not ready; camera was not started.' }
if ($CheckOnly) { Write-Output 'Environment check passed. Camera was not started.'; return }
$taskName = 'camera-stationary-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$taskRelative = 'data/' + $taskName
$taskOutput = Join-Path $taskRoot "data\$taskName"
Write-Output "Place the camera on a stable support before continuing. Keep it still for the entire $Seconds-second capture."
Write-Output 'Face textured boxes/furniture; avoid the bright screen. Starting in 5 seconds.'
Start-Sleep -Seconds 5
& $taskPython (Join-Path $PSScriptRoot 'capture_camera.py') --seconds $Seconds --record-raw --output $taskOutput
if ($LASTEXITCODE -ne 0) { throw "Camera capture failed; inspect $taskOutput\capture.json" }
$taskNote = @{session_type='stationary';fixed_sensor_declared_by_operator=$true;requested_seconds=$Seconds;scope='Exploratory stationary stereo odometry; no new moving accuracy or independent range reference.'} | ConvertTo-Json
[System.IO.File]::WriteAllText((Join-Path $taskOutput 'session-note.json'),$taskNote,[System.Text.UTF8Encoding]::new($false))
& $taskPython (Join-Path $PSScriptRoot 'verify_camera_recording.py') (Join-Path $taskOutput 'raw.db3')
if ($LASTEXITCODE -ne 0) { throw 'Raw recording audit failed. Keep this session and inspect playback-v2.json.' }
& $taskPython (Join-Path $PSScriptRoot 'export_stereo.py') (Join-Path $taskOutput 'raw.db3') --output (Join-Path $taskOutput 'stereo')
if ($LASTEXITCODE -ne 0) { throw 'Stereo export failed. Inspect stereo/stereo.json.' }
$taskReplay = @"
set -e
source /opt/ros/humble/setup.bash
cd '$taskLinuxRoot'
python3 scripts/run_odometry_baseline.py '$taskRelative/stereo' --session-type stationary --output '$taskRelative/odometry'
python3 scripts/render_odometry_video.py '$taskRelative/stereo' '$taskRelative/odometry'
"@
$taskReplayPath = Join-Path $taskOutput 'run-algorithm.sh'
[System.IO.File]::WriteAllText($taskReplayPath,$taskReplay.Replace("`r`n","`n"),[System.Text.UTF8Encoding]::new($false))
& wsl.exe -d Ubuntu-22.04 -- bash "$taskLinuxRoot/$taskRelative/run-algorithm.sh"
if ($LASTEXITCODE -ne 0) { throw "Algorithm or rendering failed; inspect $taskOutput\odometry" }
$taskResult = Get-Content -LiteralPath (Join-Path $taskOutput 'odometry\result.json') -Raw | ConvertFrom-Json
Write-Output "Status/pose coverage: $($taskResult.observed_output_fraction); lost fraction: $($taskResult.lost_status_fraction)"
Write-Output "Max stationary displacement (m): $($taskResult.static_translation_max_m); rotation (degrees): $($taskResult.static_rotation_max_deg)"
Write-Output "Exploratory static target passed: $($taskResult.static_gate_passed). This is not moving accuracy or RGB-D mapping."
Write-Output "Saved session: $taskOutput"
Invoke-Item -LiteralPath (Join-Path $taskOutput 'odometry\preview.mp4')
