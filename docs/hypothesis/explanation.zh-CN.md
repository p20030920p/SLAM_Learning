<!-- HYPOTHESIS_PART:common -->
A建图，B独立采集；$M_0$为基线，$M_1$为干预图。冻结地图后，共用B扫描、里程计、AMCL参数与初始化；真值仅用于评分。

| 符号 | 含义 |
| --- | --- |
| $T_k^o,T_k$ | 第$k$帧轮速／修正传感器位姿，均为传感器系到地图系的变换 |
| $c,\mathbf x_c,b$ | 5 cm栅格、格中心、0.5秒时间箱 |
| $\mathbf1[\cdot],M$ | 条件指示函数、占据格中心点集；坐标单位为m |

地图与静态评分参照须非空；评分使用同一坐标系和膨胀前点集，AMCL地图生成规则相同。变换按齐次坐标表示，距离取XY。

**冻结地图后的XY定位RMSE：**

$$
E_{{\rm loc},m}=\sqrt{\frac{1}{|\mathcal T|}\sum_{k\in\mathcal T}\|\hat{\mathbf p}_{m,k}-\mathbf p_k^*\|_2^2}.
$$

$\hat{\mathbf p}_{m,k},\mathbf p_k^*$为估计与真值位置；$\mathcal T$为两组共同有效时刻：预热5秒后10 Hz采样，输出滞后不超过0.15秒。多轮合并共同样本；不衡量输出成功率或导航到达率。
<!-- /HYPOTHESIS_PART:common -->

<!-- HYPOTHESIS_PART:h1 -->
**H1：扫描位姿修正与动态残影清理。** Raw只按轮速位姿累积；干预增加以下对齐与过滤。

轮速增量提供初值；令$\mathbf p=T_k\mathbf z$，$\mathbf z$为扫描点，$\mathbf q$为前序参照中的最近点：

$$
\begin{aligned}
T_{k,0}&=T_{k-1}(T_{k-1}^o)^{-1}T_k^o,\\
w_{\mathbf p}&=\min\!\left(1,\frac{0.05}{\max(\|\mathbf p-\mathbf q\|_2,10^{-9})}\right).
\end{aligned}
$$

**鲁棒对齐：**$\mathcal C_k$为筛选后的对应点对；参照来自前序保留地图中至少获3个时间箱邻域支持的位置。迭代求二维刚体增量并更新位姿，参照不足或修正过大时退回轮速预测。

$$
\begin{gathered}
\boxed{\boldsymbol{\Delta T=\arg\min_{U\in\mathrm{SE}(2)}\sum_{(\mathbf p,\mathbf q)\in\mathcal C_k}w_{\mathbf p}\|U\mathbf p-\mathbf q\|_2^2}}\\
T_k\leftarrow\Delta T T_k.
\end{gathered}
$$

在修正位姿下累计直接命中$h$、10 cm邻域命中$s$和空闲穿越$f$；每类证据每箱最多计一次，射线在回波前15 cm停止：

$$
\begin{aligned}
h(c)&=\sum_b\mathbf1[\text{hit at }c\text{ in bin }b],\quad\widetilde M=\{\mathbf x_c:h(c)>0\},\\
s(c)&=\sum_b\mathbf1[\exists c':\|\mathbf x_{c'}-\mathbf x_c\|_2\le0.10,\ \text{hit at }c'\text{ in bin }b],\\
f(c)&=\sum_b\mathbf1[\text{free ray through }c\text{ in bin }b].
\end{aligned}
$$

**占据保留规则：**仅当$f\ge3$且$f\ge1.5s$时删除；命中少本身不触发删除。保留图及其时序支持用于下一帧对齐。

$$
\boxed{\boldsymbol{M_1=\{\mathbf x_c\in\widetilde M:f(c)<3\ \lor\ f(c)<1.5s(c)\}}}
$$

评分共用A的静态参考$S$与历史动态参考$D$，按10 cm格去重；$D$须经后续射线验证为空，且不与静态支持或当前障碍重叠。令$r=0.15\,\mathrm m$：

$$
\begin{aligned}
d(\mathbf q,M)&=\min_{\mathbf x\in M}\|\mathbf q-\mathbf x\|_2,\\
\mathrm{SA}(M)&=\frac{\sum_{\mathbf q\in S}\mathbf1[d(\mathbf q,M)\le r]}{|S|},\\
\mathrm{DA}(M)&=\frac{\sum_{\mathbf q\in D}\mathbf1[d(\mathbf q,M)>r]}{|D|}.
\end{aligned}
$$

SA为静态覆盖率，DA为残影参考位置的清除率，均非几何精度；公式取0–1，表格用百分数，$D$为空时不计DA。**H1要求三项同时成立：**

$$
\mathrm{DA}(M_1)>\mathrm{DA}(M_0),\qquad\mathrm{SA}(M_1)\ge\mathrm{SA}(M_0)-0.01,\qquad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$

其中0.01为1个百分点；对齐与清理的贡献通过消融区分。
<!-- /HYPOTHESIS_PART:h1 -->

<!-- HYPOTHESIS_PART:h2 -->
**H2：逐点运动补偿。**$\mathbf z_i$为$t_i$采集的齐次点，$\hat T(t)$为轮速插值得到的传感器到地图变换，$t_e$为扫描末时刻：

$$
\boxed{\boldsymbol{\bar{\mathbf z}_i=\hat T(t_e)^{-1}\hat T(t_i)\mathbf z_i}}
$$

$M_0$不补偿，$M_1$先统一到$t_e$；两者均以$\hat T(t_e)$融合，不开启H1过滤。该式补偿机器人运动。用本项A的静态支持$S$评价单向地图误差：

$$
E_{\rm map}(M)=\sqrt{\frac1{|M|}\sum_{\mathbf x\in M}d(\mathbf x,S)^2}.
$$

该指标不评价完整性；地图及静态参照须非空，空图记为建图失败。**H2要求地图与独立定位误差同时下降：**

$$
E_{\rm map}(M_1)<E_{\rm map}(M_0)\quad\land\quad E_{{\rm loc},1}<E_{{\rm loc},0}.
$$
<!-- /HYPOTHESIS_PART:h2 -->

<!-- HYPOTHESIS_PART:comparison -->
**设计差异：邻域时序证据同时用于配准参照筛选和残影删除。** 与SRRG仅比较思路；尚未证明文献首创或指标优势。[SRRG原文，第III节](https://iris.uniroma1.it/handle/11573/1340118)。

| 方面 | SRRG | 当前H1 |
| --- | --- | --- |
| 配准 | 点及法向对应，结合里程计 | 对时序支持位置做鲁棒点对点配准 |
| 地图维护 | 共同视角投影、距离比较与点云融合 | 时间箱累计邻域命中与空闲反证，满足阈值才删除 |
| 系统范围 | 位姿图优化与长期多会话维护 | 局部逐帧处理，以独立B检验地图对定位的影响 |

H2采用标准相对位姿补偿，不作为独立创新点。
<!-- /HYPOTHESIS_PART:comparison -->
