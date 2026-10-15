param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲'
)
$ErrorActionPreference='Stop'
foreach($scene in @('static','dynamic','corridor','height-corridor')){
 & "$PSScriptRoot/presentation.ps1" -Flow "mapping-probe-$scene" -RepoRoot $RepoRoot -PresentationRoot $PresentationRoot -Auto -Record -Duration 90
 $marker=Get-Content "$RepoRoot/.cache/presentation/mapping-probe-$scene-latest.json" -Raw -Encoding UTF8 | ConvertFrom-Json
 $run=$marker.path
 $deadline=(Get-Date).AddSeconds(30)
 while(-not (Test-Path "$run/session-stopped.json")){
  if((Get-Date)-gt $deadline){throw "Mapping did not stop: $run"}
  Start-Sleep -Milliseconds 200
 }
 $repoWsl='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
 $runWsl='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
 & wsl.exe -d Ubuntu-24.04 -- python3 "$repoWsl/src/scripts/presentation/build_probe_maps.py" $runWsl
 if($LASTEXITCODE -ne 0){throw "Probe map processing failed: $run"}
}
