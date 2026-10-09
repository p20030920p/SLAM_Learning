# Camera round 4 and historical L2 recheck

English | [中文](CAMERA_TEST_ROUND4.zh-CN.md)

Two camera-fixed declarations were followed by foreground/background activity. Neither recording is a clean-static scene; original raw data and failures remain preserved.

## 1. Same-recording observations

| Session | Live RGB-D max translation / rotation | Offline stereo max translation / rotation |
| --- | --- | --- |
| Foreground activity | 7.77 cm / 11.63° | 1.37 cm / 2.15° |
| Background activity | 2.06 mm / 0.387° | 1.66 mm / 0.249° |

Modalities, sampling and execution paths differ; this is not a fair algorithm ranking. The first RGB-D run retains a tracking spike and LOST event. The second has 98.78% steady usable coverage; small excursions do not make the scene fully static or establish ATE/RPE.

[First evidence](../evidence/camera-fixed-round4-20261009.json) · [Second evidence](../evidence/camera-background-and-l2-recheck-20261009.json). The corrected RGB contact sheets replace a rejected depth-panel crop; both reviews remain traceable.

## 2. Historical L2 failure and next check

The physical serial port opened but received only 32 bytes, zero valid packets/points, followed by timeout. Zero CRC errors with zero packets is not success. A later independent UART check reproduced it; subsequent [low-light tests](POSTFALL_LOWLIGHT.md) recovered streaming without rewriting the failure.

Keep sensor, scene, lighting and parameters fixed, remove people/reflections and repeat 60 s with <5 cm/<2° and >95% usable-tracking targets. No controlled test yet identifies a unique failure cause. [Full session record](CAMERA_TEST_ROUND4.zh-CN.md).
