# Does a late pose correction need association replay

[中文](DELAYED_PROTOCOL.zh-CN.md)

This experiment tests a prerequisite of candidate H1: whether correcting geometry while retaining historical association decisions leaves a target loss that full reassociation can recover. It does not test a bounded-memory method, estimated uncertainty, physical motion, navigation or a shared four-paper bottleneck.

## 1. Freeze and independent reference

The [machine-readable design](../configs/delayed_pose.json) was committed before downloading this study's new Replica `room1` subset. Mapping uses source frames 0,25,...375. Reference views 12,137,262,387 never enter mapping or frontend extraction. Raw reference RGB-D supplies instance polygons and partial visible surfaces; predicted masks do not define truth. Annotation identity, exclusions, queries and hashes must be sealed before SAM/CLIP or mapper results are inspected. AI-assisted polygons still require independent human review; until then all target conclusions remain provisional.

The dataset uses the NICE-SLAM rendered Replica archive; calibration and camera-to-world poses follow the pinned ConceptGraphs Replica loader. RGB-D members are CRC-checked and SHA-256 recorded. A source manifest and a separate annotation freeze record bind the exact inputs. A new scene is useful evidence separation, not a claim of independent multi-scene confirmation. Existing `room0` results informed all design choices.

## 2. Intervention and arms

The first eight observations receive a world-x random-walk translation normalized to 10 or 30 cm prefix RMS, first pose fixed, seeds 417/518/619. At observation eight the complete exact historical correction becomes available. Subsequent observations use supplied exact poses. These are controlled oracle pose interventions, not measurements of real SLAM error. No rotation is injected.

| Arm | Before correction | At correction |
| --- | --- | --- |
| Native | Author association, threshold 1.2 | Leave fused history unchanged; use corrected new observations |
| Threshold | Threshold 1.0, selected from prior room0 exploration | Same behavior as native |
| Visibility | Threshold 1.0 plus projected visible support | Same behavior as native |
| Fixed association | Native threshold 1.2 with a diagnostic decision trace | Rebuild all prefix geometry at corrected poses, forcing the original association sequence and retaining semantic memberships |
| Oracle replay | Native threshold 1.2 | Discard prefix state and rerun the entire prefix at corrected poses, including reassociation |

The visibility guard permits a merge only when the candidate object's current-view projection has at least 16 unique depth-consistent pixels and at least 20% lie in the detection mask, with 10 cm depth tolerance. Rejected merges create a new object; they do not delete detections. This baseline can fragment identities, which must be reported.

The fixed-association control is deliberately strong: it has every original observation and oracle corrected pose. It rebuilds geometry through the same add/merge sequence, rather than shifting one fused centroid. Before the eight-frame correction there is no scheduled native denoise/filter/object-merge event (their intervals exceed the prefix). If pose-dependent detection acceptance changes, record that change and do not label the difference a pure association effect. Replay and fixed-association controls are diagnostic full-history oracles, not the proposed 16-observation/512 MiB implementation.

Use the pinned author frontend and mapping primitives. Freeze masks and CLIP features once; mapping never reruns them. Reset point-construction RNG per source observation in every arm, including the instrumented native control, so a different association path does not change future jitter samples. Disclose this execution adaptation. Verify the extracted loop against the pinned batch mapper at zero error; verify native, fixed-association and replay agree at zero error. A failed gate invalidates the causal comparison until repaired and logged.

## 3. Readouts and decision

Evaluate immediately after correction and after four/eight further observations. Keep partial-surface coverage, visible precision, instance recovery, annotated-instance mixing, fragmentation, restricted category top-1 and target-surface coordinate distance separate. Reference frames are excluded from mapping, but labels still cover only selected visible instances; an unlabelled valid retrieval is not automatically an open-world false positive. Observation counts are not wall-clock update latency.

The primary contrast is oracle replay versus fixed-association geometry. Require a recovery/identity or restricted-query improvement in at least two of three seeds at one RMS level, with passing zero-error gates, before pursuing a bounded replay prototype. Coordinate-distance improvement alone is insufficient. If cheap guards reach the same recovery, narrow the motivation. If full reassociation adds no recovery, do not implement H1 on the strength of this test. Report all seeds and both RMS levels, including ties and adverse results; seed spread is not a confidence interval.

