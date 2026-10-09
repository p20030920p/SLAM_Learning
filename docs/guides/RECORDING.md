# Visualization and recording scope

English | [中文](RECORDING.zh-CN.md)

## Actual RViz graphical windows

These clips capture a running RViz 3D window, not just terminal text. An evidence panel identifies method, stage, provenance and observations; RViz shows real saved point clouds. **This is measured-output inspection, not new inference or a live mapping performance demonstration.**

| Method | Visible content | Inspect | Duration |
| --- | --- | --- | ---: |
| DUFOMap | Same point sample from the first 21 source scans; input/removed/retained classifications, with GT coloring only | [MP4](../media/rviz/dufomap.mp4) · [Frame](../media/rviz/dufomap.png) | 34.4 s |
| BeautyMap | Input/removed/retained classifications under the same spatial view | [MP4](../media/rviz/beautymap.mp4) · [Frame](../media/rviz/beautymap.png) | 34.4 s |
| ConceptGraphs | Author-saved mapping snapshots at observations 1/10/20/30/39, followed by four final-map query candidates and native SAM observations | [MP4](../media/rviz/conceptgraphs.mp4) · [Frame](../media/rviz/conceptgraphs.png) | 69.6 s |
| HOV-SG | Final segment feature map, four text-query candidates and input observations | [MP4](../media/rviz/hovsg.mp4) · [Frame](../media/rviz/hovsg.png) | 34.4 s |

Each uses a private Xvfb screen and software OpenGL, avoiding CUDA contention. Actual graphical pixels are captured at 5 fps on a monotonic clock; H.264 is fully decoded and every display stage is inspected. Display thinning does not alter previous full-data scores. Replica `(x,y,z)→(x,z,-y)` is a display-only transform; stored maps are unchanged. Orange candidates are not annotated correctness.

[Sources, per-stage review frames, logs and source snapshots](../../results/reference/visual-review/record.json) bind published bytes. `prepare_visual_review.py` verifies native outputs; `view_measured_rviz.py` publishes ROS2 PointCloud2 and displays observations; `record_visual_review.sh` opens actual RViz. HOV-SG final geometry is not presented as progressive mapping. None of these author entry points runs Gazebo.

## Complete local execution recordings

Four separate complete xterm/PTY recordings span fresh command startup through exit 0: DUFOMap 36.6 s, BeautyMap 42.0 s, ConceptGraphs 256.6 s and HOV-SG 168.8 s. They document command execution, primarily through terminal content. Large originals stay local; [portable evidence](../../results/reference/full-recordings/record.json) retains commands, logs, timing and hashes.

`record_session.py` creates private Xvfb/xterm, releases the actual command after capture starts and records pixels on a monotonic clock. The older clips did not open a map GUI; these graphical clips capture RViz as a real child process on that private screen. Neither recording duration is an FPS measure or a controlled runtime benchmark.

## Homepage replays and PDFs

The original per-paper GIFs/MP4s are rendered replays of measured final maps. LiDAR input/removed/retained views use original PCL classifications; semantic panels combine native observations, final maps and candidates. ConceptGraphs coordinates are checked against its actual absolute-pose entrypoint and 39 saved camera matrices, without applying the first-frame transform again.

The homepage now uses [native-size GIFs](../../results/reference/media-previews-v2/record.json): 1200/1280 pixels wide, a 256-color palette, and 5 fps for recorded viewers. The ConceptGraphs RViz GIF samples all nine stages in chronological order; the MP4 remains complete. [Before/after](../../results/reference/media-previews-v2/before-after.png).

Regenerate with existing `ffmpeg` and `ffprobe`; add `--wsl Ubuntu-22.04` on Windows. Sources are hash-checked and an existing output directory is rejected.

```bash
uv run --project src python src/scripts/media/export_media_previews.py \
  --author-video /path/to/conceptgraphs-room0-original-window.mp4 \
  --output results/runs/my-previews
```

Sixteen bilingual PDFs retain their own generation snapshots, byte hashes and page-review evidence. Current prose edits do not silently overwrite historical reports. [Paper media and reports](../papers/README.md) · [Paired report review](../../results/reference/paired-report-review/record.json). Detailed manual recording, installation and host-operation notes stay in personal local documentation.

The room1 delayed-correction study adds three complete local terminal recordings: frontend 82.4 s, 35-cell suite 509.4 s and six post-hoc controls 189.8 s. The last recording held one frame; all MP4s were fully decoded. [Hashes, commands, logs and review frames](../../results/reference/delayed-recordings/record.json) bind them to the corresponding scientific records. These are execution recordings; the separate RViz clips above inspect saved baseline outputs. [Study results](../research/DELAYED_RESULTS.md).
