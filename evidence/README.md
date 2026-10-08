# Execution evidence

`swap-manifest.json` records temporary task-owned swap and its resource scope. Memory failures retain kernel/systemd diagnostics and excluded partial-output hashes. `runs/room0-frontend-playback-02/media.json` records a 400-frame, 40-second saved RGB/SAM playback; its source manifest binds all 400 RGB frames and rechecks all 400 validated visualizations. The local MP4 is not an interactive-window recording or a semantic-accuracy result.

`videos/conceptgraphs-room0-original-window.mp4` is a separate, direct 60-second capture of the unchanged author Open3D viewer. Its window identity, source map, command, hash and inspected frames are in `runs/conceptgraphs-room0-original-window-01/`; `gui-actions.json` records successful controls and visual QA. The compact GUI clip is included in Git. The 24 MB frontend playback remains local.

These small files are copied from new executions in `/home/qzl/projects/SLAM_Author_Originals`, not from the main branch's previous runs.

Each `record.json` contains the actual command, source commit, exit status, elapsed time, source cleanliness and artifact hashes. `artifact-manifest.json` binds local dataset and point-cloud outputs to SHA-256. A successful exit alone is not a full-reproduction claim. Logs include failed compiler/dependency attempts where collected; large datasets, weights and point clouds remain local.

`configuration-diffs/` preserves relative paths for the author-required evaluation settings and separately labeled environment/SAM microbatch compatibility adjustments. Source snapshots with `running` or `interrupted` status are not completed results. `figures/lidar-scores.json` copies the printed original evaluator numbers, with its log hash. `sam-batch-comparison.json` checks only the 26 common saved frames; it does not establish full-sequence equivalence. The scope and limitations are described in [the status document](../docs/STATUS.zh-CN.md).
