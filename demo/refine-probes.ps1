param(
 [ValidateSet('corridor','height-corridor')][string]$Scene='height-corridor',
 [ValidateSet('2D','3D')][string]$Dimension='2D',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲',
 [switch]$All
)
$ErrorActionPreference='Stop'
$pairs=if($All){@(
 [pscustomobject]@{dimension='2D';scene='corridor'},
 [pscustomobject]@{dimension='2D';scene='height-corridor'},
 [pscustomobject]@{dimension='3D';scene='corridor'},
 [pscustomobject]@{dimension='3D';scene='height-corridor'}
)}else{@([pscustomobject]@{dimension=$Dimension;scene=$Scene})}
$python=Join-Path $RepoRoot 'src/.venv/Scripts/python.exe'
foreach($pair in $pairs){
 $dimensionName=$pair.dimension;$sceneName=$pair.scene
 $parent=Join-Path $RepoRoot ("results/reference/probe-calibrated-"+$dimensionName.ToLower()+"-$sceneName/record.json")
 if(-not (Test-Path -LiteralPath $parent)){throw "Verified archived input is missing: $parent"}
 $id=(Get-Date -Format 'yyyyMMdd-HHmmss')+'-offline-refinement-'+$dimensionName.ToLower()+'-'+$sceneName+'-'+([guid]::NewGuid().ToString('N').Substring(0,6))
 $run=Join-Path $PresentationRoot ('原始会话/hypotheses-refinement/'+$id)
 Write-Host 'New offline inference on archived lidar/depth/odometry. The generated video is a saved-output replay.'
 & $python "$RepoRoot/src/scripts/presentation/refine_saved_probe.py" $parent $run --calibrated
 if($LASTEXITCODE -ne 0){throw "Offline refinement failed: $run"}
 $mirrorRoot=Join-Path $PresentationRoot '本轮成片/hypotheses'
 $mirror=Join-Path $mirrorRoot ('refinements/'+$id)
 New-Item -ItemType Directory -Path (Split-Path $mirror) -Force | Out-Null
 Copy-Item -LiteralPath $run -Destination $mirror -Recurse
 & $python "$RepoRoot/src/scripts/presentation/render_probe_gallery.py" $mirrorRoot "$mirrorRoot/index.html"
 if($LASTEXITCODE -ne 0){throw 'Refinement gallery update failed'}
 Write-Host "VERIFIED OFFLINE RESULT: $mirror"
}
