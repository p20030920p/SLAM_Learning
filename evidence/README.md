# Execution evidence

`swap-manifest.json` records temporary task-owned swap and its resource scope. Memory failures retain kernel/systemd diagnostics and excluded partial-output hashes. `runs/room0-frontend-playback-02/media.json` records a 400-frame, 40-second saved RGB/SAM playback; its source manifest binds all 400 RGB frames and rechecks all 400 validated visualizations. The local MP4 is not an interactive-window recording or a semantic-accuracy result.

`videos/conceptgraphs-room0-original-window.mp4` is a separate, direct 60-second capture of the unchanged author Open3D viewer. Its window identity, source map, command, hash and inspected frames are in `runs/conceptgraphs-room0-original-window-01/`; `gui-actions.json` records successful controls and visual QA. The compact GUI clip is included in Git. The 24 MB frontend playback remains local.

These small files are copied from new executions in `/home/qzl/projects/SLAM_Author_Originals`, not from the main branch's previous runs.

`runs/dufomap-table4-ablation-01/` contains the five documented parameter settings, original PCL exports and original scoring logs. All 15 SA/DA/AA values match Table IV at two decimals; `figures/dufomap-table4.json` verifies this against the recorded log hash. No runtime comparison is claimed.

`benchmark-qualitative-manifest.json` records the CRC/checksums for the unlabeled campus/twofloor releases. `runs/dufomap-released-qualitative-01/` records successful original DUFOMap runs on all 18/3305 scans, plus streaming geometry validation. These datasets have no GT and are excluded from accuracy tables.

`kitti-selected-manifest.json` records 333 original point-cloud ZIP members, matching label counts, calibration and both pose sources. `kitti-point-prefetch.json` independently records the same 333 local SHA-256 digests; all agree. Only selected point-cloud members were downloaded, each checked against its original ZIP CRC; no whole-84.8GB-archive hash is claimed. Label/calibration/pose ZIPs passed full CRC tests.

`runs/kitti-author-selected-02/` contains current author preprocessing, default DUFOMap/BeautyMap and three XY cell sizes on 01/02, original exports and original scores. `runs/kitti-protocol-comparison-01/` documents differences from the older released 00 input; these new runs are [reported separately](../docs/KITTI_SELECTED_RESULTS.zh-CN.md) and do not match the paper's printed precision.

`runs/kitti-historical-protocol-01/` separately executes the author-documented `161b555` historical preprocessing/GT/export/scoring. Only 00 has a released-input comparison; the initial validation's zero comparison counters for 01/02 mean untested, because those releases are unavailable. `runs/beautymap-table3-historical-01/` rechecks completed exports and runs the original current HA scorer: all nine SA/DA/HA values match BeautyMap Table III at two decimals. [Protocol and results](../docs/KITTI_PAPER_PROTOCOL.zh-CN.md).

`runs/dufo-python-output-audit-01/` contains the unchanged author Python raw-point entry and hash-verified reuse of its completed voxel entry, both d_p=2. Original PCL/scoring runs at 0.05m and additional 0.10m separate representation sensitivity from deletion claims. `runs/chamferdist-cuda-probe-01/` confirms the repaired binary on a real tiny GPU KNN operation; this is not a semantic score.

Each `record.json` contains the actual command, source commit, exit status, elapsed time, source cleanliness and artifact hashes. `artifact-manifest.json` binds local dataset and point-cloud outputs to SHA-256. A successful exit alone is not a full-reproduction claim. Logs include failed compiler/dependency attempts where collected; large datasets, weights and point clouds remain local.

`configuration-diffs/` preserves relative paths for the author-required evaluation settings and separately labeled environment/SAM microbatch compatibility adjustments. Source snapshots with `running` or `interrupted` status are not completed results. `figures/lidar-scores.json` copies the printed original evaluator numbers, with its log hash. `sam-batch-comparison.json` checks only the 26 common saved frames; it does not establish full-sequence equivalence. The scope and limitations are described in [the status document](../docs/STATUS.zh-CN.md).
