# Identity and candidate-budget study v2

[中文](IDENTITY_BUDGET.zh-CN.md)

**Status: implementation and raw-label preparation; H1 remains a candidate.** The owner declined manual review on 2026-10-08 and authorized continuing only on the experimental branch. The original human-gated protocol is preserved. The separate AI-only exploratory protocol cannot be reported as that confirmation experiment. No main merge is authorized.

## Question and limits

After every arm receives the same exact historical poses, does recomputing associations recover more valid annotated targets at the same candidate upper limit? This distinguishes historical identity decisions from coordinates and from simply exposing more low-support fragments. It does not match total memory, point count or actual candidate count; each must be reported separately. It does not establish a shared bottleneck across four methods or generalization from one scene.

All labels are partial visible-surface references, not official Replica instance GT. Class-query retrieval and physical-instance recovery are evaluated separately. A class query can hit any annotated instance of that class. Unlabelled candidates have unknown identity; they are not automatically false positives. Duplicate excess counts qualifying fragments beyond the first for one annotated physical ID. Mixed-object counts require support for two annotated IDs. Both diagnostics depend on label ontology and incomplete visibility.

## Fixed design

| Item | Declaration |
| --- | --- |
| Scene | room2; no switching after seeing outputs |
| Mapping frames | 0, 25, …, 375 (16 observations) |
| Held-out reference frames | 12, 62, 112, 162; never enter frontend/mapping |
| Instances | 5 AI proposals: blue_vase, bird_figurine, brown_jar, fish_figurine, chair |
| Correction | Exact eight-prefix-pose correction immediately after observation 8 |
| Error conditions | 10/30 cm world-x RMS × seeds 417/518/619; one zero-error control per arm |
| Arms | native_fixed; threshold_fixed (1.0); visibility_fixed; oracle_replay |
| Mapping cells | 28; failures retained, never silently overwritten |
| Readouts | Support ≥1/2/3 × candidate cap 25/50/100/unlimited, offline only |
| Ordering | Detection support descending; points descending; contributor-derived ID ascending |
| Main endpoint | Immediately after correction (observation 8); 12/16 are persistence analyses |

Each fixed arm reconstructs geometry with its own original association trace, retaining its members and original CLIP/text features. Oracle reruns native associations at the exact poses. All arms use the same frozen frontend. Prefix regeneration has computation and data-storage costs; the fixed geometry control is not a deployable low-memory method.

Complete snapshots retain contributor IDs, support, point geometry/colors, CLIP/text features and input hashes. Stage16's complete state is saved **before final filtering**, separately from the finalized native parity artifact. Native periodic postprocessing stays fixed. Readouts never change these states. Snapshot bytes measure serialization size, not total runtime memory. Correction timing excludes snapshot I/O; it includes full-prefix reconstruction.

Zero-error own-policy correction, zero-error native/oracle equivalence and original-batch parity must pass before interpretation. Fixed arms assert unchanged historical membership/support/features for every error condition. CPU contract tests complement, rather than replace, these native gates.

## Labels and owner amendment

The [review package](../annotations/review/identity-v2/index.html) contains raw RGB, proposed polygons, depth previews and an editable review form. The preserved [confirmation protocol](../configs/identity_budget_v2.json) still requires a real human receipt before sealing or frontend execution. It cannot silently accept exploratory labels.

The [owner-amended exploratory protocol](../configs/identity_budget_v2_exploratory.json) requires an explicit `--exploratory` option at sealing, frontend and mapper entry points. Its [AI labels](../annotations/room2/targets.ai-v2.json) retain `human_reviewed: false`; its freeze and every run record state `ai_only_exploratory`. AI raw-view checks do not replace independent human review. Room1 originals and scores remain unchanged; any later ontology repair must be a new, explicitly post-hoc annotation/analysis version.

## Run and recording workflow

Use an isolated Linux runtime with the pinned existing semantic environment; do not install into or modify another window's environment. All study outputs below are separate and ignored by Git. Read-only source reuse is allowed. Before each heavy phase:

```bash
python scripts/check_study_resources.py
```

Exit 2 means defer heavy work; do not stop another process, change its environment, or compete for its GPU. Prepare the selected raw subset with `fetch_delayed_scene.py --protocol … --output …`; `--archive` can read an already downloaded official ZIP without changing it. Commit the protocol before source preparation and freeze labels before frontend inspection.

```bash
python scripts/seal_delayed_annotations.py --protocol configs/identity_budget_v2_exploratory.json \
  --annotations annotations/room2/targets.ai-v2.json --data "$DATA" \
  --output "$SEAL" --seal --exploratory
python scripts/record_session.py --output "$FRONT_VIDEO" --cwd "$REPO" -- \
  "$SEMANTIC_PYTHON" scripts/prepare_delayed_frontend.py \
  --protocol configs/identity_budget_v2_exploratory.json --annotations annotations/room2/targets.ai-v2.json \
  --data "$DATA" --freeze "$SEAL/freeze.json" --native-source "$SOURCE" \
  --weights "$WEIGHTS" --output "$FRONT" --exploratory
python scripts/record_session.py --output "$MAP_VIDEO" --cwd "$REPO" -- \
  "$SEMANTIC_PYTHON" scripts/run_identity_budget.py \
  --protocol configs/identity_budget_v2_exploratory.json --annotations annotations/room2/targets.ai-v2.json \
  --data "$DATA" --freeze "$SEAL/freeze.json" --frontend "$FRONT" \
  --weights "$WEIGHTS" --output "$RUN" --exploratory
python scripts/analyze_identity_budget.py --run "$RUN" --data "$DATA" --output "$ANALYSIS"
```

Variables are explicit absolute study paths, not shared run folders. Choose a new attempt directory after any failure. Keep original terminal MP4, transcript, timestamps, command and exit record locally. The recorder uses its own X display and does not capture the user's desktop. A separate actual RViz 3D-view recording must identify **saved-map replay**; it is not live inference. Publish short GIFs only with actual source-record hashes, truthful captions and separate full-video retention. Final PDFs require per-page visual inspection. No new result media or scientific result PDF is claimed until runs finish.

## Decision and release

At one fixed RMS, support threshold and endpoint (instance recovery or category-query hit), oracle must beat every simple control by at least 10 mean percentage points at two finite caps, with at least 2/3 positive paired seeds per comparison. Neither annotated duplicate excess nor mixed-object count may increase in any paired seed. Different supports or endpoints cannot be combined to manufacture two qualifying caps. A pass only permits drafting a bounded-replay prototype plan; H1 remains unverified, especially with AI-only labels. A simple-control tie means narrow or stop H1.

Work stays in `study/identity-budget-v2`. The [working agreement](../AGENTS.md) and PR template require commit-bound review, CI, evidence, bilingual consistency and media provenance; later changes need re-review. A draft may contain exploratory results. It cannot be presented as a human-validated confirmation study, and main merging always requires separate explicit owner approval.
