# Recent directions and structural reading

Literature cutoff: **7 October 2026**. “Active direction” means several recent representative works pursue it; this is not a bibliometric popularity ranking. The eight core works are chosen for comparable map-update decisions, not a leaderboard across incompatible tasks.

## Active directions within fields 1–2

| Direction | Primary sources | Opportunity / deadline tradeoff |
| --- | --- | --- |
| Joint ego/object estimation in dynamic scenes | [DynoSAM, 2025](https://arxiv.org/abs/2501.11893), [code](https://github.com/ACFR-RPG/DynoSAM) | Separates camera and object motion; full integration takes more time than an isolated update experiment |
| Learned geometry and dense visual SLAM | [MASt3R-SLAM, CVPR 2025](https://edexheim.github.io/mast3r-slam/), [code](https://github.com/rmurai0610/MASt3R-SLAM); [DyPho-SLAM, 2025](https://arxiv.org/html/2509.00741v1) | Geometric priors / rich maps do not automatically resolve stale-object validity |
| Open-vocabulary 3D objects and scene graphs | ConceptGraphs, HOV-SG, DovSG below | Connects localization to language queries; correspondence depends on the pose/map interface |
| Persistent spatiotemporal maps | Khronos, SuperMap and PerSeM below | Visibility and memory already exist, so novelty must be narrower |

[AnyLoc](https://arxiv.org/abs/2308.00688) and [Revisit Anything](https://arxiv.org/abs/2409.18049) are adjacent visual place recognition examples. Recall depends on dataset and positive-match definitions; historical scores are not reused. No fresh VPR run is claimed.

## Eight core works

| Work | Paper evidence | Structural implication (our inference) | Existing protection / boundary |
| --- | --- | --- | --- |
| [DUFOMap, 2024](https://arxiv.org/html/2403.01449v1) | III-A/B models observed free space and sensor/pose margins; IV-C specifies `d_p=1` | Cleaning uses supplied poses; a margin is not shared-residual covariance | Already addresses pose errors and compares pose sources; “noise unaware” would be wrong |
| [BeautyMap, 2024](https://arxiv.org/html/2405.07283v1) | III uses binary occupancy and ray-based refinement/protection; Table I reports HA | Inconsistency after registration can reflect pose error or changes | Already protects against visibility mistakes; acknowledges ground-level limitations |
| [ConceptGraphs, ICRA 2024](https://arxiv.org/html/2309.16650v1) | Object association combines geometric overlap and semantics, then fuses points/features | Incorrect world alignment may fragment or merge instances before reasoning | Semantic association helps; this is not evidence that all semantic maps assume static worlds |
| [HOV-SG, RSS 2024](https://arxiv.org/html/2403.17846v2) | III-A uses accurate odometry for projection/fusion; IV-C uses external LiDAR SLAM | Graph/navigation geometry inherits the pose interface | External odometry and loop closure are safeguards; no fresh sensitivity run here |
| [Khronos, 2024](https://arxiv.org/html/2402.13817v2) | IV discusses local consistency; V-B jointly optimizes poses/fragments/background; V-C distinguishes absence of evidence | Candidate generation and local consistency still matter before corrections | **Counterexample:** already has joint optimization, history and visibility; cannot be grouped as fixed-pose independent cleaning |
| [DovSG, 2024 preprint / 2025 paper](https://arxiv.org/html/2410.11989v2) | III-D relocalizes using ACE, matching and ICP before local updates | Wrong relocalization may affect associations and obsolete-voxel decisions | Explicitly supports dynamic local updates; refutes “all scene graphs are static” |
| [SuperMap, August 2026](https://arxiv.org/html/2608.22896v1) | III conditions on pose; IV uses depth observation states and recursive evidence | Displayed model motivates checking shared pose covariance and calibration | Already separates observable, unobservable and disappeared; an omitted covariance formula does not prove a code defect |
| [PerSeM, September 2026 preprint](https://arxiv.org/html/2609.19542v2) | 3.1/3.2 projects into persistent world voxels; 5 discusses drift/correlated errors | Label stability does not guarantee correct geometric evidence assignment | Memory/refinement already exists; correlated geometry is an acknowledged limitation |

The recurring interface is narrow: establish spatial correspondence, then interpret map evidence. These papers do not implement one algorithm, and several already mitigate errors. The question concerns residual shared geometric uncertainty in destructive-update confidence.

## Code accessibility and scope

DUFOMap and BeautyMap have executable author implementations and small labeled public data. Their exact commits are in [upstreams.json](../configs/upstreams.json). Other core works were read, not freshly reproduced.

The [SuperMap repository](https://github.com/superxslam/SuperMap), inspected at `ec95b1d50a458645b2669836e2c431f1e957bbc6`, contained a README, paper and teaser, but no implementation, requirements file or runnable examples. Its setup text is not a runnable recipe at this snapshot. PerSeM is treated as a recent preprint, not an independently validated baseline.

A focused update interface permits author-code measurements and negative controls before the deadline. The next step is the same intervention in a real semantic frontend at matched coverage, rather than presenting synthetic object positions as semantic-navigation results.
