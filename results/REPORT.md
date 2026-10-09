# Measured experiment ledger

English | [中文](REPORT.zh-CN.md)

Generated from run records. Execution, paper agreement and hypothesis validation are distinct.

| Experiment | Scope | Execution | Paper table | SA % | DA % | AA % | HA % | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dufomap api diagnostic | full_teaser | executed | not evaluated | — | — | — | — | [api-check-wsl](reference/api-check-wsl/record.json) |
| measured diagnostic plot | measured_diagnostic_plot | executed | not evaluated | — | — | — | — | [api-diagnostic-plot](reference/api-diagnostic-plot/record.json) |
| beautymap | full_teaser | executed | mismatch | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap](reference/beautymap/record.json) |
| beautymap | full_teaser | executed | mismatch | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap-linux](reference/beautymap-linux/record.json) |
| beautymap | full_teaser | failed | not evaluated | — | — | — | — | [beautymap-windows-failure](reference/beautymap-windows-failure/record.json) |
| beautymap | full_teaser | executed | mismatch | 96.9529 | 98.3382 | 97.6431 | 97.6407 | [beautymap-wsl](reference/beautymap-wsl/record.json) |
| ConceptGraphs | Replica room0 40-observation subset | executed | not evaluated | — | — | — | — | [conceptgraphs-wsl](reference/conceptgraphs-wsl/record.json) |
| ConceptGraphs | Replica room0 40-observation subset | failed | not evaluated | — | — | — | — | [conceptgraphs-wsl-batch144-interrupted](reference/conceptgraphs-wsl-batch144-interrupted/record.json) |
| dufomap | full_teaser | executed | mismatch | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap](reference/dufomap/record.json) |
| dufomap | full_teaser | executed | mismatch | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap-linux](reference/dufomap-linux/record.json) |
| dufomap | full_teaser | executed | mismatch | 97.9798 | 98.7029 | 98.3407 | 98.3400 | [dufomap-wsl](reference/dufomap-wsl/record.json) |
| map evaluator cross check | full_teaser | executed | not evaluated | — | — | — | — | [evaluation-check-wsl](reference/evaluation-check-wsl/record.json) |
| controlled synthetic calibration test | controlled_synthetic_calibration_test | executed | not evaluated | — | — | — | — | [evidence-stress](reference/evidence-stress/record.json) |
| full terminal recordings | full_terminal_recordings | executed | not evaluated | — | — | — | — | [full-recordings](reference/full-recordings/record.json) |
| HOV-SG | semantic_frontend_baseline | executed | not evaluated | — | — | — | — | [hovsg-wsl](reference/hovsg-wsl/record.json) |
| HOV-SG | semantic_frontend_baseline | failed | not evaluated | — | — | — | — | [hovsg-wsl-interrupted](reference/hovsg-wsl-interrupted/record.json) |
| HOV-SG | semantic_frontend_baseline | executed | not evaluated | — | — | — | — | [hovsg-wsl-resolved](reference/hovsg-wsl-resolved/record.json) |
| controlled synthetic mechanism test | controlled_synthetic_mechanism_test | executed | not evaluated | — | — | — | — | [mechanism](reference/mechanism/record.json) |
| paired pose analysis | paired_pose_analysis | executed | not evaluated | — | — | — | — | [paired-pose](reference/paired-pose/record.json) |
| report layout review | report_layout_review | executed | not evaluated | — | — | — | — | [paired-report-review](reference/paired-report-review/record.json) |
| bilingual paired reports | Two reading reports; candidate hypothesis remains unvalidated. All pages require separate rendered visual review. | executed | not evaluated | — | — | — | — | [paired-study-pdfs](reference/paired-study-pdfs/record.json) |
| beautymap | paper_reproduction_media | executed | not evaluated | — | — | — | — | [paper-media-beautymap](reference/paper-media-beautymap/record.json) |
| conceptgraphs | paper_reproduction_media | executed | not evaluated | — | — | — | — | [paper-media-conceptgraphs](reference/paper-media-conceptgraphs/record.json) |
| dufomap | paper_reproduction_media | executed | not evaluated | — | — | — | — | [paper-media-dufomap](reference/paper-media-dufomap/record.json) |
| hovsg | paper_reproduction_media | executed | not evaluated | — | — | — | — | [paper-media-hovsg](reference/paper-media-hovsg/record.json) |
| bilingual paper reports | Reading reports, not new experiment measurements. Page rendering/visual QA is a separate publication gate. | executed | not evaluated | — | — | — | — | [paper-pdfs](reference/paper-pdfs/record.json) |
| report layout review | report_layout_review | executed | not evaluated | — | — | — | — | [paper-report-review](reference/paper-report-review/record.json) |
| real data pose sensitivity | real_data_pose_sensitivity | executed | not evaluated | — | — | — | — | [pose-stress](reference/pose-stress/record.json) |
| real data pose sensitivity | real_data_pose_sensitivity | executed | not evaluated | — | — | — | — | [pose-stress-linux](reference/pose-stress-linux/record.json) |
| author map replay | author_map_replay | executed | not evaluated | — | — | — | — | [reproduction-media-wsl](reference/reproduction-media-wsl/record.json) |

Recorded failures:

- beautymap (beautymap-windows-failure): CalledProcessError: Command '['D:\\workspace\\be2\\SLAM_Learning\\.venv310\\Scripts\\python.exe', '-m', 'slam_learning.cli', '_worker', '--root', 'D:\\workspace\\be2\\SLAM_Learning', '--method', 'beautymap', '--output', 'D:\\workspace\\be2\\SLAM_Learning\\results\\runs\\beautymap-9d32b2cc4c1c', '--frames', '0']' returned non-zero exit status 1.
- ConceptGraphs (conceptgraphs-wsl-batch144-interrupted): Command '['/home/qzl/projects/SLAM_Learning/.venv-semantic/bin/python', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/author-code/conceptgraph/scripts/generate_gsa_results.py', '--dataset_root', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/input/Replica', '--dataset_config', '/home/qzl/projects/SLAM_Learning/results/runs/conceptgraphs-855255b27df4/author-code/conceptgraph/dataset/dataconfigs/replica/replica.yaml', '--scene_id', 'room0', '--class_set', 'none', '--stride', '1']' died with <Signals.SIGTERM: 15>.
- HOV-SG (hovsg-wsl-interrupted): Shell reported worker Killed (SIGKILL) in late hierarchical merge after all 40 frontend observations; WSL session ended. OOM cause is not established.

Synthetic trials are exploratory mechanism checks with oracle inputs, not independent hypothesis validation.
Large maps and source datasets are local-only; portable records contain their hashes and fresh-run logs.
`verify --full` requires those maps to be present. No historical archive score contributes to this table.
