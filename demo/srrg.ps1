param(
 [ValidateSet('static','dynamic','large-change','corridor')][string]$Scene='dynamic',
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$PresentationRoot='F:\be2演讲',
 [double]$Duration=65,
 [switch]$Keyboard,
 [switch]$Landmarks,
 [switch]$All
)
$ErrorActionPreference='Stop'
if($Landmarks){$Scene='corridor'}
$rw='/mnt/'+$RepoRoot.Substring(0,1).ToLower()+'/'+$RepoRoot.Substring(3).Replace('\','/')
if($All){
 foreach($item in @('static','dynamic','large-change','corridor')){
  & $PSCommandPath -Scene $item -RepoRoot $RepoRoot -PresentationRoot $PresentationRoot -Duration $Duration
 }
 exit 0
}
$serverPath="$rw/src/scripts/presentation/srrg/server.py"
$server=(& wsl.exe -d Ubuntu-20.04 -u root -- pgrep -f "^python3 -u $serverPath`$")
if(-not $server){
 Start-Process wsl.exe -WindowStyle Hidden -ArgumentList "-d Ubuntu-20.04 -u root -- python3 -u $serverPath"
 Start-Sleep -Seconds 1
}
$srrgFlow='mapping-srrg-'+$(if($Landmarks){'landmark-'}else{''})+$Scene
$presentationArgs=@{Flow=$srrgFlow;RepoRoot=$RepoRoot;PresentationRoot=$PresentationRoot;Duration=$Duration;Record=$true}
if(-not $Keyboard){$presentationArgs.Auto=$true}
& "$PSScriptRoot/presentation.ps1" @presentationArgs
$marker=Get-Content "$RepoRoot/.cache/presentation/$srrgFlow-latest.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$run=[IO.Path]::GetFullPath($marker.path)
$deadline=(Get-Date).AddSeconds(30)
while(-not (Test-Path "$run/session-stopped.json")){
 if((Get-Date)-gt $deadline){throw "Native shutdown did not finish: $run"}
 Start-Sleep -Milliseconds 200
}
$stop=Get-Content "$run/session-stopped.json" -Raw | ConvertFrom-Json
if($stop.exit_code -ne 0 -or -not (Test-Path "$run/srrg-finished.json")){throw "SRRG failed; evidence retained at $run"}
$runw='/mnt/'+$run.Substring(0,1).ToLower()+'/'+$run.Substring(3).Replace('\','/')
& wsl.exe -d Ubuntu-24.04 -u root -- python3 "$rw/src/scripts/presentation/srrg/evaluate.py" $runw | Out-Null
if($LASTEXITCODE -ne 0){throw "SRRG scoring failed; inspect $run"}
& wsl.exe -d Ubuntu-24.04 -u root -- python3 "$rw/src/scripts/presentation/srrg/export_grid.py" $runw | Out-Null
if($LASTEXITCODE -ne 0){throw "SRRG occupancy export failed; inspect $run"}
if($Scene -eq 'static'){
 if(-not (Test-Path "$run/prior.g2o")){throw 'Native static prior export missing'}
 [IO.File]::WriteAllText("$RepoRoot/.cache/presentation/srrg-static-prior-latest.json",(@{path=$runw;source_run=$run;scope='Actual native author static-A graph and clouds, saved by the live worker'} | ConvertTo-Json))
}
Write-Host "SRRG mapping completed: $run"
Write-Host "Map scores: $run/srrg-quality.json ; manual-localization maps: $run/maps"
