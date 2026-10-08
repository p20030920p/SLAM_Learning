# Prepare a repository the interview can test

English | [中文](SUBMISSION.zh-CN.md)

The repository should let a reviewer trace **a research claim to a figure, a metric, a run and a pinned command**. A polished homepage helps only if this chain works. Four related papers provide a coherent scope; adding more unrelated methods would not strengthen the argument.

## What the homepage must answer in two minutes

| Question | Deliverable |
| --- | --- |
| What is the research problem? | One scoped question about spatial correspondence and map decisions, plus existing counterexamples |
| Which papers were actually reproduced? | Four paper cards, with full-teaser versus semantic-core subset scope stated |
| What was measured? | Native logs, portable records, evaluation definitions and differences from paper tables |
| What can I watch or read? | One MP4/GIF and independent English/Chinese PDF per completed core run |
| What is your hypothesis? | A candidate mechanism, a minimal implementation, baseline controls and rejection criteria |
| What is unfinished? | Independent label review, complete semantic accuracy/graphs/navigation and physical collection remain open |

Keep one prominent measured visual, then a compact four-paper table. Put install details on reproduction pages. Videos must identify input, method, pose source, coordinates and run; a rendered replay must not imply live throughput or a screen capture. PDFs should contain the same scope and numerical evidence as the paper cards.

## Acceptance criteria before emailing the link

1. Open the public **main** branch in a logged-out browser. Every paper/media/PDF link should resolve, without private cache paths.
2. In a fresh environment, run the quick smoke command and verify committed evidence. Heavy reproductions have separate commands and requirements.
3. Preserve failures, mismatched paper targets and exact compatibility/resource adaptations. Do not relabel component execution as full paper validation.
4. Check the bilingual pair after every factual correction. Audit the mapper's actual pose input rather than infer its coordinates from a loader default.
5. Confirm MP4 decodes to the recorded frame count and PDF pages render without clipping. Check the first, middle and last video frames.
6. Freeze a confirmation protocol before viewing held-out data. Already observed room0 and synthetic results remain exploratory.
7. Include AI disclosure, dataset/weight sources, licensing notes, limitations and a concise interview route.

## A ten-minute presentation

Spend two minutes on the problem and why these four papers belong together. Spend three on executed pipelines and an actual replay; explain the 5.347532 pp scoring effect and the coordinate-frame audit. Spend three on the candidate hypothesis, competing threshold/visibility baselines and a result that would reject it. Spend two on the fixed-sensor/handheld experiment and what can be done without a robot.

Be able to derive the shared-bias variance, explain a failed run and rerun one command. A reviewer may ask why more observations are correlated, why hidden does not mean removed, why query cosine is not probability, and why object count is not semantic accuracy. The honest answer should use the committed evidence, not a rehearsed claim of a universal gain.

## Suggested submission wording

“This repository reproduces the author dynamic-map pipelines of DUFOMap and BeautyMap on a complete public teaser and the mapping cores of ConceptGraphs and HOV-SG on explicitly scoped Replica subsets. It studies how spatial correspondence affects map decisions, reports evaluation and frame-convention discrepancies, and proposes a falsifiable shared-pose hypothesis. Videos, bilingual reports and a D435i/L2 physical protocol are linked; full semantic benchmark/navigation and physical validation are not claimed.”

Use this only after checking the delivered paper cards. The detailed argument is [STUDY](STUDY.md), and the executable physical plan is [REAL_WORLD](REAL_WORLD.md).
