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

### 二、⚠️ 原文拿到了 —— 但它没有数字表

我先前在本文件里写"论文闭源、取不到"。**那个判断是错的**：原文就放在作者自己的代码仓库里
（`irapkaist/removert` 根目录的 `gkim-2020-iros.pdf`，4.76 MB）。

| 尝试过的路径 | 结果 |
| :--- | :--- |
| 作者 README 里的 `irapkaist.ac.kr/...` 链接 | ❌ DNS 解析失败 |
| OpenAlex | ✅ `is_oa: false` / `oa_status: closed` / 无仓库全文 |
| 我据此下的结论 | ❌ **"取不到"——错** |
| **克隆作者仓库** | ✅ **PDF 就在里面** |

**教训**：OpenAlex 的 `is_oa` 说的是**出版商侧**的开放获取，它看不到"作者把 PDF 放进自己 GitHub 仓库"。
**先克隆仓库，再下结论。**

而拿到之后的结果比"拿不到"更值得记：**这篇论文没有一张编号表格**（全文 `TABLE` 命中 0 次）。
它的 "quantitative analysis" 指的是**图 8 / 图 9**——KITTI 03 上 TP/FP/FN 随 revert 迭代变化的曲线。
论文自己的措辞也是定性的："qualitatively competes or outperforms"。

→ **所以 Removert 没有可对标的自报数字，原因不是我们拿不到原文，是原文自己没报。**
本文件夹的验收目标因此只能取基准的重实现值（99.44 / 41.53 / 64.26）。

### 二之二、剩下的阻塞是环境，不是论文

作者仓库是 **ROS 1 catkin 包**（`CMakeLists.txt:8` 的 `find_package(catkin ...)`、`package.xml` 依赖 `roscpp`/`rospy`），
而本机是 **ROS 2 Jazzy、无 Docker、无 sudo** —— **原始代码不能直接跑**。
目前跑的是 DynamicMap_Benchmark 的无 ROS 重实现（`Kin-Zhang/removert`）。
这就是 01-03 与 01-04 共同的、尚未解决的问题，见 [PAPER_BASELINES.md](../PAPER_BASELINES.md)。

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
