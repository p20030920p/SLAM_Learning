# Live-entry execution checks

English | [中文](LIVE_VALIDATION.zh-CN.md)

Fifteen short sessions check Windows capture → loopback → WSL ROS2 → algorithm/RViz. They do not have frozen motion or independent trajectory truth. Successful startup is not a stationary/motion accuracy pass.

## 1. Executed modes

Raw camera/L2 previews, stereo, RGB-D, RGB-D SLAM, ICP and KISS all produced their scoped messages or displays. Short successful sessions do not erase earlier tracking losses. RGB-D SLAM map updates do not establish loop closure; KISS quality fields remain null.

Raw RealSense replay matches recorded four-stream counts; L2 packet/decode checks retain CRC rejection and sequence status. RViz renders actual pixels. A missing TF during LOST is not evidence of a complete map. [All-session evidence](../evidence/live-smoke-20261009.json).

## 2. Software and timing

Fixes retain failures for stereo timestamp mismatch, PowerShell exit-code handling, RGB/depth output matching and RViz status rendering. Eight transport/matching tests pass. Only later sessions have startup code hashes; earlier missing hashes remain null.

Historical live input was about 4–6 Hz under shared load. Native compute measurements are not sensor-to-display latency. Later typed-byte publication improves input rate without proving precision or long-run 30 Hz operation. [Replay controls](OFFLINE_REPLAY.md).

## 3. Next acceptance

The launcher cleans up only its own processes. Controlled fixed/measured-motion tests and independent references are still required. [Test plan](TEST_PLAN.md) · [Detailed mode counts and failures](LIVE_VALIDATION.zh-CN.md).
