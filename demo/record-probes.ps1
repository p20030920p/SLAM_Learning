param(
 [ValidateSet('static','dynamic','large-change','degradation','height-corridor')][string]$Scene='static',
 [ValidateSet('2D','3D')][string]$Dimension='2D',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲',
 [double]$Duration=90,
 [switch]$SkipPackage
)
$ErrorActionPreference='Stop'
if($Scene -in @('degradation','height-corridor') -and -not $PSBoundParameters.ContainsKey('Duration')){$Duration=120}
$mappingScene=if($Scene -eq 'large-change'){'static'}elseif($Scene -eq 'degradation'){'corridor'}else{$Scene}
if(-not (Test-Path "$RepoRoot/.cache/presentation/probe-maps-$mappingScene-latest.json")){
 throw 'Matched depth/lidar mapping A is missing. Run 38-采集假设实验地图A.bat first.'
}
& "$PSScriptRoot/record-methods.ps1" -Scene $Scene -Dimension $Dimension -Duration $Duration -Hypotheses -Calibrated -RepoRoot $RepoRoot -PresentationRoot $PresentationRoot
if(-not $SkipPackage){
 $marker=Get-Content "$RepoRoot/.cache/presentation/probe-calibrated-live-$Dimension-$Scene-latest.json" -Raw -Encoding UTF8 | ConvertFrom-Json
 $python=Join-Path $RepoRoot 'src/.venv/Scripts/python.exe'
 $package=Join-Path $marker.path 'evidence'
 & $python "$RepoRoot/src/scripts/presentation/package_session.py" $marker.path $package --no-replay
 if($LASTEXITCODE -ne 0){throw "Probe evidence verification failed: $($marker.path)"}
 $mirrorRoot=Join-Path $PresentationRoot '本轮成片/hypotheses'
 $mirror=Join-Path $mirrorRoot "$Dimension/$($marker.run_id)"
 New-Item -ItemType Directory -Path (Split-Path $mirror) -Force | Out-Null
 Copy-Item -LiteralPath $package -Destination $mirror -Recurse
 & $python "$RepoRoot/src/scripts/presentation/render_probe_gallery.py" $mirrorRoot "$mirrorRoot/index.html"
 if($LASTEXITCODE -ne 0){throw 'Probe gallery update failed'}
 Write-Host "VERIFIED RESULTS: $mirror"
}
