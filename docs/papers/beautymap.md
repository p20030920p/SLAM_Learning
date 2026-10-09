# BeautyMap — author pipeline reproduction

English | [中文](beautymap.zh-CN.md) | [PDF](../pdf/beautymap.en.pdf)

**Executed:** complete 141-scan KITTI-00 teaser, supplied poses and author map-cleaning code. No trajectory or navigation evaluation is claimed.

![BeautyMap measured replay](../media/beautymap/poster.png)

[MP4](../media/beautymap/replay.mp4) · [GIF](../media/beautymap/preview.gif) · [Run](../../results/reference/beautymap-wsl/record.json) · [Media provenance](../../results/reference/paper-media-beautymap/record.json)

## Method and execution

[BeautyMap (2024)](https://arxiv.org/html/2405.07283v1) uses global binary occupancy matrices, ground adaptation and refinement/restoration to clean a point map. Restoration protects static geometry hidden from some viewpoints. It is not simply a rule that absent means dynamic.

```bash
bash src/scripts/setup/setup_linux.sh
uv run --project src slam-study fetch
uv run --project src slam-study run --method beautymap
```

The pinned author source, executable compatibility patch and dataset hash are recorded. The Windows integer-overflow failure is preserved; explicit 64-bit masks fix compatibility. No threshold is tuned to match the paper. GT intensity is physically stripped from both scan and map inputs before the final runs; annotations remain available only to scoring.

## Measured output

| Metric | Measured % | Paper Table I % | Difference, pp |
| --- | ---: | ---: | ---: |
| SA: static retention | 96.952945 | 96.76 | +0.192945 |
| DA: dynamic removal | 98.338247 | 98.38 | -0.041753 |
| HA: harmonic mean | 97.640683 | 97.56 | +0.080683 |

All 141 scans are processed; 17,362,230 GT points are scored using 5 cm map proximity. Windows, Ubuntu and WSL counts agree. Original PCL/SciPy labels agree on every point for the stored map. The 0.01 pp paper tolerance is not met. Evaluator equivalence on these maps excludes that implementation as the cause, while paper-era source/settings remain unresolved. HA must not be ranked as though it were DUFOMap's geometric AA.

## Limitation and research relevance

The paper's global coordinates make occupancy comparisons efficient, but registration still determines which cells correspond. Ground adaptation introduces a separate geometry assumption; out-of-view restoration is already an explicit safeguard (III-A/C, V).

Our inference is that a coherent registration error may create apparent occupancy changes across many cells. The current teaser success and parameter sensitivity do not prove this failure. The relevant open problem is whether a shared registration gate plus reversible decisions improves static retention at equal dynamic recall and delay, beyond the method's existing restoration and threshold choices.

This connects dynamic robust mapping to semantic maps: removing a persistent surface can erase the geometric support for an object or target. Known pose error is an oracle diagnostic; physical tests must separately evaluate estimated uncertainty. Static camera controls isolate visibility from pose error. [Shared hypothesis and rejection controls](../research/STUDY.md).

## Video interpretation

Twenty-one selected scans use fixed world bounds and the measured final map. Raw/removed/retained panels show green correct removal, red static loss and blue missed dynamic points. This is offline replay, not an evolving online map or algorithm FPS. [Full results and retained failure](../research/RESULTS.md).
