param([string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe')
$ErrorActionPreference='Stop'
$root='D:\workspace\be2\slam_learning_updated'
Set-Location -LiteralPath $root
$suite=Join-Path $root 'results/reference/practice-3d-visible-20261016'
$rawRoot='F:\be2演讲\原始会话\practice-3d-visible-20261016'
foreach($scene in @('static','dynamic','corridor')){
 if(Test-Path "$suite/$scene-A/record.json"){continue}
 $marker=Get-Content ".cache/presentation/mapping-$scene-latest.json" -Raw | ConvertFrom-Json
 $run=$marker.path
 if($run -notlike '*practice-3d-visible-20261016*' -or -not(Test-Path "$run/session-stopped.json")){
  & "$PSScriptRoot/presentation.ps1" -Flow "mapping-$scene" -Auto -Record -View3D -Duration 65 -RunRoot $rawRoot
  $marker=Get-Content ".cache/presentation/mapping-$scene-latest.json" -Raw | ConvertFrom-Json
  $run=$marker.path
 }
 & wsl.exe -d Ubuntu-22.04 -- bash /mnt/d/workspace/be2/slam_learning_updated/src/scripts/presentation/build_maps.sh $scene
 if($LASTEXITCODE -ne 0){throw "Native cleaners failed: $scene"}
 $mapsMarker=Get-Content ".cache/presentation/maps-$scene-latest.json" -Raw | ConvertFrom-Json
 $mapsValue=$mapsMarker.path
 $maps=if($mapsValue.StartsWith('/mnt/')){$mapsValue.Substring(5,1).ToUpper()+':'+$mapsValue.Substring(6).Replace('/','\')}else{$mapsValue}
 & $Python -X utf8 src/scripts/presentation/visible_3d_suite.py A $scene $run $maps
 if($LASTEXITCODE -ne 0){throw "Cannot package A: $scene"}
}
foreach($scene in @('static','dynamic','corridor','change')){
 if(Test-Path "$suite/$scene-B/record.json"){continue}
 & $Python -X utf8 src/scripts/presentation/visible_3d_suite.py prepare-B $scene
 if($LASTEXITCODE -ne 0){throw "Cannot freeze A: $scene"}
 $bScene=if($scene -eq 'corridor'){'degradation'}elseif($scene -eq 'change'){'large-change'}else{$scene}
 & "$PSScriptRoot/record-methods.ps1" -Scene $bScene -Dimension 3D -Duration 65 -RunRoot $rawRoot
 $marker=Get-Content ".cache/presentation/method-live-3D-$bScene-latest.json" -Raw | ConvertFrom-Json
 & $Python -X utf8 src/scripts/presentation/visible_3d_suite.py B $scene $marker.path
 if($LASTEXITCODE -ne 0){throw "Cannot package B: $scene"}
}
Write-Host 'LIVE 3D A/B SUITE COMPLETE'
