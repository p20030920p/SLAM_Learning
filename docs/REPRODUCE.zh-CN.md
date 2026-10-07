# 复现协议

[English](REPRODUCE.md) | 中文

## 环境

Python **3.10.19**；NumPy 1.26.4、SciPy 1.14.1、Matplotlib 3.9.2、DUFOMap 1.1.1、Open3D 0.18.0。[uv.lock](../uv.lock)固定依赖，[requirements.lock](../requirements.lock)提供带哈希的 pip 依赖。使用指定 Python，不混入系统解释器；当前作者方法用 CPU。

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run slam-study doctor
uv run ruff check src tests scripts
uv run pytest -q
uv run python scripts/verify_evidence.py
uv run python scripts/check_docs.py
```

Ubuntu 22.04 先安装原生运行库：

```bash
sudo apt-get update
sudo apt-get install -y git libgl1 libgomp1 libglib2.0-0
```

[WSL 安装与位置选择](WSL.zh-CN.md)单独说明。Linux 可运行 `bash scripts/setup_linux.sh` 检查环境；`bash scripts/run_reproduction.sh --smoke` 做冒烟，去掉 `--smoke` 跑完整作者方法。脚本不自动运行假设探索。

[CI](../.github/workflows/ci.yml)检查 Linux／Windows 核心；真实数据由手动 `real_data=true` 或提交消息包含 `[real-data]` 触发。[运行 37622082701](https://github.com/p20030920p/SLAM_Learning/actions/runs/37622082701)在新 Ubuntu 环境下载、校验、执行两方法和位姿敏感性并导出记录，[来源与产物](../results/ci/linux-run.json)可追溯。后续扫描隔离改动经新 Windows 全量运行与跨平台解析检查；不改写旧运行版本。

## 数据与作者源码

```bash
uv run slam-study fetch
```

压缩包：[Zenodo 10886629 / 00.zip](https://zenodo.org/records/10886629)，MD5 `87f856c4dd1ad05d0ffd4171f92780a0`，下载 SHA-256 `14e30a0ddc19f275477aa0e72e6ba713f0f6a6a29dcf7ded8a92ce0c421109fd`。本机目录为 `.cache/datasets/00`，逐 PCD 哈希、141 个扫描与 17,362,230 个真值点均在执行前检查。XYZ 已在世界坐标，传感器姿态存于 VIEWPOINT。

| 作者仓库 | 提交 |
| --- | --- |
| [DynamicMap Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) | `8b60f36a735a910b8c54b7eb12438db76fb32460` |
| [DUFOMap](https://github.com/KTH-RPL/dufomap) | `9e239ddd5995136e14f5212f33382a6ebc59e518` |
| [BeautyMap](https://github.com/MKJia/BeautyMap) | `98bce4a97db96ddd0d5342e31425c7679f58ba2e` |

DUFOMap 执行作者 PyPI 绑定，而非本地编译克隆；源码用于核查演示，包版本单独检查。上游必须保持干净，fetch 不重置用户改动。仅在代理失效时使用 `fetch --direct`。

## 作者方法

```bash
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
```

DUFOMap：分辨率 0.1 m、`d_s=0.2`、论文 `d_p=1`、两线程；积分距离 `0.2 < range < 50 m`，离线传播一次，再输出原点清理图。全部原点进入输出，结构与当前作者演示一致；当前演示 `d_p=2` 的差异已明确记录。不保证与论文时期二进制等价。

BeautyMap：`dis_range=40`、`xy_resolution=1.0`、`h_res=0.5`。地图与扫描均只保留 XYZ，扫描保留 VIEWPOINT，实际移除含标注的 intensity。完整原图是离线清图的合法输入，不等于在线导航。Python 迭代器与 64 位掩码补丁仅作用于运行副本，保存于 `compatibility.patch`。

真值点距离清理图中最近点不超过 0.05 m，则视为保留。SA = 静态保留／静态总数；DA = 动态移除／动态总数；AA 为几何均值；HA 为调和均值；全部以百分数记录，两种真值类均须存在。邻近几何会使地图评分不同于精确点身份，原 PCL 尚未对齐。

`--frames 10` 只做冒烟，不评分；`--strict-paper` 在表格不一致时返回 2，环境阻塞／执行失败返回 1，完整一致返回 0。普通运行完成执行即可返回 0，表格一致性另存。每次 UUID 目录独立，日志和失败保留。

## 探索性诊断

```bash
uv run slam-study run --experiment pose-stress
uv run slam-study run --experiment mechanism
uv run slam-study run --experiment evidence-stress
```

因素与种子在 [synthetic.json](../configs/synthetic.json)、[evidence_stress.json](../configs/evidence_stress.json)、[pose_stress.json](../configs/pose_stress.json)。两个合成实验不需要数据；真实诊断需要已校验 teaser 和 DUFOMap。它们是探索，不是冻结候选假设后的留出确认；[结果与边界](RESULTS.zh-CN.md)完整记录。原生多线程不承诺位级确定性。

## 双语汇总与证据

```bash
uv run slam-study report --runs results/runs --output results/local-reproduction.md
uv run slam-study report --runs results/runs --output results/local-reproduction.zh-CN.md --lang zh
uv run slam-study verify results/runs/<run-id>/record.json --full
uv run slam-study export results/runs/<run-id>/record.json --name my-run
uv run slam-study verify results/reference/my-run/record.json
```

`<run-id>` 替换为命令打印的目录。导出拒绝已有名称，大点云与数据不上传但保留哈希。普通 verify 允许声明的本地点云缺失，`--full` 必须存在。Git 脏状态包含未提交文档，所以另存源码哈希。哈希用于完整性，不是独立真实性认证。

## 可选容器

```bash
docker build -t slam-study .
docker run --rm slam-study doctor
docker run --rm -v "$PWD/.cache:/study/.cache" -v "$PWD/results:/study/results" slam-study fetch
docker run --rm -v "$PWD/.cache:/study/.cache" -v "$PWD/results:/study/results" slam-study run --method dufomap
```

PowerShell 必要时写 `${PWD}`。Python 基础镜像标签和 apt 来源未按摘要／快照固定，Dockerfile 没有在本机测试，不承诺位级容器复现。优先使用已检查 uv 环境与已执行 CI。

## 排错

缺校验数据记为 blocked；数据改变或原生执行错误记为 failed。检查该次 `record.json` 与 `run.log`，不复制旧成绩。内存不足时增大 guest 内存或减少并发，不修改指标。上游提交缺失或有改动时保留现场，不静默换版本。
