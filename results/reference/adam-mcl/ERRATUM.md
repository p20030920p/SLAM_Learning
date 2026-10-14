# AdaM-MCL score erratum

The earlier 5.49-cell RMSE and 6.78-cell mean final error are withdrawn. The native error_position.txt files already store Euclidean distance; the legacy exporter square-rooted them again. Recomputed from all ten retained trial files: mean per-trial position RMSE 34.82 cells, mean final error 47.71 cells. Global and kidnapping sustained convergence remain 0/10 after corrected position and wrapped-angle checks. Cells are not metres and paper values are not compared.

[Per-trial source hashes and correction](score-erratum.json). Original records and videos are retained as historical artifacts; their old score fields are superseded by this correction. The terminal dashboard also had a wrong footer formula; its native numeric output and images remain useful, while corrected metrics must come from retained distance logs.

旧版 5.49 格 RMSE、6.78 格平均末帧误差撤回。作者已保存欧氏距离，旧导出器又取平方根；修正后十次运行平均 RMSE 为 34.82 格、平均末帧误差 47.71 格。正确位置误差与包裹角度检查仍为全局／绑架持续收敛 0/10；不与论文米制数值比较。旧记录原字节保留，显示指标以本勘误为准。
