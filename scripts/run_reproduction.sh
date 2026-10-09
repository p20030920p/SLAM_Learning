#!/usr/bin/env bash
# Compatibility entry for existing runbooks and command histories.
set -euo pipefail
STUDY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
exec bash "$STUDY_ROOT/launch/reproduce.sh" "$@"
