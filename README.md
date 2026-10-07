# When localization errors become map changes

A research assignment on **robust SLAM in dynamic environments** and **semantic mapping, visual localization and navigation**. The question is: **can repeated observations make a persistent map confidently wrong when those observations share a pose error?**

[中文说明](README.zh-CN.md) · [Research argument](docs/RESEARCH.md) · [Recent literature](docs/LITERATURE.md) · [Measured results](docs/RESULTS.md) · [Reproduction guide](docs/REPRODUCE.md)

This repository contains two executed author-method adapters, a real-data pose sensitivity experiment, and two controlled mechanism experiments. It distinguishes successful execution from agreement with a paper's table. It does not claim that every reviewed paper was reproduced, or that the proposed semantic SLAM system has been built.

## Read the argument

1. [Research note](docs/RESEARCH.md): shared assumptions, counterexamples, identifiability, hypothesis and rejection criteria.
2. [Literature matrix](docs/LITERATURE.md): eight core works from 2024–2026, including recent work that already handles visibility and memory.
3. [Results and their limits](docs/RESULTS.md): numbers, graphs, failures and counterevidence.
4. [Generated evidence ledger](results/REPORT.md) and [portable records](results/reference): commands, versions, source/data hashes, raw trials and logs.

## What was actually measured

| Experiment | Scope | Outcome |
| --- | --- | --- |
| DUFOMap 1.1.1 author binding | 141-frame KITTI-00 teaser, 17,362,230 labeled points | Executed; SA 97.9798%, DA 98.7029%, AA 98.3407%; paper comparison fails the declared 0.01 percentage-point tolerance |
| BeautyMap pinned author code | Same teaser, documented Python/Windows compatibility patches | Executed; SA 96.9529%, DA 98.3382%, HA 97.6407%; paper comparison fails |
| DUFOMap pose sensitivity | Six real-data runs: three correlated translation amplitudes × two pose tolerances | Static retention/changed-point detection tradeoff; small perturbation effects are not uniformly monotonic |
| Pose–motion ambiguity | 3,840 paired synthetic trials | Common-mode correction helps with minority movers; breaks with a coherent moving majority |
| Correlated evidence | 12,000 synthetic trials | Treating shared pose noise as independent makes repeated evidence overconfident; covariance-aware inference trades recall for lower false deletion |

The author-method results use a Python nearest-neighbor evaluator with the benchmark's 5 cm criterion. They are not certified reproductions of the original PCL evaluator. Pose sensitivity uses direct point identities and a different binding API; its scores belong to a separate table. See [protocol details](docs/REPRODUCE.md).

## Run from a fresh checkout

Install Git and [uv](https://docs.astral.sh/uv/). Python 3.10 is selected explicitly because the pinned author packages include native extensions.

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study doctor
uv run pytest -q
uv run slam-study run --experiment mechanism
uv run slam-study run --experiment evidence-stress
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
uv run slam-study run --experiment pose-stress
uv run slam-study report --runs results/runs --output results/my-report.md
```

`fetch` downloads a 385 MB public teaser, checks its published MD5, hashes every extracted PCD, and checks out exact upstream commits. Use `fetch --direct` only if your configured proxy is broken. Large data/maps stay outside Git. Allow several GB for inputs and fresh per-run maps.

Use `--frames 10` for a smoke run; it deliberately produces no paper score. Use `--strict-paper` to make a table mismatch return exit code 2. Every run receives a fresh output directory; subprocess failures cannot reuse an old score.

```bash
uv run slam-study verify results/runs/<run-id>/record.json --full
uv run slam-study export results/runs/<run-id>/record.json --name my-run
uv run slam-study verify results/reference/my-run/record.json
```

An export keeps portable logs, measurements and hashes. `verify --full` also requires the large local map. Hash checks establish file integrity, not independent certification of a scientific claim.

## Repository layout

```text
configs/             dataset, pinned upstreams, paper targets, experiment factors
src/slam_learning/   adapters, evaluator, provenance, experiments and CLI
tests/               metric, parsing, failure and mechanism checks
docs/                argument, literature, protocols, interpretation, audit
results/reference/   exported measured evidence; no dataset redistribution
results/runs/        ignored fresh local runs, including failures
archive/             explicitly unverified inherited claims
```

The previous implementation is recoverable from commit `af1e58b`; it is excluded from the active experiment suite. [The audit](docs/AUDIT.md) explains why its status labels were not retained as evidence.

Both author methods and the real-data sensitivity experiment also ran successfully on [Ubuntu 22.04 CI](https://github.com/p20030920p/SLAM_Learning/actions/runs/37622082701); author-method scores match Windows. Linux records are published alongside Windows records. CPU commands and an optional, locally untested Docker entry point are in [REPRODUCE.md](docs/REPRODUCE.md). CUDA is unnecessary.

## Research integrity

This is a hypothesis-development submission, not a claim of state-of-the-art semantic navigation. Controlled experiments have known identities, visibility or noise scales; real-data results cover one fragment. Negative results and limitations are part of the submission.

[AI/tool disclosure and interview preparation](docs/INTERVIEW.md) · [Chinese research prompt](docs/PROMPT.zh-CN.md)
