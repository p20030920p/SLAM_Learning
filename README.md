# Personal Learning

English | [中文](docs/HOME.zh-CN.md)

Reading notes, reproduction practice and D435 / Unitree L2 experiments.

## Start here

| Purpose | Entry |
| --- | --- |
| Study and analysis | [Learning guides](docs/notes/README.md) |
| Hardware practice | [D435 / L2](src/physical/README.md) |
| Mapping workflows | [Runbook](docs/guides/REPRODUCE.md) |
| Recorded results | [Reports](docs/README.md) · [Evidence](results/reference) |

## Status

Camera/LiDAR capture and RGB-D loader checks are recorded. Hardware semantic mapping and controlled recovery tests remain in progress. The D435 has no IMU.

## Structure

```text
docs/      # notes, papers and guides
results/   # recorded results and media
src/       # mapping code, scripts, configs and physical/
```

Run mapping commands from the repository root; hardware commands use `src/physical/` as their project root. [Setup](docs/guides/STRUCTURE.md) · [Hardware setup](src/physical/docs/ENVIRONMENT.md).

[Delivery](https://github.com/p20030920p/SLAM_Learning/tree/main) · [Author reproduction](https://github.com/p20030920p/SLAM_Learning/tree/reproduce/author-originals)
