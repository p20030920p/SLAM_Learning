# Per-paper recordings and reports

English | [中文](RECORDING.zh-CN.md)

The convention follows the user's [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench) reference at `53324d40def0dd753b4a99021b8fe596955a1ecd`: one method has an MP4, a lightweight GIF preview and machine-readable metadata; the output is checked for completeness and blank panels. Its source is not copied.

These clips are **replays of measured author outputs**. LiDAR videos show final-map PCL labels across selected original scans. Semantic videos show native SAM observations beside the final map and query candidates. They are not recordings of live navigation, progressive online mapping, or algorithm FPS. No ground-truth label is supplied to the author pipelines.

```bash
# In the separate semantic environment; supply a full local run, not an exported record without its map.
uv pip install --python .venv-semantic/bin/python imageio-ffmpeg==0.6.0
.venv-semantic/bin/python scripts/render_paper_media.py dufomap results/runs/REPLAY_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py beautymap results/runs/REPLAY_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py conceptgraphs results/runs/CG_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py hovsg results/runs/HOV_ID/record.json
```

The renderer first verifies the source artifacts. H.264 clips decode completely; first/middle/last frame variance guards against blank output. `render.json` records selected source frames, fixed view, explicit coordinate conversion, query results, playback settings and source hashes. A human also checks posters and representative video frames. Export records before copying byte-identical assets to the homepage.

English and Chinese PDFs are generated from the paper cards and verified run summaries by `scripts/build_paper_pdfs.py`. They contain scope, native output, commands, measured numbers, limitations and the relation to the hypothesis. Render every PDF page and check layout; text extraction alone is insufficient. A media/PDF record binds all published bytes and inputs.

```bash
uv venv .venv-reports --python 3.10
uv pip install --python .venv-reports/bin/python -r environments/reports/requirements.txt
.venv-reports/bin/python scripts/build_paper_pdfs.py --publish
# Render every PDF page with Poppler; inspect images before exporting the record.
```

**Coordinate audit:** ConceptGraphs' default loader normalizes the poses returned by `__getitem__`, but the executed batch mapper deliberately reads absolute `dataset.poses` instead. Its 39 saved camera matrices (observations 1–39; initialization at 0 has no snapshot) are checked against supplied poses before rendering. The original `center_world_m` therefore already uses Replica world coordinates; no additional first-frame transformation is applied. HOV-SG also reads absolute trajectory matrices. Following the actual entry point matters more than a loader default.

Future physical clips should add the raw sensor view and independent event/annotation view. Keep the camera and axes fixed, show a session identifier and disclose supply/estimate/reference pose sources. Recording is the last stage of a verified run, not evidence that every paper task was reproduced.
