# 对象身份与候选预算实验 v2

[English](IDENTITY_BUDGET.md)

**状态：实现与原始标注准备阶段；H1 仍为候选。** 用户于 2026-10-08 明确不再人工复核，授权仅在实验分支继续。原人工复核协议保留；新增 AI-only 探索协议不能冒充原确认性实验。未授权合并主分支。

## 问题与边界

四组都得到相同精确历史位姿后，在相同候选数量上限下，重新关联是否能恢复更多已标有效目标？这用于区分历史身份决策损失、坐标误差，以及单纯多暴露低支持碎片的收益。相同上限不等于总内存、点数或实际候选数相同，必须分别报告。单场景也不能证明四种方法的共性瓶颈或泛化。

标注仅覆盖部分可见表面，不是官方 Replica 实例 GT。类别查询与物理实例恢复分别评分；类别查询命中同类别任一已标实例即可。未标候选身份未知，不能自动算假阳性。同一物理 ID 的多个达标碎片，超出第一个的数量为重复余量；一个对象支持两个已标 ID 才计混合。两项诊断均受部件定义与不完整可见性影响。

## 固定设计

| 项目 | 声明 |
| --- | --- |
| 场景 | room2；看到输出后不能换场景 |
| 建图帧 | 0、25、…、375，共 16 次观测 |
| 独立参考帧 | 12、62、112、162；不进入前端或建图 |
| 实例 | 5 个 AI 草稿：blue_vase、bird_figurine、brown_jar、fish_figurine、chair |
| 修正 | 第 8 次观测后立即精确修正前八个位姿 |
| 误差条件 | 世界 x 方向 RMS 10／30 cm × 种子 417／518／619；每组一个零误差控制 |
| 四组 | native_fixed；threshold_fixed（1.0）；visibility_fixed；oracle_replay |
| 建图单元 | 28；失败记录保留，不覆盖 |
| 读出 | 支持数 ≥1／2／3 × 候选上限 25／50／100／不限，仅离线扫描 |
| 排序 | 检测支持数降序、点数降序、由来源确定的对象 ID 升序 |
| 主评价 | 修正刚发生时（第 8 次）；第 12／16 次仅作持续性分析 |

固定组三组按各自原始关联轨迹重建几何，保留原成员及原 CLIP／文本特征。Oracle 在精确位姿上重新计算原生关联。四组共用冻结前端。完整前缀重建需要计算与数据存储，这个强坐标对照不是可部署的低内存方法。

完整快照保存来源 ID、支持数、点云几何／颜色、CLIP／文本特征与输入哈希。第 16 次的完整状态在**最终过滤前**保存，并与原生最终处理后的校验快照区分；固定的原生周期后处理不变。读出不得修改这些状态。快照字节数仅表示序列化大小，不代表完整运行内存。修正耗时不含快照 I/O，但包含完整前缀重建。

解释结果前，必须通过零误差下各自策略修正等价、原生／oracle 等价及作者原始 batch 对齐。每个误差条件的固定组均断言历史成员、支持数、特征不变。CPU 契约测试不能替代这些原生运行校验。

## 标注与用户调整

[复核包](../annotations/review/identity-v2/index.html) 含原始 RGB、草稿边界、深度预览和可编辑表单。保留的[确认性协议](../configs/identity_budget_v2.json) 仍要求真实人工回执，才能封存或运行前端，不会静默接受探索标注。

[用户调整后的探索协议](../configs/identity_budget_v2_exploratory.json) 在封存、前端、建图入口均须显式传入 `--exploratory`。[AI 标注](../annotations/room2/targets.ai-v2.json) 保持 `human_reviewed: false`，冻结记录与每次运行均声明 `ai_only_exploratory`。AI 原图检查不能替代独立人工复核。room1 原始标注与分数保持不变；后续部件定义修订只能保存为新标注版本，并明确标为事后分析。

## 运行与录制

使用独立 Linux 运行目录和已固定的现有语义环境，不安装或修改另一窗口的环境。以下输出均在本研究独立目录且不提交 Git；可只读复用原始数据。每个重任务前先运行：

```bash
python scripts/check_study_resources.py
```

返回 2 表示应延后重任务，不停止其他进程、不改其环境、不争抢 GPU。用 `fetch_delayed_scene.py --protocol … --output …` 准备固定子集；`--archive` 可只读复用已下载的官方 ZIP。先提交协议，再准备原始数据；在观察前端输出前封存标注。

```bash
python scripts/seal_delayed_annotations.py --protocol configs/identity_budget_v2_exploratory.json \
  --annotations annotations/room2/targets.ai-v2.json --data "$DATA" \
  --output "$SEAL" --seal --exploratory
python scripts/record_session.py --output "$FRONT_VIDEO" --cwd "$REPO" -- \
  "$SEMANTIC_PYTHON" scripts/prepare_delayed_frontend.py \
  --protocol configs/identity_budget_v2_exploratory.json --annotations annotations/room2/targets.ai-v2.json \
  --data "$DATA" --freeze "$SEAL/freeze.json" --native-source "$SOURCE" \
  --weights "$WEIGHTS" --output "$FRONT" --exploratory
python scripts/record_session.py --output "$MAP_VIDEO" --cwd "$REPO" -- \
  "$SEMANTIC_PYTHON" scripts/run_identity_budget.py \
  --protocol configs/identity_budget_v2_exploratory.json --annotations annotations/room2/targets.ai-v2.json \
  --data "$DATA" --freeze "$SEAL/freeze.json" --frontend "$FRONT" \
  --weights "$WEIGHTS" --output "$RUN" --exploratory
python scripts/analyze_identity_budget.py --run "$RUN" --data "$DATA" --output "$ANALYSIS"
```

变量须为本阶段明确的绝对路径，不能使用共享运行目录。失败后换新尝试目录。全程实时终端 MP4、日志、时间、命令与退出记录留在本地；录制器使用独立 X 显示，不录用户桌面。另录真实 RViz 三维查看过程，明确标注为**保存地图回放**，不能称为实时推理。短 GIF 必须绑定真实源记录哈希，说明范围，并另外保留全程视频。最终 PDF 逐页视觉检查。运行未完成前不宣称已有新结果媒体或科学结果 PDF。

## 决策与发布

在同一 RMS、同一支持门槛、同一端点（实例恢复或类别查询命中）下，oracle 须在至少两个有限候选上限，相对每个简单对照平均改善 ≥10 个百分点；每次比较至少 2／3 配对种子同向改善。每个种子的已标重复余量与混合对象数都不得增加。不能拼接不同支持门槛或不同端点，凑出两个合格预算。通过只允许提出有界回放原型计划，仍未验证 H1；尤其 AI-only 标注仅供探索。简单对照打平即收窄或停止 H1。

成果留在 `study/identity-budget-v2`。[工作约定](../AGENTS.md) 与 PR 模板要求绑定提交的审核、CI、证据、双语一致性及媒体来源；新增修改重新审核。草稿 PR 可包含探索结果，但不能将其作为人工验证的确认性实验。合并主分支始终须用户另行明确批准。
