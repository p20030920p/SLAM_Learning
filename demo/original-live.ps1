param(
 [ValidateSet('dufomap','beautymap','ir-mcl')][string]$Method='ir-mcl',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated'
)
$ErrorActionPreference='Stop'
$id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-author-live-'+$Method+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$id)
New-Item -ItemType Directory -Path $run -Force | Out-Null
$rw='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
$rootw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
$title='SLAM-AUTHOR-LIVE-'+$Method+'-'+$id.Substring($id.Length-6)
$viewer=Start-Process -FilePath 'wsl.exe' -WindowStyle Hidden -PassThru -ArgumentList "-d Ubuntu-24.04 -- bash $rootw/src/scripts/presentation/run_author_view.sh $Method $rw"
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList "-w new --pos 0,740 --size 200,13 new-tab --title $title --suppressApplicationTitle wsl.exe -d Ubuntu-22.04 -- bash $rootw/src/scripts/presentation/run_original.sh $Method $rw 1 true"
$deadline=(Get-Date).AddMinutes(4)
while(-not (Test-Path "$run/ready.json") -or -not (Test-Path "$run/viewer-ready.json")){
 if($viewer.HasExited){throw "Author viewer failed or another author demo is active: $run"}
 if((Get-Date)-gt $deadline){[IO.File]::WriteAllText("$run/viewer-stop",'timeout');throw "Author/viewer not ready: $run"}
 Start-Sleep -Milliseconds 300
}
Start-Sleep -Seconds 4
$filter="gfxcapture=window_title=^SLAM AUTHOR LIVE - $Method.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=1920:720:force_original_aspect_ratio=decrease,pad=1920:720:(ow-iw)/2:(oh-ih)/2[rv];gfxcapture=window_title=^$title.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=1920:360:force_original_aspect_ratio=decrease,pad=1920:360:(ow-iw)/2:(oh-ih)/2[cli];[rv][cli]vstack=inputs=2,format=yuv420p[out]"
[IO.File]::WriteAllText("$run/capture-filter.txt",$filter)
$info=[Diagnostics.ProcessStartInfo]::new();$info.FileName=(Get-Command ffmpeg.exe).Source
$info.Arguments='-hide_banner -loglevel warning -filter_complex_threads 1 -filter_complex "'+$filter+'" -map "[out]" -r 12 -fps_mode cfr -c:v libx264 -threads 2 -preset veryfast -crf 22 -y "'+$run+'\execution.mp4"'
$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardInput=$true;$info.RedirectStandardError=$true
$proc=[Diagnostics.Process]::new();$proc.StartInfo=$info;$null=$proc.Start();$stderr=$proc.StandardError.ReadToEndAsync()
try{
 Start-Sleep -Seconds 2
 if($proc.HasExited){throw $stderr.Result}
 [IO.File]::WriteAllText("$run/recording.started",(Get-Date -Format o))
 while(-not (Test-Path "$run/finished.json")){
  if(Test-Path "$run/failed.json"){throw (Get-Content "$run/execution.json" -Raw)}
  if($proc.HasExited){throw $stderr.Result}
  Start-Sleep -Milliseconds 500
 }
 Start-Sleep -Seconds 3
}finally{
 if(-not $proc.HasExited){$proc.StandardInput.WriteLine('q');$proc.StandardInput.Flush();$null=$proc.WaitForExit(20000);if(-not $proc.HasExited){$proc.Kill()}}
 [IO.File]::WriteAllText("$run/capture.log",$stderr.Result)
 [IO.File]::WriteAllText("$run/capture.finished",(Get-Date -Format o))
 [IO.File]::WriteAllText("$run/viewer-stop",'capture complete')
}
if($proc.ExitCode -ne 0){throw 'Author live capture failed'}
$dest='F:\be2演讲\屏幕实录\20261014-native-ui'
$name='论文原库__'+$Method+'__原生计算与RViz实时__'+$id.Substring(0,15)+'-'+$id.Substring($id.Length-6)+'.mp4'
Copy-Item -LiteralPath "$run/execution.mp4" -Destination (Join-Path $dest $name)
[IO.File]::WriteAllText((Join-Path $RepoRoot ".cache/presentation/author-live-$Method-latest.json"),(@{path=$run;method=$Method;run_id=$id}|ConvertTo-Json))
Write-Host "COMPLETE: $run"
