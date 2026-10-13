param([ValidateSet('check','setup','reproduce','experiment','departure','stop','update')][string]$Action='check',
      [switch]$NoGui,[switch]$NonInteractive)
$ErrorActionPreference='Stop'
$learningRoot=Split-Path $PSScriptRoot -Parent
$physicalRoot=Join-Path (Split-Path $learningRoot -Parent) 'SLAM-Physical'
if (-not (Test-Path -LiteralPath $physicalRoot)) {
  & git -c http.proxy= clone https://github.com/p20030920p/SLAM-Physical.git $physicalRoot
  if ($LASTEXITCODE -ne 0) { throw 'Cannot clone SLAM-Physical. Check network and Git installation.' }
}
$scriptName=@{check='doctor';setup='setup';reproduce='reproduce';experiment='experiment';departure='experiment';stop='stop';update='update'}[$Action]
$scriptPath=Join-Path $physicalRoot ('launchers\'+$scriptName+'.ps1')
if (-not (Test-Path -LiteralPath $scriptPath)) { throw 'The sibling folder is not a complete SLAM-Physical checkout.' }
$options=@{}
if ($NonInteractive -and $Action -in @('check','reproduce','experiment','departure','update')) { $options.NonInteractive=$true }
if ($NoGui -and $Action -in @('reproduce','experiment','departure')) { $options.NoGui=$true }
if ($Action -eq 'departure') { $options.Scenario='departure' }
& $scriptPath @options
