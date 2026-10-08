# 每篇复现的录制与报告

[English](RECORDING.md) | 中文

## 本地全过程执行录制

另外录制了四份**真实终端全过程视频**，覆盖命令启动、作者流程运行、可见的退出码 0 和结尾停留。按正常经过时间录制独立 Linux 终端；原有 GIF 仍是地图输出回放。全过程视频展示执行日志，不是实时三维建图界面或实物导航。

| 方法 | 视频时长（秒） | 作者命令（秒） |
| --- | ---: | ---: |
| DUFOMap | 36.6 | 32.631 |
| BeautyMap | 42.0 | 38.164 |
| ConceptGraphs，40 次观测 | 256.6 | 253.019 |
| HOV-SG，8 次观测 | 168.8 | 165.134 |

在采集机器打开 `D:/workspace/be2/SLAM_Recordings/2026-10-08/VIDEO_INDEX.md`。索引内每个目录都有 `full-session.mp4`、`terminal.raw`、`terminal.time`、命令、退出／录制 JSON 及首／中／尾检查帧。视频在 Git 目录外本地留存；[轻量证据及原生运行记录](../results/reference/full-recordings/record.json) 绑定视频字节、日志与检查帧。未通过检查的早期录制保留在本地，不列入交付索引。

`scripts/record_session.py` 使用 Xvfb、xterm、util-linux `script`、随机 Xauthority cookie 和单调时钟帧调度。录制开始后才放行命令，刷新 PTY，只追踪当前方法的新日志，检查整段解码、时长及非空白帧；捕获独立画面，不录用户桌面。`scripts/import_full_recordings.py` 将大视频记为仅本地资产。

```bash
sudo apt-get install xvfb xterm xauth ffmpeg util-linux
# 录制环境需有支持 XCB 的 Pillow。
.venv/bin/python scripts/record_session.py \
  --output /mnt/d/workspace/be2/SLAM_Recordings/new-dufomap \
  -- .venv/bin/python -m slam_learning.cli run --method dufomap
# ConceptGraphs 命令：.venv-semantic/bin/python scripts/run_conceptgraphs.py
# HOV-SG 命令：.venv-hovsg/bin/python scripts/run_hovsg.py
```

## 主页 GIF、回放视频与 PDF

参考你给的 [Sim2Real-AlgoBench](https://github.com/p20030920p/Sim2Real-AlgoBench)，固定快照 `53324d40def0dd753b4a99021b8fe596955a1ecd`：每个方法有 MP4、轻量 GIF 和机器可读元数据，并检查输出完整与面板空白；没有复制其源码。

这些视频是**作者实测输出的回放**。LiDAR 视频按选定原始扫描展示最终地图的 PCL 标签；语义视频把原生 SAM 观测与最终地图、查询候选并排展示。它们不表示实时导航、在线地图演变或算法 FPS。真值标签不输入作者流程。

```bash
# 在独立语义环境；提供有本地地图的完整记录，不能用只导出的轻量记录替代。
uv pip install --python .venv-semantic/bin/python imageio-ffmpeg==0.6.0
.venv-semantic/bin/python scripts/render_paper_media.py dufomap results/runs/REPLAY_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py beautymap results/runs/REPLAY_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py conceptgraphs results/runs/CG_ID/record.json
.venv-semantic/bin/python scripts/render_paper_media.py hovsg results/runs/HOV_ID/record.json
```

渲染先核查来源产物；H.264 全部解码，并检查首／中／尾帧方差以排查空白。`render.json` 保存来源帧、固定视角、坐标转换、查询、播放配置和哈希；人工也检查海报及代表视频帧。先导出记录，再把字节相同资产放主页。

中英文 PDF 由 `scripts/build_paper_pdfs.py` 根据论文卡及验证过的运行汇总生成，包含范围、原输出、命令、数值、限制及假设关系。每页渲染检查，不能只看提取文本。媒体／PDF 记录绑定全部发布字节与输入。

```bash
uv venv .venv-reports --python 3.10
uv pip install --python .venv-reports/bin/python -r environments/reports/requirements.txt
.venv-reports/bin/python scripts/build_paper_pdfs.py --publish
# 用 Poppler 渲染每一页，检查图像后再导出记录。
```

可传 `--cjk-font /path/to/licensed-font.ttc` 嵌入 TrueType 字体子集。本次 PDF 使用该 Windows 安装的微软雅黑并记录字体哈希，不把字体文件上传 Git；默认使用 STSong CID 回退。英文版中的中文版本链接也使用中文字体。

**坐标核查：** ConceptGraphs 默认加载器会归一化 `__getitem__` 返回的位姿，但本次批处理入口明确读取绝对 `dataset.poses`。渲染前将保存的 39 个矩阵（观测 1–39；第 0 帧初始化无快照）逐个对照提供位姿，因此原 `center_world_m` 已是 Replica 世界坐标，不额外施加第一帧变换。HOV-SG 也读取绝对轨迹矩阵。应追踪实际入口，不能只看加载器默认值。

未来实物视频再加入传感器原输入和独立事件／标注视角。固定相机与坐标轴，显示会话编号，区分提供／估计／参考位姿。录制是验证运行后的交付环节，不代表论文全部任务已复现。
