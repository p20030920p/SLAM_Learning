# 01-04 · Removert

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | Removert: Remove then Revert — Static Map Building in Challenging Environment |
| Venue | **IROS 2020** |
| 论文链接 | [doi:10.1109/IROS45743.2020.9340856](https://doi.org/10.1109/IROS45743.2020.9340856) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [gisbi-kim/removert](https://github.com/gisbi-kim/removert) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | 🟢 **已复现：命中基准表 I 行（99.44/41.53/64.26）**；⚠️ 原论文闭源 |
## 它做了什么 What it does

先从距离图像里删掉「可疑」的点，再用多分辨率距离图像把**被误删的静态点回滚回来**（remove then revert）。

## 为什么复现它 Why

**四个方法里唯一带显式回滚步骤的。** 回滚本质上就是在保护静态结构，所以如果 H1′ 成立（F1 高 ≠ 定位好），Removert 应该是表现最稳的对照组——它是我们理解「为什么有的删除方式更伤定位」的关键样本。

## 复现目标（可验收）Goals

- [ ] 编译通过，产出清理后的地图
- [ ] 单独记录 **revert 步骤删掉了多少点**（这是它和其他方法最大的结构差异）
- [ ] 与 ERASOR 对比：同样的 KITTI 序列，静态点保留率差多少
- [ ] 交给 01-02，看回滚是否真的换来了更低的配准失败率

## 步骤 Steps

```bash
git clone https://github.com/gisbi-kim/removert code/
# ROS1 catkin；仓库 README 给的依赖较多，先按它装完再编译
catkin build removert
```

## 坑与注意 Pitfalls

- ROS1，同样单独开工作空间。
- 依赖重（距离图像相关库），编译失败优先查 README 的依赖清单而不是猜。
- 它的参数比 ERASOR 多，**但正因为有 revert 步骤，它对参数应当更不敏感**——
  如果实测发现它也很敏感，这本身就是一个值得记录的发现。

## 复现结果 Results（2026-10-05）

### 一、命中基准行

跑法：`methods/removert/build/removert_run <seq> config/params_kitti.yaml`，
KITTI 00（141 帧），评测用基准自带的 `export_eval_pcd`（`min_dis=0.05`）。

| | SA [%] | DA [%] | AA [%] | HA [%] |
| :--- | ---: | ---: | ---: | ---: |
| **DynamicMap_Benchmark 表 I, p.5** | 99.44 | 41.53 | 64.26 | — |
| **BeautyMap 论文 表 I, p.6（HA 列）** | 99.44 | 41.53 | — | 58.59 |
| **本次复现** | **99.4361** | **41.5313** | **64.2628** | **58.591** |

### 二、⚠️ 这是唯一一个"论文原文拿不到"的复现

Removert 的 IROS 2020 原文是**闭源**的：

| 尝试 | 结果 |
| :--- | :--- |
| 作者 README 给的唯一链接 `irap.kaist.ac.kr` | ❌ DNS 无法解析 |
| 本仓库的抓取流水线 | ❌ arXiv 覆盖率 0.08，IEEE 返回 202 反爬 |
| **OpenAlex** | ✅ `is_oa: false` / `oa_status: "closed"` / `any_repository_has_fulltext: false` |

因此**本文件夹的验收目标是基准的重实现值，不是 Removert 作者自报值**——
17 个复现里只有它是这样。详见 [`paper_baseline.md`](paper_baseline.md)。

### 三、它和 ERASOR 是同一条轴上的两个极端

| 方法 | SA [%] | DA [%] |
| :--- | ---: | ---: |
| **Removert** | **99.44** | 41.53 |
| ERASOR | 66.71 | **98.54** |

一个**几乎不删**（56,120 个动态 GT 点留在图里），一个**删得过多**（5,748,315 个静态点被判为删除）。
**AA 排名是 DUFOMap > ERASOR > Removert，SA 排名是 Removert > DUFOMap > ERASOR** ——
任务书 §6 的排序稳定性问题，用真实数字回答了。

```bash
python3 reproductions/run_all.py --only 01-04
```

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
