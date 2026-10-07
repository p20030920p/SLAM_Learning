"""Install the checksum-bound author-recommended PyTorch3D conda binary locally."""
from __future__ import annotations

import hashlib
import json
import subprocess
import tarfile
import urllib.request
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "configs/semantic.json").read_text())
    path = root / ".cache/pytorch3d-0.7.4.tar.bz2"
    if not path.exists():
        with urllib.request.urlopen(config["pytorch3d_binary"], timeout=120) as response:
            with path.open("wb") as f:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    f.write(block)
    if hashlib.sha256(path.read_bytes()).hexdigest() != config["pytorch3d_binary_sha256"]:
        raise ValueError("PyTorch3D binary checksum mismatch")
    interpreter = root / ".venv-semantic/bin/python"
    base = Path(subprocess.check_output([str(interpreter), "-c",
                "import sysconfig; print(sysconfig.get_path('purelib'))"], text=True).strip()).resolve()
    if not base.is_relative_to((root / ".venv-semantic").resolve()):
        raise ValueError("Refuse to install binary outside the project semantic environment")
    prefix = "lib/python3.10/site-packages/"
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.startswith(prefix):
                continue
            target = (base / member.name[len(prefix):]).resolve()
            if not target.is_relative_to(base):
                raise ValueError("Binary archive path escapes environment")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    subprocess.run([str(interpreter), "-c", "import torch; from pytorch3d.ops import box3d_overlap; print('PyTorch3D ready')"],
                   check=True)


if __name__ == "__main__":
    main()
