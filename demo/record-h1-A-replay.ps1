param([ValidateSet('static','dynamic')][string]$Scene='dynamic',[switch]$Refined=$true)
$ErrorActionPreference='Stop'
$root='D:\workspace\be2\slam_learning_updated'
$suiteName=if($Refined){'h1-refined-20261016'}else{'h1-supported-20261016'}
$replayFlag=if($Refined){'refined'}else{''}
$out=Join-Path $root "results/reference/$suiteName/$Scene-A"
if(Test-Path "$out/execution.mp4"){throw 'Preserve existing capture'}
$worker=Start-Process -FilePath wsl.exe -WindowStyle Hidden -ArgumentList "-d Ubuntu-24.04 -- bash /mnt/d/workspace/be2/slam_learning_updated/src/scripts/presentation/h1_replay_a.sh $Scene $replayFlag" -PassThru -RedirectStandardOutput "$out/replay.stdout.log" -RedirectStandardError "$out/replay.stderr.log"
$deadline=(Get-Date).AddMinutes(2)
while(-not (Test-Path "$out/A-replay-ready.json")){
 if($worker.HasExited -or (Get-Date)-gt $deadline){throw 'Native A replay did not start'}
 Start-Sleep -Milliseconds 300
}
$filter="gfxcapture=window_title=^H1 MAP REPLAY $Scene.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=1600:900:force_original_aspect_ratio=decrease,pad=1600:900:(ow-iw)/2:(oh-ih)/2,format=yuv420p[out]"
$info=[Diagnostics.ProcessStartInfo]::new()
$info.FileName=(Get-Command ffmpeg.exe).Source
$info.Arguments='-hide_banner -loglevel warning -filter_complex "'+$filter+'" -map "[out]" -r 12 -fps_mode cfr -c:v libx264 -threads 2 -preset veryfast -crf 21 -progress "'+$out+'\capture-progress.txt" -y "'+$out+'\execution.mp4"'
$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardInput=$true;$info.RedirectStandardError=$true
$capture=[Diagnostics.Process]::new();$capture.StartInfo=$info;$null=$capture.Start();$errors=$capture.StandardError.ReadToEndAsync()
try{
 Start-Sleep -Seconds 3
 if($capture.HasExited){throw $errors.Result}
 [IO.File]::WriteAllText("$out/A-capture-started",(Get-Date -Format o))
 $deadline=(Get-Date).AddMinutes(3)
 while(-not (Test-Path "$out/A-replay-finished.json")){
  if($worker.HasExited -or $capture.HasExited -or (Get-Date)-gt $deadline){throw 'A replay/capture failed'}
  Start-Sleep -Milliseconds 300
 }
}finally{
 if(-not $capture.HasExited){$capture.StandardInput.WriteLine('q');$capture.StandardInput.Flush();$capture.StandardInput.Close();$null=$capture.WaitForExit(20000)}
 [IO.File]::WriteAllText("$out/capture.log",$errors.Result)
 [IO.File]::WriteAllText("$out/A-capture-stopped",(Get-Date -Format o))
}
if($capture.ExitCode -ne 0){throw 'A capture encoding failed'}
& 'D:/workspace/be2/SLAM_Learning/.venv/Scripts/python.exe' -X utf8 -c "import sys;sys.path.insert(0,r'$root/src/scripts/presentation');from pathlib import Path;from package_session import gif;from h1_revision import write;out=Path(r'$out');write(out/'video-timing.json',gif(out/'execution.mp4',out/'execution.gif'))"
if($LASTEXITCODE -ne 0){throw 'A GIF failed'}
Write-Host "H1 A native replay captured: $Scene"
