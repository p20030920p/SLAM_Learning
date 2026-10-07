#!/usr/bin/env bash
set -euo pipefail
STUDY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$STUDY_ROOT"
case "${1:-}" in
    '') STUDY_FRAMES=0 ;;
    --smoke) STUDY_FRAMES=10 ;;
    *) echo 'Usage: bash scripts/run_reproduction.sh [--smoke]' >&2; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then echo 'Only --smoke is supported.' >&2; exit 2; fi
uv run slam-study fetch
uv run slam-study run --method dufomap --frames "$STUDY_FRAMES"
uv run slam-study run --method beautymap --frames "$STUDY_FRAMES"
uv run slam-study report --runs results/runs --output results/local-reproduction.md
uv run slam-study report --runs results/runs --output results/local-reproduction.zh-CN.md --lang zh
echo 'Reproduction recorded. This command does not run exploratory hypothesis experiments.'
