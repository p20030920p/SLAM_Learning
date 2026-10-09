# Next decision, not a wider roadmap

English | [中文](PLAN.zh-CN.md)

Finish the existing equal-cap analysis of identity errors and query hits before building a bounded replay prototype or adding methods. The primary hypothesis compares reassociation with fixed associations; simple controls separately inform the prototype decision. [Current question](STUDY.md).

| Stage | Status / required output |
| --- | --- |
| Four reproductions | Core outputs published; larger [author runs](https://github.com/p20030920p/SLAM_Learning/blob/535a2780af7ca7eb3aa02f722e1340fe90bc2dcf/docs/SCOPE.md) include scoped scoring, adaptations and failures |
| Counterevidence | room0: correlation is not uniformly worse; room1: lower support closes the selected recovery deficit |
| room2 mapping | 28 cells executed; one frozen frontend and AI-only labels |
| room2 analysis | Pending: recalculate all seeds/readouts, zero-error parity, identities, query hits and correction cost |
| Prototype decision | Apply the frozen oracle-versus-simple-controls gate below; publish ties and failures |
| Confirmation | Independent label review and broader scenes/events remain necessary; AI-only exploration cannot confirm H1 |

At matched RMS, support and endpoint, oracle needs ≥10 mean percentage-point improvement over every simple control at two finite caps, ≥2/3 positive paired seeds, and no seed increasing labelled duplicates/mixes. Passing permits a prototype plan; failing narrows or stops that proposal. This gate is separate from testing reassociation against the fixed-association baseline. [Exact protocol](https://github.com/p20030920p/SLAM_Learning/blob/4361d4f353a7449c7d6964887643915d2fc72a11/docs/IDENTITY_BUDGET.md).

If justified, compare bounded replay with full replay and the strongest simple controls, measuring recovery/query quality, identity errors, peak memory and correction latency. No budget benefit is established by matching candidate caps alone.

Hardware acquisition, full navigation and shared-covariance inference are optional later work, not prerequisites for this decision. Preserve original labels, failures, run hashes and reviewed PDF snapshots. Main changes require commit-bound review, CI and explicit owner approval.

Legacy R*/E* codes in media records refer to the [earlier staged plan](https://github.com/p20030920p/SLAM_Learning/blob/dfd4a05f02352d32b4f0a2bf522e189708c9e2b2/docs/PLAN.md), not current completion claims.
