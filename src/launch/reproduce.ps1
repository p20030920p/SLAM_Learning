param(
    [switch]$Smoke,
    [switch]$Help
)
$ErrorActionPreference = 'Stop'
if ($Help) {
    Write-Output 'Usage: powershell -File src/launch/reproduce.ps1 [-Smoke]'
    exit 0
}
$studyRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'uv is required; see docs/guides/REPRODUCE.md' }
$studyFrames = if ($Smoke) { 10 } else { 0 }
function Invoke-Study {
    param([string[]]$StudyArguments)
    & uv run --project src --frozen slam-study @StudyArguments
    if ($LASTEXITCODE -ne 0) { throw "slam-study exited with code $LASTEXITCODE" }
}
Push-Location -LiteralPath $studyRoot
try {
    Invoke-Study -StudyArguments @('fetch')
    Invoke-Study -StudyArguments @('run', '--method', 'dufomap', '--frames', "$studyFrames")
    Invoke-Study -StudyArguments @('run', '--method', 'beautymap', '--frames', "$studyFrames")
    Invoke-Study -StudyArguments @('report', '--runs', 'results/runs', '--output', 'results/local-reproduction.md')
    Invoke-Study -StudyArguments @('report', '--runs', 'results/runs', '--output', 'results/local-reproduction.zh-CN.md', '--lang', 'zh')
    Write-Output 'Reproduction recorded. This command does not run exploratory hypothesis experiments.'
} finally {
    Pop-Location
}
