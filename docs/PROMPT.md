# Research prompt for directions 1–2

English | [中文](PROMPT.zh-CN.md)

Focus on robust localization/SLAM in dynamic environments and semantic mapping, visual localization and navigation. Start by reproducing selected author pipelines and inspecting their outputs. Do not choose a hypothesis first and then treat its supporting examples as confirmation.

Read DUFOMap, BeautyMap, ConceptGraphs, HOV-SG, Khronos, DovSG and verifiable recent spatiotemporal maps through the information flow: pose → correspondence → visibility/change evidence → object/semantic fusion → map update → localization/navigation query. Identify assumptions shared by several methods that make a class of tasks unidentifiable or unreliable even with different networks or thresholds.

Investigate whether pose drift can resemble object motion/disappearance, occlusion can resemble absence, and correlated observations can be counted as independent evidence. These are questions, not assumed failures. Identify methods that already model visibility, memory or joint estimation, and use them as counterexamples to narrow the bottleneck.

Give original sections, equations and code locations. Separate paper statements, reproduced observations, structural inference and untested conjecture. Reconcile evaluator differences before claiming failure. At least one semantic frontend is required before asserting an empirical cross-field common problem.

After reproduction, formulate a candidate hypothesis. Freeze held-out scenes/seeds, validation-only thresholds, coverage/latency budgets and rejection criteria before the confirmatory experiments. Control pose magnitude and correlation separately, anchor/mover fraction, visibility and delayed correction. Compare simple swept thresholds with the proposed intervention. Preserve negative results and report recall/coverage with risk.

Deliver a bilingual repository with fixed versions and verified data, raw scores/logs, a staged plan, and media slots for measured GIF/video comparisons. Render from the same point identities used for scoring. Synthetic mechanisms are exploratory, not full SLAM/navigation reproduction or independent confirmation of a hypothesis selected from those results.
