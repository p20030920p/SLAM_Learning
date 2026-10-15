param(
 [string]$RepoRoot='D:\workspace\be2\slam_learning_updated',
 [string]$Python='D:\workspace\be2\SLAM_Learning\.venv\Scripts\python.exe',
 [string]$Suite='results/reference/own-hypotheses-20261016',
 [switch]$Resume
)
& "$PSScriptRoot/record-own-hypotheses.ps1" -RepoRoot $RepoRoot -Python $Python -Suite $Suite -Resume:$Resume
