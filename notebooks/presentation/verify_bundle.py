"""Validate exported notebooks, frozen copies and the running local Jupyter endpoints."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import nbformat
from nbformat.sign import NotebookNotary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path(r"F:\be2演讲\展示"))
    parser.add_argument("--server", action="store_true")
    args = parser.parse_args()
    root = args.directory.resolve()
    name = "SLAM_实验逐步展示"
    nb = nbformat.read(root / f"{name}.ipynb", as_version=4)
    nbformat.validate(nb)
    assert NotebookNotary().check_signature(nb), "Generated Notebook must be locally trusted"
    codes = [c for c in nb.cells if c.cell_type == "code"]
    assert all(c.execution_count is not None for c in codes)
    assert not any(o.output_type == "error" for c in codes for o in c.outputs)
    assert all("START_THIS_EXPERIMENT = False" in c.source for c in codes
               if "manual-live-launch" in c.metadata.get("tags", []))
    notebook_urls = []
    plots = Path(__file__).resolve().parents[2] / ".cache" / "notebook-review"
    plots.mkdir(parents=True, exist_ok=True)
    png_count = 0
    for i, c in enumerate(nb.cells):
        for output in c.get("outputs", []):
            data = output.get("data", {})
            markup = data.get("text/html", "")
            notebook_urls.extend(re.findall(r'<video[^>]*src="([^"]+)"', markup))
            if "可确认延迟" in markup:
                print("Recovery timing table:", re.sub(r"<[^>]*>", " | ", markup))
            if "image/png" in data:
                (plots / f"cell-{i:02d}.png").write_bytes(base64.b64decode(data["image/png"]))
                png_count += 1
    assert len(notebook_urls) == 19, notebook_urls
    for url in notebook_urls:
        assert url.startswith("/files/")
        assert (root / unquote(url[len("/files/"):])).is_file(), url
    html = (root / f"{name}.html").read_text(encoding="utf-8")
    offline_urls = re.findall(r'<video[^>]*src="([^"]+)"', html)
    assert len(offline_urls) == 19
    for url in offline_urls:
        assert not urlsplit(url).scheme and not url.startswith("/")
        assert (root / unquote(url)).is_file(), url
    manifest = json.loads((root / "bundle-manifest.json").read_text(encoding="utf-8"))
    for relative, item in manifest["files"].items():
        path = root / relative
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
    print(f"Validated {len(codes)} executed cells, {len(notebook_urls)} video links, "
          f"{png_count} plots and {len(manifest['files'])} frozen evidence files.")
    if args.server:
        runtime = Path.home() / "AppData" / "Roaming" / "jupyter" / "runtime"
        servers = [json.loads(p.read_text()) for p in runtime.glob("jpserver-*.json")]
        target = [s for s in servers if Path(s["root_dir"]).resolve() == root]
        assert target, "The one-click server is not running"
        s = target[-1]
        # Never print the authentication token.
        def request(path, *, media=False):
            req = urllib.request.Request(s["url"].rstrip("/") + path,
                                         headers={"Authorization": "token " + s["token"]})
            if media:
                req.add_header("Range", "bytes=0-255")
            with urllib.request.urlopen(req, timeout=20) as response:
                if media:
                    assert response.status == 206 and response.headers.get_content_type() == "video/mp4"
                    assert b"ftyp" in response.read(256)
                    return None
                return response.read()
        contents = json.loads(request("/api/contents/" + quote(f"{name}.ipynb")))
        assert contents["type"] == "notebook" and len(contents["content"]["cells"]) == len(nb.cells)
        kernels = json.loads(request("/api/kernelspecs"))
        assert "slam-presentation" in kernels["kernelspecs"]
        assert b"jupyter" in request("/lab/tree/" + quote(f"{name}.ipynb")).lower()
        for url in notebook_urls:
            request(url, media=True)
        print("One-click Jupyter server: Notebook, dedicated kernel and all 19 MP4 range requests passed.")


if __name__ == "__main__":
    main()
