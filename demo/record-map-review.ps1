param([string]$RepoRoot='D:\workspace\be2\slam_learning_updated',[double]$Duration=40)
$ErrorActionPreference='Stop'
$id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-3d-map-review-'+([guid]::NewGuid().ToString('N').Substring(0,6))
$run=Join-Path $RepoRoot ('results\runs\presentation\'+$id)
New-Item -ItemType Directory -Path $run -Force | Out-Null
$rootw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
$runw='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
$title='SLAM-3D-MAP-REVIEW-'+$id.Substring($id.Length-6)
Start-Process -FilePath (Get-Command wt.exe).Source -ArgumentList "-w new --pos 0,740 --size 200,13 new-tab --title $title --suppressApplicationTitle wsl.exe -d Ubuntu-24.04 -- bash $rootw/src/scripts/presentation/run_map_review.sh $runw"
$deadline=(Get-Date).AddSeconds(70)
while(-not (Test-Path "$run/ready.json")) {if((Get-Date)-gt $deadline){throw 'Map review did not start'};Start-Sleep -Milliseconds 300}
Start-Sleep -Seconds 4
$sources=@();$index=0
foreach($method in @('raw','dufomap','beautymap')){
 $sources+="gfxcapture=window_title=^3D MAP REVIEW $method - RViz2.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=640:720:force_original_aspect_ratio=decrease,pad=640:720:(ow-iw)/2:(oh-ih)/2[v$index]"
 $index++
}
$sources+='[v0][v1][v2]hstack=inputs=3[gui]'
$sources+="gfxcapture=window_title=^$title.*:max_framerate=12:capture_border=1,hwdownload,format=bgra,scale=1920:360:force_original_aspect_ratio=decrease,pad=1920:360:(ow-iw)/2:(oh-ih)/2[cli]"
$sources+='[gui][cli]vstack=inputs=2,format=yuv420p[out]'
$filter=$sources -join ';'
[IO.File]::WriteAllText("$run/capture-filter.txt",$filter)
try {
 & ffmpeg.exe -hide_banner -loglevel warning -filter_complex_threads 4 -filter_complex $filter -map '[out]' -t $Duration -r 12 -fps_mode cfr -c:v libx264 -threads 2 -preset veryfast -crf 22 -y "$run/execution.mp4" 2> "$run/capture.log"
 if($LASTEXITCODE -ne 0){throw 'Map-result review capture failed'}
} finally {[IO.File]::WriteAllText("$run/STOP",'Review recording finished')}
[IO.File]::WriteAllText((Join-Path $RepoRoot '.cache/presentation/3d-map-review-latest.json'),(@{path=$run;run_id=$id}|ConvertTo-Json))
Write-Output "COMPLETE: $run"
