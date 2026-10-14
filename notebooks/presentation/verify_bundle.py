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
from experiment_tools import expected_media


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
    assert all("RUN_LIVE = False" in c.source for c in codes
               if "manual-live-launch" in c.metadata.get("tags", []))
    assert all("RUN_REFINEMENT = False" in c.source for c in codes if "RUN_REFINEMENT" in c.source)
    notebook_urls = []
    plots = root / ".cache" / "notebook-review"
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
    expected = expected_media()
    relative_media = []
    for url in notebook_urls:
        assert url.startswith("/files/")
        relative = unquote(url[len("/files/"):])
        assert (root / relative).is_file(), url
        assert relative.startswith("evidence/"), url
        relative_media.append(relative[len("evidence/"):])
    assert len(relative_media) == len(set(relative_media))
    assert set(relative_media) == expected, (set(relative_media) ^ expected)
    html = (root / f"{name}.html").read_text(encoding="utf-8")
    offline_urls = re.findall(r'<video[^>]*src="([^"]+)"', html)
    assert len(offline_urls) == len(notebook_urls)
    for url in offline_urls:
        assert not urlsplit(url).scheme and not url.startswith("/")
        assert (root / unquote(url)).is_file(), url
    sources = "\n".join(c.source for c in nb.cells if c.cell_type == "markdown")
    anchors = re.findall(r'<a id="([^"]+)"', sources)
    assert len(anchors) == len(set(anchors))
    for target in re.findall(r'\]\(#([^)]+)\)', sources):
        assert target in anchors, target
        assert f'id="{target}"' in html, target
    manifest = json.loads((root / "bundle-manifest.json").read_text(encoding="utf-8"))
    for relative, item in manifest["files"].items():
        path = root / relative
        assert path.stat().st_size == item["bytes"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], path
    print(f"Validated {len(codes)} executed cells, {len(notebook_urls)} video links, "
          f"{png_count} plots and {len(manifest['files'])} frozen evidence files.")
    if args.server:
        runtime = Path.home() / "AppData" / "Roaming" / "jupyter" / "runtime"
        servers = [json.loads(p.read_text(encoding="utf-8")) for p in
                   sorted(runtime.glob("jpserver-*.json"), key=lambda p: p.stat().st_mtime)]
        target = [s for s in servers if Path(s["root_dir"]).resolve() == root]
        assert target, "The one-click server is not running"
        s = target[-1]
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        # Never print the authentication token.
        def request(path, *, media=False):
            req = urllib.request.Request(s["url"].rstrip("/") + path,
                                         headers={"Authorization": "token " + s["token"]})
            if media:
                req.add_header("Range", "bytes=0-255")
            with opener.open(req, timeout=20) as response:
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
        print(f"One-click Jupyter server: Notebook, dedicated kernel and all {len(notebook_urls)} MP4 range requests passed.")


if __name__ == "__main__":
    main()
