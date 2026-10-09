# Hardware tests and acceptance targets

English | [中文](TEST_PLAN.zh-CN.md)

These are initial project targets, not achieved scores or manufacturer guarantees. Test sensors, then odometry, then mapping; retain all failures and full recordings.

## 1. Sensor checks

Use confirmed-fixed 60-second sessions, textured matte geometry at 1–3 m and independent distance references. Record lighting, emitter, cables and operator declaration.

| Check | Initial target |
| --- | --- |
| Raw camera streams | 29–31 fps, <1% sequence loss, no backwards time; steady state has no >100 ms stall |
| Matte-plane ROI | >90% valid depth; at 2 m, temporal median-depth SD <10 mm |
| Independent 1/2/3 m measurement | Bias <max(3 cm, distance×2%), with reference uncertainty |
| L2 packets | CRC ideally zero; rejection/loss each <0.1%; no backwards time |
| Clock before LIO/fusion | Explain current host/device ratio≈2; target <1000 ppm and controlled p95 residual <5 ms |

Host receipt jitter is not hardware synchronization. IMU units/axes must be established before applying gravity/bias targets.

## 2. Odometry and motion

Fixed tests target <5 cm maximum translation, <2° rotation and >95% usable tracking. KISS LOST is null. Replay identical raw inputs for method comparison; different live sessions are not matched inputs.

After fixed tests pass, separately test a measured 2 m straight motion, about 90° rotation, a 5–10 m loop and adverse texture/occlusion. Initial endpoint targets are <5% length error, <5° return orientation and <20 cm loop endpoint error. Repeat and record uncertainty.

ATE/RPE remain empty without independent trajectories, timing and alignment conventions. Tape measurements, another SLAM and IMU are not full trajectory ground truth.

## 3. Mapping and semantics

Fix the sensor and record static, occluded, removed-visible and 30 cm moved-object events. Each 80-second session uses 0–20 s baseline, 20–25 action, 25–60 hold and 60–80 restore; record actual times. Use ≥3 validation and ≥5 held-out sessions per event after freezing parameters.

Measure SA/DA, false deletion, change recall, identity fragments/mixes, queries, coordinate error, latency and memory. Initial targets include <5% visible-static false deletion, >80% visible-removal recall and <10 cm independent surface-anchor error. These are future tests; real semantic cores remain unexecuted.

Current input-loader checks are 8/8, not semantic success. L2 fixed drift and strict camera coverage still have failures. [Current results](POSTFALL_LOWLIGHT.md) · [Integration](MAIN_INTEGRATION.md) · [Full action/metric specification](TEST_PLAN.zh-CN.md).

## 4. Deliver and review

Keep raw hashes, calibration/pose provenance, events, full LIVE or explicitly OFFLINE videos, input/output denominators and failures. Integrate selected modules through a main-based isolated branch, regression tests, PR and explicit owner approval; do not merge this orphan history wholesale.
