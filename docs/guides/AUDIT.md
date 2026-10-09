# Refactor audit

English | [中文](AUDIT.zh-CN.md)

> Historical measurements/analysis; current question and next decision: [STUDY](../research/STUDY.md) · [PLAN](../research/PLAN.md).

Baseline inspected: `af1e58b`. Original files remain recoverable in Git; a local sibling backup was preserved. Historical scores are **unverified inherited claims**, not inputs to the new ledger.

| Finding | Consequence | Replacement |
| --- | --- | --- |
| `run_all.py` rendered completion from metadata ticks/verdicts | Static labels could stay complete for unexecuted/blocked methods | Runtime evidence states: running, executed, smoke_passed, failed, blocked |
| Historical summary: 21 entries, 14 green, 7 blocked, `ran_this_pass=0` | Summary was not fresh-run evidence | Preserve only in [inherited-ledger.json](../archive/inherited-ledger.json) |
| Output existence accepted by several wrappers | Failed reruns could retain stale scores | Fresh UUID directories; checked subprocess return codes and artifacts |
| AnyLoc could read prior scores after subprocess failure | Displayed score did not imply successful execution | Excluded from active suite; new adapters forbid this path |
| Local backtests, including empty comparisons, confused with paper baselines | Regression checks could falsely look like paper agreement | Explicit paper/table/metric and 0.01 pp tolerance; invalid/empty metrics rejected |
| Old hardware blocker assumed no GPU | Stale for the current RTX 4070 SUPER host | Runtime detection; active methods use CPU |
| “Observability” used range/FOV without occlusion | Did not establish visibility | Do not reuse that conclusion; synthetic visibility is explicitly oracle |
| Map/point evaluation and AA/HA conflated | Incompatible scores could share a ranking | Separate protocols; geometric AA / harmonic HA checked |
| Incomplete PCD field/layout/payload validation | Malformed data could yield plausible metrics | Strict binary parser and meaningful validation checks |

BeautyMap needed Python `map` iterators converted to lists and explicitly 64-bit integer masks to avoid Windows overflow. The first failure is preserved. Pinned checkouts remain clean; only per-run copies are patched and patch details exported.

The author implementation uses scan XYZ but the downloaded intensity contains annotations. The final adapter physically strips scan intensity too, preserving sensor VIEWPOINT. A fresh full BeautyMap run confirmed unchanged scores after that isolation change.

The active suite has two methods and three experiments, rather than 21 nominally complete folders that were not all re-established. This scope reduction prioritizes auditable evidence. It does not imply every historical upstream is defective.

Tests cover correspondence, metrics, parsing, failed subprocesses, timeouts, traversal, artifact tampering, exports and mechanisms. Hash verification establishes integrity, not independent scientific certification. Large maps are local-only; portable evidence requires no data redistribution.

The writing revision orders the study as reproduction, observations, candidate bottleneck, hypothesis and next experiments. Synthetic measurements are retained but classified as exploratory. Independent bilingual documents, media slots and WSL preparation were added.
