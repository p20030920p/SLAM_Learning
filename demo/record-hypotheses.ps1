param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe',
 [string]$Suite='results/reference/direction-20261016-v2',
 [switch]$Resume
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $RepoRoot
$scriptRoot=Join-Path $RepoRoot 'src/scripts/presentation'
$output=Join-Path $RepoRoot $Suite
if(Test-Path -LiteralPath (Join-Path $output 'record.json')){throw "Evidence is sealed: $output"}
if((Test-Path -LiteralPath $output) -and -not $Resume){throw "Use a fresh evidence directory or -Resume: $output"}
New-Item -ItemType Directory -Path $output -Force | Out-Null
function RunPython([string]$name,[string[]]$arguments){
 & $Python (Join-Path $scriptRoot $name) @arguments | Out-File -FilePath (Join-Path $output 'packaging.log') -Append -Encoding utf8
 if($LASTEXITCODE -ne 0){throw "Failed: $name"}
}
function ReadRun([string]$marker){
 $item=Get-Content (Join-Path $RepoRoot ('.cache/presentation/'+$marker+'-latest.json')) -Raw -Encoding utf8 | ConvertFrom-Json
 $path=[IO.Path]::GetFullPath($item.path)
 $deadline=(Get-Date).AddSeconds(40)
 while(-not (Test-Path -LiteralPath (Join-Path $path 'session-stopped.json'))){
  if((Get-Date)-gt $deadline){throw "Native shutdown did not finish: $path"}
  Start-Sleep -Milliseconds 200
 }
 $stop=Get-Content (Join-Path $path 'session-stopped.json') -Raw | ConvertFrom-Json
 if($stop.exit_code -ne 0){throw "Native run failed: $path"}
 return $path
}
foreach($scene in @('static','dynamic','corridor','landmark-corridor')){
 if($Resume -and (Test-Path "$output/2d-$scene/record.json") -and (Test-Path "$output/2d-A-$scene/record.json")){
  Write-Host "Keep completed fresh A/B: $scene"
  continue
 }
 Write-Host "Fresh A/B: $scene"
 $landmark=$scene -eq 'landmark-corridor'
 $mappingScene=if($landmark){'corridor'}else{$scene}
 & "$PSScriptRoot/srrg.ps1" -Scene $mappingScene -Landmarks:$landmark -Duration 65
 $localizationScene=if($landmark){'landmark-degradation'}elseif($scene -eq 'corridor'){'degradation'}else{$scene}
 & "$PSScriptRoot/record-methods.ps1" -Scene $localizationScene -Dimension 2D -Duration 72
 $run=ReadRun ('method-live-2D-'+$localizationScene)
 RunPython 'package_simple_hypotheses.py' @($run,$Suite,$scene)
}
RunPython 'compare_corridor_geometry.py' @("$output/2d-corridor","$output/2d-landmark-corridor","$output/corridor-comparison.json")
Write-Host 'Fresh FAST-LIO A and frozen-map B'
& "$PSScriptRoot/presentation.ps1" -Flow mapping-fastlio-static -Auto -Record -Duration 45
$fastRun=ReadRun 'mapping-fastlio-static'
RunPython 'package_direction_run.py' @($fastRun,"$output/fastlio-motion")
RunPython 'score_fastlio_study.py' @($fastRun,"$output/fastlio-maps")
& "$PSScriptRoot/record-methods.ps1" -Scene static -Dimension 3D -FastLioMaps -Duration 65
$fastB=ReadRun 'method-live-3D-static'
RunPython 'package_direction_run.py' @($fastB,"$output/fastlio-B")
RunPython 'score_direction_3d_b.py' @("$output/fastlio-B")
$fastWsl='/mnt/'+$fastRun.Substring(0,1).ToLower()+'/'+$fastRun.Substring(3).Replace('\','/')
$outWsl='/mnt/'+$output.Substring(0,1).ToLower()+'/'+$output.Substring(3).Replace('\','/')
$repoWsl='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
& wsl.exe -d Ubuntu-24.04 -u root -- bash -c "source /opt/ros/jazzy/setup.bash && python3 $repoWsl/src/scripts/presentation/audit_fastlio_inputs.py $fastWsl $outWsl/fastlio-input-audit.json"
if($LASTEXITCODE -ne 0){throw 'FAST-LIO serialized input audit failed'}
[IO.File]::WriteAllText((Join-Path $output 'completed.json'),(@{completed=(Get-Date -Format o);suite=$Suite;new_mapping_runs=5;new_localization_runs=5} | ConvertTo-Json))
Write-Host "Fresh three-hypothesis recordings completed: $output"
