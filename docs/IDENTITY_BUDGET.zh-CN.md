# 对象身份与候选预算实验 v2

[English](IDENTITY_BUDGET.md)

**进行中 · AI 标注探索实验 · H1 未验证。**

## 问题

精确修正历史位姿后，在相同候选上限下，重新关联是否比固定关联恢复更多有效目标？这用于区分关联损失、坐标误差与低支持过滤的影响。单场景不能证明跨方法共性瓶颈；相同上限也不代表实际候选数、点数或内存相同。

参考仅覆盖部分可见表面，不是官方 Replica 实例 GT。物理实例恢复与类别查询分别评分，查询可命中同类任一已标实例；未标候选身份未知，不能直接算假阳性。同一物理 ID 的达标碎片超出第一个的数量计为重复余量；一个对象支持两个已标 ID 才计混合。两项诊断均受标注边界和可见性影响。

## 冻结设计

| 项目 | 设置 |
| --- | --- |
| 场景与帧 | room2；建图 0、25、…、375；参考 12、62、112、162 不进入前端／建图 |
| 目标 | [5 个 AI 实例](../annotations/room2/targets.ai-v2.1.json)，在前端输出前固定 |
| 修正 | 第 8 次观测后精确修正前缀位姿并作主评价；第 12／16 次评估持续性 |
| 条件 | 世界 x 方向 RMS 10／30 cm × 种子 417／518／619，每组另设零误差，共 28 单元 |
| 四组 | native_fixed；threshold_fixed（1.0）；visibility_fixed；oracle_replay |
| 离线读出 | 支持 ≥1／2／3 × 上限 25／50／100／不限，三个阶段共 1008 行 |
| 候选排序 | 不用标注：支持数降序、点数降序、由来源确定的 ID 升序 |

四组共用冻结前端。固定组按各自关联轨迹重建几何，保留成员、支持数和 CLIP／文本特征；oracle 重算原生关联。完整快照在读出过滤前保存来源、几何、颜色和特征；第 16 次也在最终过滤前保存，最终输出另存。读出不得修改地图。解释结果前须通过各自策略零误差、原生／oracle 和原始 batch 对齐。修正耗时包含前缀重建，不含快照 I/O；快照字节数不是运行内存。这些对照不能证明低内存修正方法可部署。

## 运行与录制

[探索协议](../configs/identity_budget_v2_exploratory.json)依据用户 2026-10-08 取消人工复核的调整执行，标注保持 `human_reviewed: false`。[确认性协议](../configs/identity_budget_v2.json)仍要求人工回执；[原始视图复核包](../annotations/review/identity-v2/index.html)与 room1 证据保留。后续重评分须另存版本并标为事后分析。

使用已固定的 Linux 环境和独立绝对输出路径。用 `fetch_delayed_scene.py` 准备固定子集，在前端执行前用 `seal_delayed_annotations.py --seal --exploratory` 封存。数据与冻结记录就绪后运行：

```bash
python scripts/check_study_resources.py
python scripts/run_identity_pipeline.py \
  --repo "$REPO" --semantic-python "$SEMANTIC_PYTHON" \
  --protocol "$REPO/configs/identity_budget_v2_exploratory.json" \
  --annotations "$REPO/annotations/room2/targets.ai-v2.1.json" \
  --data "$DATA" --freeze "$SEAL/freeze.json" \
  --native-source "$SOURCE" --weights "$WEIGHTS" \
  --output "$OUT" --recordings "$VIDEOS" --wait-idle-seconds 10800
```

资源检查返回 2 即延后。流水线每阶段最多等待三小时，不改其他任务或环境；复制源码后执行前端 → 28 单元 → 重算 → 双语图表／报告 → 真实 RViz 保存地图回放。失败换新目录，旧尝试保留。全程终端视频、日志、命令和退出记录留在本地；RViz 明确标为回放。GIF 须绑定来源哈希，科学结果 PDF 须逐页检查；两者尚未完成。[录制范围](RECORDING.zh-CN.md)。

## 决策

在相同 RMS、支持门槛和端点（恢复率或类别查询命中）下，oracle 须在两个有限上限相对每个简单对照平均改善 ≥10 个百分点，≥2／3 配对种子改善，且任何种子的已标重复或混合都不增加。通过只允许提出有界回放原型计划；打平则收窄或停止 H1。AI 标注不能确认 H1。

成果留在 `study/identity-budget-v2`。[审核约定](../AGENTS.md)要求绑定提交审核、CI 和用户明确批准后才能合并 main。[初版实现审核](reviews/IDENTITY_BUDGET_3740e51.zh-CN.md)是历史记录，不是结果报告。
