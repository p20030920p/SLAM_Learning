# AdaM_MCL reproduction harness

Scripts that drove the released [AdaM_MCL](https://github.com/Runjian-Chen/AdaM_MCL/tree/e8aedd2bae03816aabd5300e5ca2fe181b39d830) code for the run recorded in
[../runs/adam-mcl-wsl/record.json](../runs/adam-mcl-wsl/record.json). They are kept here so the published numbers can be re-derived; none of them replaces an
upstream entry point.

| Script | Role |
| --- | --- |
| `make_maps.py` | Authors the 128-cell occupancy plans the released data generator expects (the upstream `Dataset/` directory ships empty) |
| `gen_train_data.sh` | Runs the released `Data_processor/synthetic_dataset.py` over those plans |
| `gen_test_data.sh` | Runs the released `src/Generate_Path.py` to build the evaluation sequences |
| `stage_dataset.sh` | Copies the generated dataset onto the WSL filesystem, which the released per-sample PNG loaders read far faster than the 9p mount |
| `train.sh` | Runs the released `Main.py --operation train` |
| `live_eval.py` | Runs the released `Main.py --operation test_MCL` and shows a live dashboard of that program's own output |
| `run_session.sh` | The command recorded by `src/scripts/media/record_session.py` |
| `run_recorded_session.sh` | Wraps the above in the repository's session recorder |
| `publish_recording.py` | Publishes the recorded directory (renames the video, compresses the PTY transcript, removes the X cookie) |
| `publish_evidence.py` | Writes `record.json`, `metrics.json`, `worker.json` and `run.log`, then indexes the reference directory |
| `make_preview.py` | Builds `media/preview.gif` and `media/timing.json` from the recording |
| `sequence_facts.py` | Reports the teleport index of each evaluation sequence |
| `show_teleport.py` | Prints the ground-truth poses either side of the teleport in the published sequence |
| `show_metrics.py` | Prints the summary and per-trial rows of `runs/adam-mcl-wsl/metrics.json` |
| `probe_trajectory.py` | Prints the released per-update error trajectory of a trial |

One normalisation was applied when the released output was published, and it changes no byte of any file: the trial directories the released interface names
with a colon-bearing timestamp use a dash instead, because a colon cannot be checked out on Windows. Every change made to upstream files is in
[../runs/adam-mcl-wsl/compatibility.patch](../runs/adam-mcl-wsl/compatibility.patch).
