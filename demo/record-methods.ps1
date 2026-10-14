param(
 [ValidateSet('static','dynamic','large-change','degradation')][string]$Scene='static',
 [ValidateSet('2D','3D')][string]$Dimension='2D',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲',
 [double]$Duration=90,
 [switch]$Keyboard
)
$ErrorActionPreference='Stop'
$flow='localization-'+$Scene
if($Dimension -eq '3D'){$flow='localization-3d-'+$Scene}
$id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-'+$flow+'-method-live-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$id)
New-Item -ItemType Directory -Path (Join-Path $run 'executions') -Force | Out-Null
$rw='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
$rootw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
$title='SLAM-LIVE-METHODS-'+$Scene+'-'+$id.Substring($id.Length-6)
$automatic=if($Keyboard){'false'}else{'true'}
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList "-w new --pos 0,740 --size 200,13 new-tab --title $title --suppressApplicationTitle wsl.exe -d Ubuntu-24.04 -- bash $rootw/src/scripts/presentation/run_live.sh $flow $rw $Duration $automatic true"
$deadline=(Get-Date).AddMinutes(4)
while(-not (Test-Path "$run/ready.json") -or -not (Test-Path "$run/views-ready.json")){
 if(Test-Path "$run/failed.json"){throw "Startup failed: $run"}
 if((Get-Date)-gt $deadline){[IO.File]::WriteAllText("$run/STOP",'Views did not become ready');throw "Three live RViz views not ready: $run"}
 Start-Sleep -Milliseconds 500
}
$views=Get-Content "$run/views.json" -Raw | ConvertFrom-Json
$captures=@()
try{
 foreach($item in $views.PSObject.Properties){
  $case=$item.Name; $viewTitle=$item.Value.title
  $filter="gfxcapture=window_title=^Gazebo Sim.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=960:720:force_original_aspect_ratio=decrease,pad=960:720:(ow-iw)/2:(oh-ih)/2[gz];gfxcapture=window_title=^$viewTitle.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=960:720:force_original_aspect_ratio=decrease,pad=960:720:(ow-iw)/2:(oh-ih)/2[rv];[gz][rv]hstack=inputs=2[gui];gfxcapture=window_title=^$title.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=1920:360:force_original_aspect_ratio=decrease,pad=1920:360:(ow-iw)/2:(oh-ih)/2[cli];[gui][cli]vstack=inputs=2,format=yuv420p[out]"
  [IO.File]::WriteAllText("$run/executions/$case-filter.txt",$filter)
  $info=[Diagnostics.ProcessStartInfo]::new()
  $info.FileName=(Get-Command ffmpeg.exe).Source
  $info.Arguments='-hide_banner -loglevel warning -filter_complex_threads 4 -filter_complex "'+$filter+'" -map "[out]" -r 12 -fps_mode cfr -c:v libx264 -threads 2 -preset veryfast -crf 22 -y "'+$run+'\executions\'+$case+'.mp4"'
  $info.UseShellExecute=$false;$info.CreateNoWindow=$true
  $info.RedirectStandardInput=$true;$info.RedirectStandardError=$true
  $proc=[Diagnostics.Process]::new();$proc.StartInfo=$info;$null=$proc.Start()
  $stderr=$proc.StandardError.ReadToEndAsync()
  $captures+=@{case=$case;process=$proc;stderr=$stderr;title=$viewTitle;map_topic=$item.Value.map_topic;pose_topic=$item.Value.pose_topic;tf_topic=$item.Value.tf_topic}
 }
 Start-Sleep -Seconds 4
 foreach($c in $captures){if($c.process.HasExited){throw ($c.case+': '+$c.stderr.Result)}}
 [IO.File]::WriteAllText("$run/recording.capture",'Native window capture')
 [IO.File]::WriteAllText("$run/recording.started",(Get-Date -Format o))
 while(-not (Test-Path "$run/finished.json")){
  if(Test-Path "$run/failed.json"){throw "Live run failed: $run"}
  foreach($c in $captures){if($c.process.HasExited){throw ($c.case+': '+$c.stderr.Result)}}
  Start-Sleep -Milliseconds 500
 }
}catch{
 [IO.File]::WriteAllText("$run/STOP",'Recorder stopped: '+$_.Exception.Message)
 throw
}finally{
 foreach($c in $captures){if(-not $c.process.HasExited){$c.process.StandardInput.WriteLine('q');$c.process.StandardInput.Flush();$c.process.StandardInput.Close()}}
 foreach($c in $captures){
  if(-not $c.process.HasExited){$null=$c.process.WaitForExit(25000);if(-not $c.process.HasExited){$c.process.Kill()}}
  [IO.File]::WriteAllText("$run/executions/$($c.case)-capture.log",$c.stderr.Result)
 }
 [IO.File]::WriteAllText("$run/recording.stopped",(Get-Date -Format o))
}
$dest=Join-Path $PresentationRoot ('屏幕实录\20261014-native-ui\'+$Dimension)
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$sceneLabel=@{static='S1-纯静态';dynamic='S2-运动障碍物';'large-change'='S3-持久变化';degradation='S4-走廊退化'}[$Scene]
$manifest=@()
foreach($c in $captures){
 if($c.process.ExitCode -ne 0){throw "Capture failed: $($c.case)"}
 $video="$run/executions/$($c.case).mp4"
 & ffprobe.exe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames,r_frame_rate -of json $video | Set-Content "$run/executions/$($c.case)-probe.json" -Encoding utf8
 $estimator=if($Dimension -eq '3D'){'GICP'}else{'AMCL'}
 $name=$sceneLabel+'__'+$Dimension+'__B-定位__'+$c.case+'-map_'+$estimator+'_独立RViz实时__'+$id.Substring(0,15)+'-'+$id.Substring($id.Length-6)+'.mp4'
 Copy-Item -LiteralPath $video -Destination (Join-Path $dest $name)
 $manifest+=@{case=$c.case;window_title=$c.title;map_topic=$c.map_topic;pose_topic=$c.pose_topic;tf_topic=$c.tf_topic;video='executions/'+$c.case+'.mp4';mirror_file=$name;sha256=(Get-FileHash -LiteralPath $video -Algorithm SHA256).Hash.ToLower()}
}
Copy-Item -LiteralPath "$run/executions/$($captures[0].case).mp4" -Destination "$run/execution.mp4"
[IO.File]::WriteAllText("$run/native-views.json",(ConvertTo-Json -InputObject $manifest -Depth 8))
$stopDeadline=(Get-Date).AddSeconds(15)
while(-not (Test-Path "$run/session-stopped.json")){
 if((Get-Date)-gt $stopDeadline){throw "Native shutdown did not finish: $run"}
 Start-Sleep -Milliseconds 100
}
if(-not (Test-Path "$run/truth.jsonl")){throw "Independent truth was not finalized: $run"}
[IO.File]::WriteAllText((Join-Path $RepoRoot ".cache/presentation/method-live-$Dimension-$Scene-latest.json"),(@{path=$run;flow=$flow;run_id=$id}|ConvertTo-Json))
if($Dimension -eq '2D'){
 [IO.File]::WriteAllText((Join-Path $RepoRoot ".cache/presentation/method-live-$Scene-latest.json"),(@{path=$run;flow=$flow;run_id=$id}|ConvertTo-Json))
}
Write-Host "COMPLETE: $run"
