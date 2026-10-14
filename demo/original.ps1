param(
 [ValidateSet('dufomap','beautymap','ir-mcl','adam-mcl')][string]$Method='dufomap',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [ValidateRange(1,100)][int]$Trials=10,
 [switch]$Record
)
$ErrorActionPreference='Stop'
$id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-author-'+$Method+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$id)
New-Item -ItemType Directory -Path $run -Force | Out-Null
$rw='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
$rootw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
$title='SLAM-AUTHOR-'+$Method+'-'+$id.Substring($id.Length-6)
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList "-w new --pos 0,0 --size 160,48 new-tab --title $title --suppressApplicationTitle wsl.exe -d Ubuntu-22.04 -- bash $rootw/src/scripts/presentation/run_original.sh $Method $rw $Trials"
$deadline=(Get-Date).AddMinutes(3)
while (-not (Test-Path "$run/ready.json")) {
 if((Get-Date) -gt $deadline){throw "Author environment did not become ready: $run"}
 Start-Sleep -Milliseconds 300
}
$proc=$null
if($Record){
 $filter='scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p'
 $info=[Diagnostics.ProcessStartInfo]::new()
 $info.FileName=(Get-Command ffmpeg.exe).Source
 $info.Arguments='-hide_banner -loglevel warning -f gdigrab -framerate 15 -i "title='+$title+'" -vf "'+$filter+'" -r 15 -fps_mode cfr -c:v libx264 -preset veryfast -crf 23 -movflags +frag_keyframe+empty_moov -y "'+$run+'\execution.mp4"'
 $info.UseShellExecute=$false; $info.CreateNoWindow=$true
 $info.RedirectStandardInput=$true; $info.RedirectStandardError=$true
 $proc=[Diagnostics.Process]::new(); $proc.StartInfo=$info; $null=$proc.Start()
 $stderr=$proc.StandardError.ReadToEndAsync()
 Start-Sleep -Seconds 2
 if($proc.HasExited){throw $stderr.Result}
}
[IO.File]::WriteAllText("$run/recording.started",(Get-Date -Format o))
Write-Host "AUTHOR DESKTOP RUN: $run"
try{
 while(-not (Test-Path "$run/finished.json")){
  if(Test-Path "$run/failed.json"){throw (Get-Content "$run/execution.json" -Raw)}
  if($proc -and $proc.HasExited){throw $stderr.Result}
  Start-Sleep -Milliseconds 500
 }
 Start-Sleep -Seconds 3
}finally{
 if($proc -and -not $proc.HasExited){$proc.StandardInput.WriteLine('q'); $proc.StandardInput.Flush(); $null=$proc.WaitForExit(15000); if(-not $proc.HasExited){$proc.Kill()}}
 if($proc){[IO.File]::WriteAllText("$run/capture.log",$stderr.Result)}
 [IO.File]::WriteAllText("$run/capture.finished",(Get-Date -Format o))
}
if($Record){
 if($proc.ExitCode -ne 0){throw "Capture exit $($proc.ExitCode)"}
 & ffprobe.exe -v error -show_entries format=duration,size -show_entries stream=width,height,nb_frames,r_frame_rate -of json "$run/execution.mp4" | Set-Content "$run/video-probe.json" -Encoding utf8
 $dest='F:\be2演讲\屏幕实录\20261014-native-ui'
 New-Item -ItemType Directory -Path $dest -Force | Out-Null
 Copy-Item -LiteralPath "$run/execution.mp4" -Destination (Join-Path $dest "$id.mp4")
}
[IO.File]::WriteAllText((Join-Path $RepoRoot ".cache/presentation/author-$Method-latest.json"),(@{path=$run;method=$Method;run_id=$id}|ConvertTo-Json))
Write-Host "COMPLETE: $run"
