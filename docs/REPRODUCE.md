# Reproduction protocol

## Environment

Python **3.10.19**; NumPy 1.26.4, SciPy 1.14.1, Matplotlib 3.9.2, DUFOMap 1.1.1, Open3D 0.18.0. [uv.lock](../uv.lock) pins the environment; [requirements.lock](../requirements.lock) contains hashed transitive dependencies for pip. Use Python 3.10, not an unrelated system interpreter. CPU suffices; a GPU is not used by the active suite.

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study doctor
uv run ruff check src tests scripts
uv run pytest -q
```

On Ubuntu 22.04 install native runtime libraries first:

```bash
sudo apt-get update
sudo apt-get install -y git libgl1 libgomp1 libglib2.0-0
```

The [CI workflow](../.github/workflows/ci.yml) checks the core on Linux and Windows. Its real-data job runs on manual dispatch with `real_data=true`, or a push whose commit message contains `[real-data]`. Consult actual Actions results; configuration alone is not verification.

[Run 37622082701](https://github.com/p20030920p/SLAM_Learning/actions/runs/37622082701) successfully installed a fresh Ubuntu environment, downloaded/verified data, executed both author methods and pose sensitivity, and uploaded portable evidence. Source commit and artifact details are in [linux-run.json](../results/ci/linux-run.json). Subsequent scan-annotation isolation was checked by a fresh Windows author run and cross-platform parser tests; exact executed code versions remain in each record.

VMware without configured GPU passthrough is still suitable for this CPU suite. It requires working guest SSH or an interactive terminal and sufficient RAM/disk. On the current host the existing Ubuntu VM starts, but SSH/VMware Tools were unavailable; no guest execution is claimed. WSL and a Docker daemon were also unavailable locally.

## Data and upstream sources

```bash
uv run slam-study fetch
```

Published archive: [Zenodo 10886629 / 00.zip](https://zenodo.org/records/10886629). MD5 `87f856c4dd1ad05d0ffd4171f92780a0`; downloaded SHA-256 `14e30a0ddc19f275477aa0e72e6ba713f0f6a6a29dcf7ded8a92ce0c421109fd`. Data stays in `.cache/datasets/00`. The manifest hashes each extracted file; runners verify those hashes, 141 scan files and 17,362,230 GT points before execution. Range coordinates are already world-frame; sensor pose is PCD `VIEWPOINT`.

Exact upstream commits:

| Repository | Commit |
| --- | --- |
| [DynamicMap Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | `8b60f36a735a910b8c54b7eb12438db76fb32460` |
| [DUFOMap](https://github.com/KTH-RPL/dufomap) | `9e239ddd5995136e14f5212f33382a6ebc59e518` |
| [BeautyMap](https://github.com/MKJia/BeautyMap) | `98bce4a97db96ddd0d5342e31425c7679f58ba2e` |

DUFOMap execution uses the authors' released PyPI binding, not a locally compiled clone. The clone documents the author demo; the package version is checked separately. A clean pinned checkout is required. `fetch` refuses edited checkouts rather than resetting them. `--direct` bypasses broken proxy settings for the fetch operation only.

## Author-method protocol

```bash
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
```

DUFOMap: 0.1 m resolution, `d_s=0.2`, paper setting `d_p=1`, two native threads. Integrate points with `0.2 < range < 50 m`, then propagate once offline and export the cleaned original-point map. All original points are supplied to output, matching current demo structure. The current demo uses `d_p=2`; that discrepancy is explicit. Paper-era binary equivalence is not asserted.

BeautyMap: author code with `dis_range=40`, `xy_resolution=1.0`, `h_res=0.5`. Both map and scans are staged as **unlabeled XYZ**, preserving each scan's VIEWPOINT; annotation-bearing intensity is physically stripped. Scans and a completed raw map are legitimate inputs for offline cleaning, not an online-navigation experiment. Python iterator and 64-bit mask patches affect an isolated copy and are recorded in `compatibility.patch`.

The evaluator labels a GT point retained if a cleaned-map point lies within 0.05 m. SA = kept static / all static; DA = removed dynamic / all dynamic; AA = geometric mean of SA and DA; HA = harmonic mean. Values are percentages. Both classes must exist. Near coincident geometry can make map correspondence differ from exact point-label evaluation. Original PCL equivalence has not been cross-checked.

`--frames 10` is smoke-only, with no GT score or paper comparison. `--strict-paper` returns 2 for paper disagreement, 1 for blocked/failed execution and 0 for a matched full run. Normal runs return 0 for completed execution even if paper agreement fails. A fresh UUID output directory prevents stale results; logs and nonzero subprocess exits are retained.

## Mechanism and real-data diagnostics

```bash
uv run slam-study run --experiment mechanism
uv run slam-study run --experiment evidence-stress
uv run slam-study run --experiment pose-stress
```

Factors, seeds and noise scales are in [synthetic.json](../configs/synthetic.json), [evidence_stress.json](../configs/evidence_stress.json) and [pose_stress.json](../configs/pose_stress.json). The first two need no downloaded data; the third requires the verified teaser and DUFOMap. Interpretation, negative results and all metric boundaries are in [RESULTS.md](RESULTS.md). Native multithreaded output is not promised bitwise deterministic.

## Evidence and export

```bash
uv run slam-study report --runs results/runs --output results/my-report.md
uv run slam-study verify results/runs/<run-id>/record.json --full
uv run slam-study export results/runs/<run-id>/record.json --name my-run
uv run slam-study verify results/reference/my-run/record.json
```

Replace `<run-id>` with the directory printed by the command. The export refuses an existing name. Published evidence omits large maps and dataset files but retains their hashes. Portable `verify` allows declared local-only maps to be absent; `--full` requires them. Git dirty state includes untracked documentation/evidence, so source hashes are also recorded. A hash is an integrity check, not an authenticity guarantee.

## Optional container

```bash
docker build -t slam-study .
docker run --rm slam-study doctor
docker run --rm -v "$PWD/.cache:/study/.cache" -v "$PWD/results:/study/results" slam-study fetch
docker run --rm -v "$PWD/.cache:/study/.cache" -v "$PWD/results:/study/results" slam-study run --method dufomap
```

On PowerShell use `${PWD}` if needed by the local Docker client. The image includes hashed pip dependencies but its Python base tag and apt repositories are not digest/snapshot pinned. The Dockerfile is a convenience entry point, **not a locally tested or bitwise reproducible container**. Prefer the tested uv environment and inspect CI evidence for Linux verification.

## Troubleshooting

Missing verified data is `blocked`; modified data or failed native execution is `failed`. Inspect that run's `record.json` and `run.log`. Do not copy an old score into the fresh output directory. Out-of-memory errors require more guest RAM or fewer simultaneous processes, not a changed metric. If an upstream pin is unavailable or dirty, preserve it and diagnose instead of silently checking out a new revision.
