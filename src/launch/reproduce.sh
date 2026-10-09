#!/usr/bin/env bash
# Run the supplied-pose LiDAR reproduction through the stable CLI.
set -euo pipefail
STUDY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
case "${1:-}" in
    --help|-h) echo 'Usage: bash src/launch/reproduce.sh [--smoke]'; exit 0 ;;
    '') STUDY_FRAMES=0 ;;
    --smoke) STUDY_FRAMES=10 ;;
    *) echo 'Usage: bash src/launch/reproduce.sh [--smoke]' >&2; exit 2 ;;
esac
if [ "$#" -gt 1 ]; then echo 'Only --smoke is supported.' >&2; exit 2; fi
cd "$STUDY_ROOT"
uv run --project src --frozen slam-study fetch
uv run --project src --frozen slam-study run --method dufomap --frames "$STUDY_FRAMES"
uv run --project src --frozen slam-study run --method beautymap --frames "$STUDY_FRAMES"
uv run --project src --frozen slam-study report --runs results/runs --output results/local-reproduction.md
uv run --project src --frozen slam-study report --runs results/runs --output results/local-reproduction.zh-CN.md --lang zh
echo 'Reproduction recorded. This command does not run exploratory hypothesis experiments.'
