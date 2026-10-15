<a id="mapping-hypothesis-tests"></a>

## 假设

<!-- SIMPLE_HYPOTHESES_V2 -->

| 问题 | 一句话假设 | 对照方法 | 指标 |
| --- | --- | --- | --- |
| H1 / Q1 | 动态清图在保留静态结构的同时减少残影，并降低独立定位误差。 | Raw / SRRG | DA、SA、Eₘ、XY RMSE |
| H2 / Q2 | FAST-LIO去畸变能降低运动造成的地图误差，并提高独立定位精度。 | 点补偿关 / 开 | Eₘ、Cₘ、XYZ RMSE |
| H3 / Q3 | 长廊中增加雷达可见的非对称静态参照，能降低沿廊定位误差。 | 原长廊 / 加参照长廊 | Eₘ、SA、沿廊 RMSE |

目标：先检查地图是否改善，再检验同一定位器在独立B中的误差是否下降。

镜面识别与真实反射仍是Q3中待验证的部分，实物证据保留在首页开头。

<a id="hypothesis-math"></a>

### 数学表达

A用于建图，B是另一次采集；冻结A的地图后，用相同定位器处理B。$j$是对照方法，$Z$是扫描，$T$是传感器位姿，$p^*$是位置真值：

$$
M_j=\mathcal B_j(Z^A,\hat T_j^A),\qquad
\hat T^B_{j,t}=\mathcal L(Z^B_{\le t},M_j).
$$

$$
E_L(j)=\sqrt{\frac1N\sum_t\|\hat p^B_{j,t}-p^{B,*}_t\|^2},\qquad
\Delta E_L=E_L(\mathrm{baseline})-E_L(\mathrm{method}).
$$

$\Delta E_L>0$表示定位改善；地图误差$E_M$下降但$\Delta E_L\le0$时，只支持建图改善。下式是要检验的预测：

$$
\begin{aligned}
H1:\;& DA_{\rm SRRG}>DA_{\rm Raw},\quad SA_{\rm SRRG}\ge SA_{\rm Raw}-\varepsilon,
\quad E_M({\rm SRRG})<E_M({\rm Raw}),\quad\Delta E_L>0;\\
H2:\;&p_i^{\rm end}=T(t_{\rm end})^{-1}T(t_i)p_i,
\quad E_M({\rm on})<E_M({\rm off}),\quad\Delta E_L>0;\\
H3:\;&E_{\parallel}({\rm landmark})<E_{\parallel}({\rm original}),
\quad E_{\parallel}=\sqrt{\frac1N\sum_t[u^T(\hat p_t-p_t^*)]^2}.
\end{aligned}
$$

$\varepsilon=1$个百分点为本轮静态损失容差；$u$为走廊方向。SRRG本轮是端到端对照，包含位姿优化与地图维护；给定相同位姿的纯删除消融仍待做。真值仅用于评分。

<a id="hypothesis-pseudocode"></a>

### 伪代码

```text
for scene in [static, dynamic, motion, corridor, corridor_landmarks]:
    controls = methods_for(scene)
    A, maps = record_A_and_build_maps(scene, controls)
    map_metrics = score_and_freeze(maps)
    B = record_new_localization_session(scene)
    poses = same_localizer_for_all_maps(B, maps)
    report(map_metrics, score_on_common_times(poses, B.truth))
    save_native_recordings_and_input_hashes()
compare_corridor_variants_on_common_elapsed_times()
```

H3分别采集原长廊与加参照场景的A/B，保持路线、速度、初始偏移和定位参数相同。

[实验与新录像](../HOME.zh-CN.md#practice-index)

### 实验设计

| 实验 | 场景 | A建图对照 | 独立B定位 |
| --- | --- | --- | --- |
| H1 | 静态＋动态 | Raw / SRRG | AMCL |
| H2 | 静态场景：静止、慢转、快转、平移 | FAST-LIO点补偿关 / 开 | GICP |
| H3 | 原长廊 / 加非对称参照 | SRRG（Raw同时保留） | AMCL |

每个场景重新采集A/B；同一场景各方法共享输入和参数，仅改变表中的对照因素。原三维Raw／DUFOMap／BeautyMap测试保留。

```powershell
./demo/record-hypotheses.ps1 -Suite results/reference/direction-YYYYMMDD-new
```