The scene is static, so this experiment cannot establish true-change recall, dynamic target staleness or a matched risk–recall–delay frontier. Positive evidence only motivates the next test with physical change and delayed estimated pose correction. Negative evidence is a reason to stop or revise H1, not select a different favorable scene silently.

<a id="reproduction-status"></a>

## 4. Reproduction status

Completed: 35 primary cells and seven native parity gates. A separate six-cell post-hoc support control follows the primary study. [Results and revised decision](DELAYED_RESULTS.md) are separate from this design; the original configuration and annotation freeze remain unchanged. Large inputs and maps stay local; executed source versions and the failed setup attempt are retained.

For a fresh native rerun, first complete the ConceptGraphs baseline in the [reproduction entry](REPRODUCE.md). Set `native_run` to its actual run folder containing `author-code`; set `weights` to the verified SAM/CLIP cache. From the repository root in Linux/WSL, choose a new empty `study_dir`. Do not overwrite existing evidence.

```bash
study_dir="$PWD/results/runs/delayed-local-v2"
native_run="$PWD/results/runs/conceptgraphs-YOUR_RUN_ID"
weights="$PWD/.cache/semantic-weights"
.venv-semantic/bin/python scripts/fetch_delayed_scene.py --protocol configs/delayed_pose.json --output "$study_dir/data"
.venv-semantic/bin/python scripts/seal_delayed_annotations.py --protocol configs/delayed_pose.json --annotations annotations/room1/targets.json --data "$study_dir/data" --output "$study_dir/annotation"
```

Inspect the four overlays against raw RGB-D before sealing. An unchanged-file reproduction can use the published polygons; a human-reviewed revision needs a new annotation/protocol version and should preserve the old one. After review:

```bash
.venv-semantic/bin/python scripts/seal_delayed_annotations.py --protocol configs/delayed_pose.json --annotations annotations/room1/targets.json --data "$study_dir/data" --output "$study_dir/annotation" --seal
.venv-semantic/bin/python scripts/prepare_delayed_frontend.py --protocol configs/delayed_pose.json --annotations annotations/room1/targets.json --freeze "$study_dir/annotation/freeze.json" --data "$study_dir/data" --native-source "$native_run" --weights "$weights" --output "$study_dir/frontend"
.venv-semantic/bin/python scripts/run_delayed_correction.py --frontend "$study_dir/frontend" --data "$study_dir/data" --freeze "$study_dir/annotation/freeze.json" --weights "$weights" --output "$study_dir/primary"
.venv/bin/python scripts/analyze_delayed_correction.py "$study_dir/primary" --annotations-review "$study_dir/annotation" --frontend "$study_dir/frontend" --output "$study_dir/primary-export"
.venv/bin/python scripts/verify_delayed_evidence.py --record "$study_dir/primary-export/record.json" --raw-suite "$study_dir/primary"
.venv-semantic/bin/python scripts/run_delayed_correction.py --frontend "$study_dir/frontend" --data "$study_dir/data" --freeze "$study_dir/annotation/freeze.json" --weights "$weights" --output "$study_dir/support-control" --support-control-from "$study_dir/primary"
.venv/bin/python scripts/analyze_delayed_support.py "$study_dir/support-control" --primary "$study_dir/primary-export" --output "$study_dir/support-export"
.venv/bin/python scripts/verify_delayed_support.py --record "$study_dir/support-export/record.json" --primary "$study_dir/primary-export" --raw-followup "$study_dir/support-control"
```

The CPU commands use the separate installed project environment. Wrap native commands with `scripts/record_session.py` to retain a complete real-time terminal video; the actual invocation and recording metadata are archived in the [new study](DELAYED_RESULTS.md). Frontend extraction and the mapper are distinct recording stages. These scripts run sequentially and leave prior study outputs untouched.

Sources: [NICE-SLAM data preparation](https://github.com/cvg/nice-slam#replica-1), [pinned ConceptGraphs batch mapper](https://github.com/concept-graphs/concept-graphs/blob/93277a02bd89171f8121e84203121cf7af9ebb5d/conceptgraph/slam/cfslam_pipeline_batch.py).
