param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe',
 [string]$RunRoot='F:\be2演讲\原始会话\practice-frozen-20261016',
 [string]$StaticRun=''
)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $RepoRoot
$suite=Join-Path $RepoRoot 'results/reference/practice-frozen-20261016'
foreach($key in @('3d-static','3d-dynamic','3d-corridor','3d-change','srrg-change')){
 if(Test-Path "$suite/$key/record.json"){Write-Host "SEALED: $key";continue}
 & $Python -X utf8 src/scripts/presentation/package_frozen_practice.py prepare $key
 if($LASTEXITCODE -ne 0){throw "Cannot freeze: $key"}
 if($key -eq '3d-static' -and $StaticRun){$run=$StaticRun}else{
  $scene=@{'3d-static'='static';'3d-dynamic'='dynamic';'3d-corridor'='degradation';'3d-change'='large-change';'srrg-change'='large-change'}[$key]
  $dimension=if($key.StartsWith('3d-')){'3D'}else{'2D'}
  & "$PSScriptRoot/record-methods.ps1" -Scene $scene -Dimension $dimension -Duration 65 -RunRoot $RunRoot
  $marker=Get-Content ".cache/presentation/method-live-$dimension-$scene-latest.json" -Raw -Encoding utf8 | ConvertFrom-Json
  $run=$marker.path
 }
 & $Python -X utf8 src/scripts/presentation/package_frozen_practice.py finish $key $run
 if($LASTEXITCODE -ne 0){throw "Cannot package: $key"}
}
Write-Host 'FROZEN PRACTICE RECORDINGS COMPLETE'
