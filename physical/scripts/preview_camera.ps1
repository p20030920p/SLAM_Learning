param([int]$Seconds = 5)
$ErrorActionPreference = 'Stop'
if ($Seconds -lt 3) { throw 'Use at least 3 seconds to produce a preview image.' }
$taskRoot = Split-Path $PSScriptRoot -Parent
$taskPython = Join-Path $taskRoot '.venv\Scripts\python.exe'
$taskCapture = Join-Path $PSScriptRoot 'capture_camera.py'
if (-not (Test-Path -LiteralPath $taskPython)) {
    throw "Camera Python environment missing: $taskPython"
}
$taskStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$taskOutput = Join-Path $taskRoot "data\camera-view-$taskStamp"
Write-Output "Keep the camera steady, facing a textured scene 1-3 m away. Capturing $Seconds seconds."
& $taskPython $taskCapture --seconds $Seconds --output $taskOutput
if ($LASTEXITCODE -ne 0) {
    throw "Camera capture failed. Inspect capture.json in $taskOutput."
}
$taskImage = Join-Path $taskOutput 'preview.png'
if (-not (Test-Path -LiteralPath $taskImage)) {
    throw "Preview image missing: $taskImage"
}
Write-Output "Saved preview: $taskImage"
Write-Output 'This is raw camera data; no SLAM is running.'
Invoke-Item -LiteralPath $taskImage
