param(
  [ValidateSet('mapping-fastlio-static','mapping-fastlio-dynamic','mapping-fastlio-corridor','mapping-srrg-landmark-corridor','mapping-srrg-static','mapping-srrg-dynamic','mapping-srrg-large-change','mapping-srrg-corridor','mapping-static','mapping-dynamic','mapping-corridor','mapping-probe-static','mapping-probe-dynamic','mapping-probe-corridor','mapping-probe-height-corridor','localization-static','localization-dynamic','localization-large-change','localization-degradation','localization-ndt-static','localization-gicp-static','localization-ndt-dynamic','localization-gicp-dynamic')]
  [string]$Flow='mapping-static',
  [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
  [string]$PresentationRoot='F:\be2演讲',
  [double]$Duration=90,
  [switch]$Auto,
  [switch]$Record
)
$ErrorActionPreference='Stop'
$runId=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$Flow+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$runId)
New-Item -ItemType Directory -Path $run -Force | Out-Null
function Convert-ToWslPath([string]$path) {
  $absolute=[IO.Path]::GetFullPath($path)
  if ($absolute -notmatch '^[A-Za-z]:\\') {throw 'A local drive path is required'}
  return '/mnt/'+$absolute.Substring(0,1).ToLower()+'/'+$absolute.Substring(3).Replace('\','/')
}
$runWsl=Convert-ToWslPath $run
$repoWsl=Convert-ToWslPath $RepoRoot
$title='SLAM-LIVE-'+$Flow+'-'+$runId.Substring($runId.Length-6)
$autoText=if ($Auto) {'true'} else {'false'}
if ($Duration -le 0) {$Duration=86400}
$terminalArgs="-w new --pos 0,740 --size 200,13 new-tab --title $title --suppressApplicationTitle wsl.exe -d Ubuntu-24.04 -- bash $repoWsl/src/scripts/presentation/run_live.sh $Flow $runWsl $Duration $autoText"
Start-Process -FilePath (Get-Command wt.exe).Source -WindowStyle Hidden -ArgumentList $terminalArgs
$deadline=(Get-Date).AddMinutes(3)
while (-not (Test-Path -LiteralPath (Join-Path $run 'ready.json'))) {
  if (Test-Path -LiteralPath (Join-Path $run 'failed.json')) {throw ('Session failed: '+(Get-Content (Join-Path $run 'failed.json') -Raw))}
  if ((Get-Date) -gt $deadline) {throw ('Live data did not become ready. Inspect '+$run+'\logs')}
  Start-Sleep -Milliseconds 500
}
$video=Join-Path $run 'execution.mp4'
$recorder=$null
if ($Record) {
  $filter="gfxcapture=window_title=^Gazebo Sim.*:max_framerate=15:capture_border=1,hwdownload,format=bgra,scale=960:720:force_original_aspect_ratio=decrease,pad=960:720:(ow-iw)/2:(oh-ih)/2[gz];gfxcapture=window_title=^SLAM LIVE - RViz2.*:max_framerate=15:capture_border=1,hwdownload,format=bgra,scale=960:720:force_original_aspect_ratio=decrease,pad=960:720:(ow-iw)/2:(oh-ih)/2[rv];[gz][rv]hstack=inputs=2,format=yuv420p[out]"
  $filterPath=Join-Path $run 'capture-filter.txt'
  [IO.File]::WriteAllText($filterPath,$filter,[Text.UTF8Encoding]::new($false))
  $argsText='-hide_banner -loglevel warning -filter_complex_threads 1 -filter_complex "'+$filter+'" -map "[out]" -r 15 -fps_mode cfr -c:v libx264 -threads 2 -preset veryfast -crf 21 -progress "'+$run+'\capture-progress.txt" -y "'+$video+'"'
  $info=[Diagnostics.ProcessStartInfo]::new()
  $info.FileName=(Get-Command ffmpeg.exe).Source
  $info.Arguments=$argsText
  $info.UseShellExecute=$false
  $info.CreateNoWindow=$true
  $info.RedirectStandardInput=$true
  $info.RedirectStandardError=$true
  for($attempt=0;$attempt -lt 10;$attempt++){
    $recorder=[Diagnostics.Process]::new()
    $recorder.StartInfo=$info
    $null=$recorder.Start()
    $stderr=$recorder.StandardError.ReadToEndAsync()
    Start-Sleep -Seconds 2
    if(-not $recorder.HasExited){break}
    if($stderr.Result -notmatch 'Failed to find capture source'){break}
    if($attempt -eq 9){break}
    # WSLg may expose the Windows title after the ROS data-ready marker.
    $recorder.Dispose()
  }
  if ($recorder.HasExited) {
    [IO.File]::WriteAllText((Join-Path $run 'STOP'),'Capture preflight failed')
    throw ('Real-window recording failed: '+$stderr.Result)
  }
  $captureDeadline=(Get-Date).AddSeconds(30)
  while(-not ((Test-Path -LiteralPath "$run/capture-progress.txt") -and (Select-String -LiteralPath "$run/capture-progress.txt" -Pattern '^frame=[1-9][0-9]*$' -Quiet))){
    if($recorder.HasExited -or (Get-Date)-gt $captureDeadline){
      [IO.File]::WriteAllText((Join-Path $run 'STOP'),'Native capture produced no frames; experiment not started')
      if(-not $recorder.HasExited){$recorder.Kill();$recorder.WaitForExit()}
      [IO.File]::WriteAllText((Join-Path $run 'capture.log'),$stderr.Result)
      throw "Native capture produced no frames: $run"
    }
    Start-Sleep -Milliseconds 250
  }
  [IO.File]::WriteAllText((Join-Path $run 'recording.capture'),'Native window capture')
}
[IO.File]::WriteAllText((Join-Path $run 'recording.started'),(Get-Date -Format o))
Write-Host ('LIVE SESSION: '+$run)
Write-Host 'Gazebo and RViz are real application windows. Use keyboard in the SLAM-LIVE console; q finishes.'
try {
  while (-not (Test-Path -LiteralPath (Join-Path $run 'finished.json'))) {
    if (Test-Path -LiteralPath (Join-Path $run 'failed.json')) {throw ('Session failed: '+(Get-Content (Join-Path $run 'failed.json') -Raw))}
    if ($recorder -and $recorder.HasExited) {throw ('Capture stopped unexpectedly: '+$stderr.Result)}
    Start-Sleep -Milliseconds 500
  }
} finally {
  if ($recorder -and -not $recorder.HasExited) {
    $recorder.StandardInput.WriteLine('q')
    $recorder.StandardInput.Flush()
    $recorder.StandardInput.Close()
    $null=$recorder.WaitForExit(30000)
    if (-not $recorder.HasExited) {$recorder.Kill()}
  }
  if ($recorder) {[IO.File]::WriteAllText((Join-Path $run 'capture.log'),$stderr.Result)}
  [IO.File]::WriteAllText((Join-Path $run 'recording.stopped'),(Get-Date -Format o))
}
if ($Record) {
  if ($recorder.ExitCode -ne 0) {throw ('Recorder exit code '+$recorder.ExitCode)}
  $mediaDir=Join-Path $PresentationRoot '屏幕实录\20261014-native-ui'
  New-Item -ItemType Directory -Path $mediaDir -Force | Out-Null
  $labels=@{
    'mapping-static'='S1-纯静态__A-建图__slam_toolbox与3D点云'
    'mapping-dynamic'='S2-运动障碍物__A-建图__slam_toolbox与3D点云'
    'mapping-corridor'='S4-走廊退化__A-建图__slam_toolbox与3D点云'
    'localization-static'='S1-纯静态__B-定位__AMCL_Raw-DUFOMap-BeautyMap'
    'localization-dynamic'='S2-运动障碍物__B-定位__AMCL_Raw-DUFOMap-BeautyMap_动静地图六组'
    'localization-large-change'='S3-持久变化__B-定位__AMCL_Raw-DUFOMap-BeautyMap_旧地图'
    'localization-degradation'='S4-走廊退化__B-定位__AMCL_Raw-DUFOMap-BeautyMap_完整与恢复六组'
    'localization-ndt-static'='S1-纯静态__B-三维定位__NDT_OMP_Raw3D地图'
    'localization-gicp-static'='S1-纯静态__B-三维定位__GICP_Raw3D地图'
    'localization-ndt-dynamic'='S2-运动障碍物__B-三维定位__NDT_OMP_Raw3D地图'
    'localization-gicp-dynamic'='S2-运动障碍物__B-三维定位__GICP_Raw3D地图'
  }
  $mirrorName=$labels[$Flow]+'__'+$runId.Substring(0,15)+'-'+$runId.Substring($runId.Length-6)+'.mp4'
  if($Flow -like 'mapping-probe-*'){$mirrorName=$Flow+'__2D-3D-depth_A__'+$runId.Substring(0,15)+'-'+$runId.Substring($runId.Length-6)+'.mp4'}
  if($Flow -like 'mapping-srrg-*'){$mirrorName=$Flow+'__2D_作者在线建图__'+$runId.Substring(0,15)+'-'+$runId.Substring($runId.Length-6)+'.mp4'}
  Copy-Item -LiteralPath $video -Destination (Join-Path $mediaDir $mirrorName)
  [IO.File]::WriteAllText((Join-Path $run 'mirror.json'),(@{run_id=$runId;flow=$Flow;file=(Join-Path $mediaDir $mirrorName);scope='Native capture; metrics require a completed and verified session'}|ConvertTo-Json))
  & ffprobe.exe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames,r_frame_rate -of json $video | Set-Content -LiteralPath (Join-Path $run 'video-probe.json') -Encoding utf8
}
[IO.File]::WriteAllText((Join-Path $RepoRoot ('.cache\presentation\'+$Flow+'-latest.json')),(@{path=$run;flow=$Flow;run_id=$runId}|ConvertTo-Json))
Write-Host ('COMPLETE: '+$run)
