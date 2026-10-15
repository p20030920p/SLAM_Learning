param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe',
 [string]$Suite='results/reference/own-hypotheses-20261016',
 [switch]$Resume
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $RepoRoot
$output=Join-Path $RepoRoot $Suite
if(Test-Path "$output/record.json"){throw "Evidence is sealed: $output"}
if((Test-Path $output) -and -not $Resume){throw 'Use a fresh Suite or -Resume'}
New-Item -ItemType Directory -Path $output -Force | Out-Null
foreach($scene in @('static','dynamic','motion','corridor')){
 if(-not (Test-Path "$output/$scene-A/record.json")){
  & "$PSScriptRoot/presentation.ps1" -Flow "mapping-own-$scene" -Auto -Record -Duration $(if($scene -eq 'motion'){45}else{60})
  $marker=Get-Content ".cache/presentation/mapping-own-$scene-latest.json" -Raw -Encoding utf8 | ConvertFrom-Json
  $run=$marker.path
  $deadline=(Get-Date).AddSeconds(40)
  while(-not (Test-Path "$run/session-stopped.json")){
   if((Get-Date)-gt $deadline){throw "Mapping did not stop: $run"}
   Start-Sleep -Milliseconds 200
  }
  & $Python src/scripts/presentation/package_own_hypotheses.py $run "$output/$scene-A" A
  if($LASTEXITCODE -ne 0){throw "Mapping package failed: $run"}
 }
 if(-not (Test-Path "$output/$scene-B/record.json")){
  $frozenA=[IO.Path]::GetFullPath("$output/$scene-A")
  [IO.File]::WriteAllText("$RepoRoot/.cache/presentation/mapping-own-$scene-latest.json",(@{path=$frozenA;scope='Frozen own-method A selected for this B'} | ConvertTo-Json))
  $bScene=if($scene -eq 'corridor'){'degradation'}elseif($scene -eq 'motion'){'static'}else{$scene}
  & "$PSScriptRoot/record-methods.ps1" -Scene $bScene -OwnMaps -MotionMap:($scene -eq 'motion') -Duration 65
  $marker=Get-Content ".cache/presentation/method-live-2D-$bScene-latest.json" -Raw -Encoding utf8 | ConvertFrom-Json
  & $Python src/scripts/presentation/package_own_hypotheses.py $marker.path "$output/$scene-B" B
  if($LASTEXITCODE -ne 0){throw "Localization package failed: $scene"}
 }
}
Write-Host "Own prototype recordings completed: $output"
