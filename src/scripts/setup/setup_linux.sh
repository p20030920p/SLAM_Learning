#!/usr/bin/env bash
set -euo pipefail
STUDY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$STUDY_ROOT"
command -v git >/dev/null || { echo 'Install Git first.' >&2; exit 1; }
command -v uv >/dev/null || { echo 'Install uv first; see docs/guides/REPRODUCE.md.' >&2; exit 1; }
case "$STUDY_ROOT" in /mnt/*) echo 'For faster Linux I/O, use a checkout under ~/projects rather than /mnt/.' ;; esac
uv sync --project src --frozen --python 3.10 --extra methods --extra dev
uv run --project src slam-study doctor
uv run --project src pytest -q src/tests
uv run --project src python src/scripts/evidence/verify_evidence.py
uv run --project src python src/scripts/evidence/check_docs.py
echo 'Environment checked. Run bash src/scripts/run_reproduction.sh for author-method reproduction.'
