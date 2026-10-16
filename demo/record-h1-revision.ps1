param([string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe',[switch]$Refined=$true)
$ErrorActionPreference='Stop'
$root='D:\workspace\be2\slam_learning_updated'
Set-Location -LiteralPath $root
$suiteName=if($Refined){'h1-refined-20261016'}else{'h1-supported-20261016'}
$suite=Join-Path $root ('results/reference/'+$suiteName)
$rawRoot=Join-Path 'F:\be2演讲\原始会话' $suiteName
foreach($item in @(@('static',1),@('dynamic',1),@('dynamic',2),@('dynamic',3))){
 $scene=$item[0];$trial=$item[1]
 $name=$scene+'-B'+$(if($trial -gt 1){[string]$trial}else{''})
 $target=Join-Path $suite $name
 if(Test-Path "$target/record.json"){continue}
 $mapping=[IO.Path]::GetFullPath("$suite/$scene-A")
 [IO.File]::WriteAllText("$root/.cache/presentation/mapping-own-$scene-latest.json",(@{path=$mapping;scope='Frozen revised H1 A; primary Raw/Temporal controls'}|ConvertTo-Json))
 & "$PSScriptRoot/record-methods.ps1" -Scene $scene -OwnMaps -Duration 65 -RunRoot $rawRoot
 if($LASTEXITCODE -ne 0){throw "H1 live B failed: $name"}
 $marker=Get-Content ".cache/presentation/method-live-2D-$scene-latest.json" -Raw -Encoding utf8|ConvertFrom-Json
 & $Python -X utf8 src/scripts/presentation/package_own_hypotheses.py $marker.path $target B
 if($LASTEXITCODE -ne 0){throw "H1 B packaging failed: $name"}
}
