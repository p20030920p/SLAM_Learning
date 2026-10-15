# Select metrics for the experiment's task

[Homepage metrics](../../README.md#metrics) · [Practice](../../README.md#practice-index) · [Own hypotheses](MAPPING-FOCUS.md)

Build maps in A, freeze them, then evaluate localization on independently acquired B. Show the stages in separate tables. DA/SA measure removal and retention, not geometric or localization accuracy.

| Experiment | A: mapping / cleaning | B: localization on frozen maps |
| --- | --- | --- |
| DUFOMap / BeautyMap cleaning reproduction | DA, SA | Not tested in this experiment |
| SRRG static / corridor controls | SA | XY and yaw RMSE |
| SRRG dynamic scene | DA, SA | XY and yaw RMSE |
| FAST-LIO deskew | Map geometry Eₘ; motion-phase odometry errors labelled separately | XYZ and rotation RMSE |
| IR-MCL / AdaM-MCL localization reproduction | No removal / retention scores | Position error; yaw also for IR-MCL |
| Own H1 | Dynamic: DA, SA; static: SA only | XY RMSE |
| Own H2 | Map geometry Eₘ | XY RMSE |
| Own H3 | Additional cells retained by protection | Along-corridor RMSE during limited observations |

DA = removed dynamic reference units / all dynamic reference units; SA = retained static reference units / all static reference units. Units are observed spatial support in 2D and reference points in 3D. Do not directly rank different units, datasets or thresholds. Omit DA without dynamics.

Eₘ is map-point distance RMSE to static reference geometry. B position RMSE compares estimates with truth, using XY in 2D and XYZ in 3D; H3 uses only the along-corridor component.

Display pages omit AA/HA, P95, sample counts, output coverage and redundant threshold statistics. Full scores, valid output intervals and failures remain in source records; missing outputs must not be treated as zero error.

Current B tests localization while the robot moves; complete navigation-task outcomes were not measured. Better removal / retention supports only cleaning; lower B error is needed to support downstream localization improvement.
