#!/usr/bin/env bash
# AdaM_MCL reproduction harness -- stage the generated dataset on the WSL
# filesystem. The released loaders read one PNG per sample per iteration over
# the 9p /mnt/d mount, which dominates the training step; the directory layout
# is unchanged, only Dataset/simulation becomes a symlink to an ext4 copy.
set -euo pipefail

CODE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STAGE="${ADAM_STAGE:-$HOME/adam-dataset}"

cd "$CODE_DIR/.."
mkdir -p "$STAGE"
if [ -L Dataset/simulation ]; then
  echo "already staged: $(readlink -f Dataset/simulation)"
  exit 0
fi
cp -a Dataset/simulation "$STAGE/simulation"
rm -rf Dataset/simulation
ln -s "$STAGE/simulation" Dataset/simulation
echo "staged Dataset/simulation -> $(readlink -f Dataset/simulation)"
du -sh "$STAGE/simulation"
