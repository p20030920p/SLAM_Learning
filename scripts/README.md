# Tools

| Directory | Purpose | Example |
| --- | --- | --- |
| `setup/` | Install isolated environments | `bash scripts/setup/setup_linux.sh` |
| `methods/` | Fetch inputs and run semantic methods | `.venv-hovsg/bin/python scripts/methods/run_hovsg.py` |
| `experiments/` | Pose controls, analysis and annotations | `uv run python scripts/experiments/run_paired_suite.py --help` |
| `evidence/` | Validate and recover recorded evidence | `uv run python scripts/evidence/verify_evidence.py` |
| `media/` | Record, view and export measured outputs | `uv run python scripts/media/prepare_visual_review.py --help` |

Start ordinary LiDAR reproduction through `launch/reproduce.sh` or `launch/reproduce.ps1`; `scripts/run_reproduction.sh` remains a compatibility entry. Other tools retain their filenames and arguments in the directories above. Run commands from the repository root with the environment specified in [Setup](../docs/guides/REPRODUCE.md).

安装、方法运行、对照实验、证据检查和媒体工具分别放在以上五个目录。常用复现从 `launch/` 启动；其余工具保持原文件名和参数，使用新的分组路径。完整中文命令见[安装说明](../docs/guides/REPRODUCE.zh-CN.md)。
