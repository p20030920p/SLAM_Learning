<a id="mapping-hypothesis-tests"></a>

## Hypothesis

<!-- SIMPLE_HYPOTHESES_V2 -->

| Question | Hypothesis | Controls | Metrics |
| --- | --- | --- | --- |
| H1 / Q1 | Dynamic cleaning removes traces while retaining static structure and reduces held-out localization error. | Raw / SRRG | DA, SA, Eₘ, XY RMSE |
| H2 / Q2 | FAST-LIO deskew reduces motion-induced map error and improves held-out localization accuracy. | Point compensation off / on | Eₘ, Cₘ, XYZ RMSE |
| H3 / Q3 | Adding LiDAR-visible asymmetric static references reduces along-corridor localization error. | Original / landmark corridor | Eₘ, SA, along RMSE |

Goal: first measure map improvement, then test whether the same localizer has lower error on independent B.

Mirror identification and physical reflections remain open within Q3; physical evidence stays at the top.

<a id="hypothesis-math"></a>

### Mathematical form

A builds the map; B is a separate acquisition. Freeze A's map and run the same localizer on B. $`j`$ indexes the control, $`Z`$ denotes scans, $`T`$ is the sensor pose and $`p^{\ast}`$ is true position:

```math
M_j = \mathcal{B}_j\bigl(Z^A,\hat{T}_j^A\bigr)
```

```math
\hat{T}_{j,t}^B = \mathcal{L}\bigl(Z_{\leq t}^B,M_j\bigr)
```

```math
E_L(j) = \sqrt{\frac{1}{N}\sum_t\left\lVert\hat{p}_{j,t}^B-p_t^{B,\ast}\right\rVert^2}
```

```math
\Delta E_L = E_L(\mathrm{baseline})-E_L(\mathrm{method})
```

$`\Delta E_L\gt 0`$ means improved localization; lower map error $`E_M`$ with $`\Delta E_L\leq 0`$ supports only map improvement. Test these predictions:

**H1**

```math
\mathrm{DA}_{\mathrm{SRRG}}\gt\mathrm{DA}_{\mathrm{Raw}},\qquad \mathrm{SA}_{\mathrm{SRRG}}\geq\mathrm{SA}_{\mathrm{Raw}}-\varepsilon
```

```math
E_M(\mathrm{SRRG})\lt E_M(\mathrm{Raw}),\qquad\Delta E_L\gt 0
```

**H2**

```math
p_i^{\mathrm{end}}=T(t_{\mathrm{end}})^{-1}T(t_i)p_i
```

```math
E_M(\mathrm{on})\lt E_M(\mathrm{off}),\qquad\Delta E_L\gt 0
```

**H3**

```math
E_{\parallel}=\sqrt{\frac{1}{N}\sum_t\left[u^{\mathsf{T}}\left(\hat{p}_t-p_t^{\ast}\right)\right]^2}
```

```math
E_{\parallel}(\mathrm{landmark})\lt E_{\parallel}(\mathrm{original})
```

$`\varepsilon=1`$ percentage point is the static-loss tolerance; $`u`$ is the corridor direction. This SRRG comparison includes pose optimization and maintenance; deletion alone at fixed poses remains untested. Truth is used only for scoring.

<a id="hypothesis-pseudocode"></a>

### Pseudocode

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

For H3, acquire A/B in each corridor variant with the same route, speed, initial offset and localization settings.

[Experiments and new recordings](../../README.md#practice-index)

### Experiment design

| Experiment | Scene | A mapping controls | Separate B localization |
| --- | --- | --- | --- |
| H1 | Static + dynamic | Raw / SRRG | AMCL |
| H2 | Static scene: stationary, slow/fast turns, translation | FAST-LIO compensation off / on | GICP |
| H3 | Original / landmark corridor | SRRG (retain Raw control) | AMCL |

Reacquire A/B for each scene; within each scene share inputs and settings and change only the listed control. Existing 3D Raw/DUFOMap/BeautyMap tests are retained.

```powershell
./demo/record-hypotheses.ps1 -Suite results/reference/direction-YYYYMMDD-new
```
