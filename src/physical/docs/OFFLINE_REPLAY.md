# Recorded RGB-D replay and input-rate controls

English | [中文](OFFLINE_REPLAY.zh-CN.md)

Existing raw data supports unattended odometry comparisons without new physical actions. Independent distance, moving-trajectory and clean-static acceptance remain incomplete.

## 1. Inputs and results

The same raw SHA-256 produces 500 SDK-aligned RGB-D observations, about 3–53 s. The camera was declared fixed, with dynamic background. Offline paired images share the color timestamp for exact synchronization; this differs from live approximate sync and is not hardware sync.

Four controls retain all outputs and failures. ROS typed-byte publication reaches 10 Hz; the strict ≥99% valid/non-LOST coverage gate still fails at 98.8% in the final run. LOST=0 does not compensate for missing output or an initial high-covariance pose. Limits are <5 cm and <2° with this separate strict coverage gate.

## 2. Software change

`array('B', payload)` avoids per-element checks in the generated ROS setter. Independent checks preserve fields and payload for images/depth/XYZI. Synthetic assignment timings improve, but do not establish the same end-to-end speedup. Earlier failed CDR-comparison drafts remain preserved.

The Linux copy contains 1,504 verified files, about 354 MB. A separate 15-second live preview receives about 8.19 Hz with 97.48% valid coverage, not a 30 Hz algorithm result or stationary-accuracy pass. [Evidence](../evidence/rgbd-rate-and-payload-20261009.json).

## 3. Video and rerun

`preview.mp4` shows measured offline input/state/trajectory at source time, not wall-clock execution speed. A small stationary trajectory is expected. Videos are H.264 without audio; local maps are not semantic object maps. Indoor videos remain local.

Use `--stride 2` for the lower sampling comparison; `--speed` changes playback speed and is not a substitute. Use new output paths and inspect `actual_publish_hz`, `valid_tracking_input_fraction`, `lost_status_fraction` and publish/pose logs. [Detailed controls](OFFLINE_REPLAY.zh-CN.md).

Historical L2 no-packet status on this page predates the later recovery; consult [latest hardware checks](POSTFALL_LOWLIGHT.md). No fusion or H1 result follows from these tests.

## 4. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```powershell
D:\workspace\be2\Personal-Learning-Physical\.venv\Scripts\python.exe D:\workspace\be2\Personal-Learning-Physical\scripts\export_rgbd.py D:\workspace\be2\Personal-Learning-Physical\data\live-camera-20261009-014327-492\raw.db3 --fixed-sensor-session --frames 500 --interval 0.1 --output D:\workspace\be2\Personal-Learning-Physical\data\manual-rate-01
```

```powershell
wsl -d Ubuntu-22.04
```

```bash
cd /mnt/d/workspace/be2/Personal-Learning-Physical
```

```bash
source /opt/ros/humble/setup.bash
```

```bash
python3 scripts/stage_rgbd.py data/manual-rate-01 --output /home/qzl/.cache/personal-learning-physical/manual-rate-01
```

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 python3 scripts/run_odometry_baseline.py /home/qzl/.cache/personal-learning-physical/manual-rate-01 --mode rgbd --stride 1 --domain 85 --session-type stationary --output data/manual-rate-01/odom-10hz
```

```bash
python3 scripts/render_odometry_video.py /home/qzl/.cache/personal-learning-physical/manual-rate-01 data/manual-rate-01/odom-10hz
```
