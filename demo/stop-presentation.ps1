param([string]$RepoRoot='D:\workspace\be2\slam_learning_updated')
Get-ChildItem -LiteralPath (Join-Path $RepoRoot 'results/runs/presentation') -Directory | ForEach-Object {
 if((Test-Path (Join-Path $_.FullName 'ready.json')) -and -not (Test-Path (Join-Path $_.FullName 'finished.json')) -and -not (Test-Path (Join-Path $_.FullName 'failed.json'))){
  [IO.File]::WriteAllText((Join-Path $_.FullName 'STOP'),'User requested a graceful presentation stop')
 }
}
