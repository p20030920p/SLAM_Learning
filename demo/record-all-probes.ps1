param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲',
 [switch]$RebuildMaps,
 [string]$ResumeBatch=''
)
$ErrorActionPreference='Stop'
$missing=@('static','dynamic','corridor','height-corridor') | Where-Object {-not (Test-Path "$RepoRoot/.cache/presentation/probe-maps-$_-latest.json")}
if($RebuildMaps -or $missing.Count -gt 0){
 & "$PSScriptRoot/build-probe-maps.ps1" -RepoRoot $RepoRoot -PresentationRoot $PresentationRoot
}
if($ResumeBatch){
 $batchPath=[IO.Path]::GetFullPath($ResumeBatch)
 $previous=Get-Content -LiteralPath $batchPath -Raw -Encoding UTF8 | ConvertFrom-Json
 $diagnostics=@($previous.diagnostics)
 if($previous.status -eq 'failed'){$diagnostics+=@{state=$previous.status;error=$previous.error;finished_at=$previous.finished_at}}
 $batch=@{status='running';started_at=$previous.started_at;scope=$previous.scope;runs=@($previous.runs);diagnostics=$diagnostics;resumed_at=(Get-Date -Format o)}
}else{
 $batchPath=Join-Path $RepoRoot ('results/runs/presentation/probe-calibrated-batch-'+(Get-Date -Format 'yyyyMMdd-HHmmss')+'.json')
 $batch=@{status='running';started_at=(Get-Date -Format o);scope='Mapping-A calibrated height; four original scenes plus explicitly derived height control; fixed settings; all fresh captures retained';runs=@();diagnostics=@()}
}
[IO.File]::WriteAllText($batchPath,($batch|ConvertTo-Json -Depth 10))
try{
 foreach($dimension in @('2D','3D')){
  foreach($scene in @('static','dynamic','large-change','degradation','height-corridor')){
   if(@($batch.runs | Where-Object {$_.dimension -eq $dimension -and $_.scene -eq $scene}).Count -gt 0){continue}
   Write-Host "NEXT: $dimension / $scene"
   & "$PSScriptRoot/record-probes.ps1" -Scene $scene -Dimension $dimension -RepoRoot $RepoRoot -PresentationRoot $PresentationRoot
   $run=Get-Content "$RepoRoot/.cache/presentation/probe-calibrated-live-$dimension-$scene-latest.json" -Raw -Encoding UTF8 | ConvertFrom-Json
   $batch.runs+=@{dimension=$dimension;scene=$scene;path=$run.path;run_id=$run.run_id}
   [IO.File]::WriteAllText($batchPath,($batch|ConvertTo-Json -Depth 10))
  }
 }
 $batch.status='completed'
}catch{
 $batch.status='failed';$batch.error=$_.Exception.Message
 throw
}finally{
 $batch.finished_at=(Get-Date -Format o)
 [IO.File]::WriteAllText($batchPath,($batch|ConvertTo-Json -Depth 10))
}
Write-Host "BATCH COMPLETE: $batchPath"
