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

The renderer offers `--cjk-font /path/to/licensed-font.ttc` for an embedded TrueType subset; the delivered PDFs use Microsoft YaHei from this Windows installation and record its hash. Without it, the built-in STSong CID fallback is used. Fonts are not redistributed in Git. English pages also use the CJK font for Chinese edition links.

**Coordinate audit:** ConceptGraphs' default loader normalizes the poses returned by `__getitem__`, but the executed batch mapper deliberately reads absolute `dataset.poses` instead. Its 39 saved camera matrices (observations 1–39; initialization at 0 has no snapshot) are checked against supplied poses before rendering. The original `center_world_m` therefore already uses Replica world coordinates; no additional first-frame transformation is applied. HOV-SG also reads absolute trajectory matrices. Following the actual entry point matters more than a loader default.

Future physical clips should add the raw sensor view and independent event/annotation view. Keep the camera and axes fixed, show a session identifier and disclose supply/estimate/reference pose sources. Recording is the last stage of a verified run, not evidence that every paper task was reproduced.

## Complete local execution recordings

Four additional **live terminal recordings** now cover command startup, author execution, visible exit code 0 and a closing hold. They are normal elapsed-time captures of a private Linux terminal; the GIFs above remain map-output replays. These full recordings show execution logs, not a live 3D mapping GUI or hardware navigation.

| Method | Video duration (s) | Author command (s) |
| --- | ---: | ---: |
| DUFOMap | 36.6 | 32.631 |
| BeautyMap | 42.0 | 38.164 |
| ConceptGraphs, 40 observations | 256.6 | 253.019 |
| HOV-SG, 8 observations | 168.8 | 165.134 |

On the collection machine, open `D:/workspace/be2/SLAM_Recordings/2026-10-08/VIDEO_INDEX.md`. Every indexed folder includes `full-session.mp4`, `terminal.raw`, `terminal.time`, the command, exit/recording JSON and start/middle/end review PNGs. The videos stay local, outside Git. [Portable evidence and native run records](../results/reference/full-recordings/record.json) bind the video bytes, transcripts and reviewed frames. Rejected preliminary captures remain local and are excluded from the index.

`scripts/record_session.py` uses Xvfb + xterm + util-linux `script`, a random Xauthority cookie and monotonic frame scheduling. It waits for video capture before releasing the command, flushes the PTY, watches only the selected method's new logs, decodes the entire movie and checks duration and nonblank review frames. It captures its private screen rather than the user's desktop. Large videos are imported as local-only artifacts by `scripts/import_full_recordings.py`.

```bash
sudo apt-get install xvfb xterm xauth ffmpeg util-linux
# Pillow with XCB support is required in this recording environment.
.venv/bin/python scripts/record_session.py \
  --output /mnt/d/workspace/be2/SLAM_Recordings/new-dufomap \
  -- .venv/bin/python -m slam_learning.cli run --method dufomap
# Use -- .venv-semantic/bin/python scripts/run_conceptgraphs.py for ConceptGraphs;
# use -- .venv-hovsg/bin/python scripts/run_hovsg.py for HOV-SG.
```
