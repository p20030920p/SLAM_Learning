# 当定位误差被误认为地图变化

面向实验室申请的方向 1「动态环境中的鲁棒定位与 SLAM」和方向 2「语义建图、视觉定位与导航」。这次重构将论文目录汇总改为有明确研究问题、实际执行记录和失败边界的项目。

**研究问题：多个观测共享定位偏差时，地图维护为什么可能越看越自信、却越改越错？** 清除动态点、关联对象和更新语义都依赖空间对应关系。如果先固定有误差的位姿，再逐点／逐对象独立判定变化，公共的位姿误差可能变成许多“环境变化证据”。

假设是：在不可逆更新之前，建模共享位姿不确定性与观测相关性；对无法观测的对象保留未知状态；缺少稳定锚点时延迟更新并请求额外视角。重点是可辨识性与证据校准，不能简单归结为“加一个记忆模块”。

| 阅读入口 | 内容 |
| --- | --- |
| [研究论证](docs/RESEARCH.md) | 结构性问题、反例、公式、可证伪假设 |
| [热门方向与论文对照](docs/LITERATURE.md) | 2024–2026 年代表作、共同假设、已有解决方案 |
| [实际实验结果](docs/RESULTS.md) | 两种作者方法、三组实验、负面结果与适用边界 |
| [复现说明](docs/REPRODUCE.md) | 干净环境安装、下载、运行、验证及 Linux 路径 |
| [重构审计](docs/AUDIT.md) | 原仓库的问题、改动、未保留的历史结论 |
| [替换后的提示词](docs/PROMPT.zh-CN.md) | 将足式 RL 研究思路改写为方向 1–2 |
| [面试准备](docs/INTERVIEW.md) | 必须能解释的假设、指标和 AI 使用情况 |

## 已完成的实测

在公开 KITTI-00 teaser 的全部 141 帧、17,362,230 个标注点上，运行了 DUFOMap 作者绑定与 BeautyMap 作者代码。两种方法都完成执行，**均未在声明容差内完全匹配论文表格**。

受控实验测试位姿与对象运动的混淆，以及相关观测造成的过度自信。真实数据实验改变 DUFOMap 的位姿容差与注入误差，显示静态保留和动态检出的权衡，也包含小扰动下没有退化的情况。完整语义建图与导航尚未实测，合成对象位置误差也不是 SLAM ATE 或导航成功率。

## 最短运行路径

安装 Git 与 uv，然后在仓库根目录执行。Linux 与 PowerShell 均可使用：

```bash
uv sync --frozen --python 3.10 --extra methods --extra dev
uv run pytest -q
uv run slam-study run --experiment mechanism
uv run slam-study run --experiment evidence-stress
uv run slam-study fetch
uv run slam-study run --method dufomap
uv run slam-study run --method beautymap
uv run slam-study run --experiment pose-stress
uv run slam-study report --runs results/runs --output results/my-report.md
```

每次运行独立保存记录、日志与哈希；小样本 smoke 不参与论文评分；失败不会读取上次结果。数据和大点云不上传 GitHub。原版本保留于 Git 历史 `af1e58b`，新项目只接受实际运行产生的证据。

提交前应能现场解释“为什么更保守的方法可能只是在少回答”“为什么多数对象同向移动会让公共位姿修正失效”，以及为何已有的可见性、记忆和联合图优化不等于我们已经证明它们有缺陷。
