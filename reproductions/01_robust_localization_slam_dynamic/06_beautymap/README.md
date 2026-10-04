# 01-06 · BeautyMap

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | BeautyMap: Binary-Encoded Adaptable Ground Matrix for Dynamic Points Removal in Global Maps |
| Venue | **RA-L 2024** |
| 论文链接 | [arXiv:2405.07283](https://arxiv.org/abs/2405.07283) |
| 论文报告值 | [`paper_baseline.md`](paper_baseline.md) —— 原论文自报结果与复现阻塞分析 |
| 代码 | [MKJia/BeautyMap](https://github.com/MKJia/BeautyMap) ✅ 实测 200 |
| 数据 | KITTI / MulRan（配合 DynamicMap_Benchmark） |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §2 难点 4 高变动场景的地图维护 |
| 复现状态 | 🟢 **已复现：命中论文表 I（96.76/98.38/97.56）** |
## 它做了什么 What it does

用**二值编码的「可适应地面矩阵」**表示地面，把地面上的动态点从全局地图里剔除；核心卖点是不用逐数据集调参。

## 为什么复现它 Why

第四个清理方法，补齐 H1′ 的对比集合。它和 DUFOMap 代表两种「免调参」路线（几何地面假设 vs 可见性建模），两者都要在，排名才有说服力。

## 复现目标（可验收）Goals

- [ ] 编译通过，产出清理后的地图
- [ ] 验证「免调参」：在两个不同数据集上是否真的用同一组参数
- [ ] 交给 01-02 得配准失败率
- [ ] 与 DUFOMap 对照：免调参路线内部，谁的定位可用性更好

## 步骤 Steps

```bash
git clone https://github.com/MKJia/BeautyMap code/
# 按仓库 README 构建与运行
```

## 坑与注意 Pitfalls

- ⚠️ **链接修正**：上游 `Localise/01_task_books/materials/links.md` 记的是
  `github.com/KTH-RPL/BeautyMap`，该地址**实测 404**。正确仓库是
  [`MKJia/BeautyMap`](https://github.com/MKJia/BeautyMap)（实测 200），别照抄旧的。
- 地面假设在坡道/多层场景会失效，记录它在哪种场景下降。

## 复现结果 Results（2026-10-05）

### 一、命中论文表 I：SA/DA/HA 在 0.2 pp 内

跑法：`methods/BeautyMap/main.py --data_dir <seq>`，KITTI 00（141 帧，48.6 s），
评测用基准自带的 `export_eval_pcd`（`min_dis=0.05`）。

| | SA [%] | DA [%] | HA [%] | AA [%] |
| :--- | ---: | ---: | ---: | ---: |
| **BeautyMap 论文 表 I, p.6** | 96.76 | 98.38 | **97.56** | — |
| **本次复现** | **96.9529** | **98.3382** | **97.6407** | 97.6431 |
| 差值 | +0.19 | −0.04 | +0.08 | — |

> ⚠️ **BeautyMap 报的是调和平均 HA，基准与 DUFOMap 报的是几何平均 AA** ——
> 两个不同的数。本次两者几乎相等（差 0.0024 pp），但那是**因为 SA 与 DA 本身就很接近**，
> 不是两个指标等价。反例见 [01-05](../05_dufomap/README.md)：那里换个参数，SA/DA 各动 2 pp 而 AA 只动 0.09。

### 二、⚠️ 上游代码在 NumPy 2 下跑不起来（两处，必须打补丁）

BeautyMap 自带的 `utils/pcdpy3.py` 用了两个 NumPy 2 已删除的 API：

| 行 | 原写法 | 补丁 | 后果 |
| :--- | :--- | :--- | :--- |
| 150 | `np.fromstring(buf, dtype)` | `np.frombuffer(buf, dtype).copy()` | **读入时就崩** |
| 265 | `pc.pc_data.tostring('C')` | `pc.pc_data.tobytes(order='C')` | **跑完 48 秒、在最后写文件时才崩** |

第二处特别值得记：只修第一处的话，程序会正常跑完整个过程，然后在**最后一步**失败 ——
从日志上看像是"算法跑通了但存不下来"。`reproduce.py` 的 `require()` 会检查这两个补丁是否已打，避免新克隆的人重新踩一遍。

### 三、四个方法齐了：基准表 I 的 D 线部分已复现

| 方法 | 本次 SA | 本次 DA | 本次 HA | 论文 HA | 论文出处 |
| :--- | ---: | ---: | ---: | ---: | :--- |
| Removert | 99.4361 | 41.5313 | 58.591 | 58.59 | BeautyMap 表 I |
| ERASOR | 66.7078 | 98.5352 | 79.5563 | 79.55 | BeautyMap 表 I |
| **BeautyMap** | 96.9529 | 98.3382 | **97.6407** | **97.56** | **BeautyMap 表 I（自报）** |
| DUFOMap | 97.9635 | 98.7196 | 98.3401 | — | DUFOMap 表 I（SA/DA/AA） |

**BeautyMap 是四个里唯一 SA 与 DA 都 > 96 的**：它既不像 Removert 那样几乎不删，也不像 ERASOR 那样删得过多。

```bash
python3 reproductions/run_all.py --only 01-06
```

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
