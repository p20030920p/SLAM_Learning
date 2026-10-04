# 01-01 · DynamicMap_Benchmark

| 项 Item | 内容 |
| :--- | :--- |
| 论文 | A Dynamic Points Removal Benchmark in Point Cloud Maps |
| Venue | **ITSC 2023** |
| 论文链接 | [arXiv:2307.07260](https://arxiv.org/abs/2307.07260) |
| 代码 | [KTH-RPL/DynamicMap_Benchmark](https://github.com/KTH-RPL/DynamicMap_Benchmark) ✅ 实测 200 |
| 数据 | KITTI / MulRan / SemanticKITTI —— 仓库内含清洗后的序列与**人工 GT 标签** |
| 方向 | D1 · 动态环境下的鲁棒定位与 SLAM |
| 任务书对应 | §6 并行实验（恢复自原 T1） |
| 复现状态 | ⬜ 未开始 |

## 它做了什么 What it does

把「动态点删除」变成可横向比较的任务：提供人工标注的真值，统一定义 PR（保留率）/ RR（删除率）/ F1，并内置 ERASOR、Removert、DUFOMap 等方法的结果。

## 为什么复现它 Why

**所有 F1 对比的地基。** 没有同一套 GT 与同一套指标，四个清理方法的排名就不可比，H1′ 也就无从检验。它是整个 D1 链路里第一个必须跑通的东西。

## 复现目标（可验收）Goals

- [ ] 仓库跑通，`evaluate.py` 能对一条 KITTI 序列输出 PR / RR / F1
- [ ] 搞清 GT 的标注口径（哪些点被标成动态、标注覆盖哪些序列）
- [ ] 复现出论文里某一个方法的数字（误差在合理范围内即算通过）
- [ ] 记录：GT 覆盖范围之外怎么办（这是我们自己实验必然要面对的问题）

## 步骤 Steps

```bash
git clone https://github.com/KTH-RPL/DynamicMap_Benchmark code/
cd code/benchmark
pip install -r requirements.txt
# 按仓库 README 下载对应数据集，放到它要求的目录结构
python3 evaluate.py --dataset kitti --seq 00 --method <method>
```

## 坑与注意 Pitfalls

- 数据集体积大，先确认磁盘；下载脚本与目录结构以**仓库 README 为准**（会变）。
- GT 只覆盖部分序列 —— 不要假设每条序列都有真值。
- 指标定义（PR/RR/F1 的分子分母）要抄进 `results/`，否则后面和别人对比时会说不清。

## 记录 Log

> 复现时在这里补：实际命令、参数、跑出来的数字、与论文不一致的地方、失败原因。
> 不要只留在终端历史里。

| 日期 | 做了什么 | 结果 / 数字 | 结论 |
| :--- | :--- | :--- | :--- |
| | | | |
