param([ValidateSet('check','setup','reproduce','experiment','departure','stop','update','amcl','build_maps','choose_map','compare','static_keyboard','dynamic_keyboard','benchmark')][string]$Action='check',
      [switch]$NoGui,[switch]$NonInteractive)
$ErrorActionPreference='Stop'
$learningRoot=Split-Path $PSScriptRoot -Parent
$physicalRoot=Join-Path (Split-Path $learningRoot -Parent) 'SLAM-Physical'
if (-not (Test-Path -LiteralPath $physicalRoot)) {
  & git -c http.proxy= clone https://github.com/p20030920p/SLAM-Physical.git $physicalRoot
  if ($LASTEXITCODE -ne 0) { throw 'Cannot clone SLAM-Physical. Check network and Git installation.' }
}
$scriptName=@{check='doctor';setup='setup';reproduce='reproduce';experiment='experiment';departure='experiment';stop='stop';update='update';amcl='localize';build_maps='build-maps';choose_map='localize';compare='compare-localization';static_keyboard='scene-keyboard';dynamic_keyboard='scene-keyboard';benchmark='benchmark-localization'}[$Action]
$scriptPath=Join-Path $physicalRoot ('launchers\'+$scriptName+'.ps1')
if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'The sibling folder is not a complete SLAM-Physical checkout.' }
$options=@{}
if ($NonInteractive -and $Action -in @('check','reproduce','experiment','departure','update','amcl','build_maps','choose_map','compare','static_keyboard','dynamic_keyboard','benchmark')) { $options.NonInteractive=$true }
if ($NoGui -and $Action -in @('reproduce','experiment','departure','amcl','choose_map','static_keyboard','dynamic_keyboard')) { $options.NoGui=$true }
if ($Action -eq 'departure') { $options.Scenario='departure' }
if ($Action -eq 'choose_map') { $options.ChooseMap=$true }
if ($Action -eq 'static_keyboard') { $options.Scenario='static' }
if ($Action -eq 'dynamic_keyboard') { $options.Scenario='dynamic' }
& $scriptPath @options
