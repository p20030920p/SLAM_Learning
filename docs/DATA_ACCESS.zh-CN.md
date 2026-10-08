# 新增原始数据与访问步骤

KITTI 下载和原始预处理在本机 Linux 文件系统执行，大文件不放进 Git。目录：`/home/qzl/projects/SLAM_Author_Originals/data/kitti-original`。Windows 文件资源管理器可访问 `\\wsl.localhost\Ubuntu-22.04\home\qzl\projects\SLAM_Author_Originals\data\kitti-original`。

2026-10-09 已下载 333 帧原始扫描，逐成员核对原包 CRC、字节数和标签点数，并记录 SHA-256；主读取器和并行预取的 333 个 SHA-256 记录全部一致。标签、标定和两套位姿归档完整通过 CRC。01/02 作者预处理、方法运行及原始评分已完成。完整证据见 [下载清单](../evidence/kitti-selected-manifest.json)。

## KITTI / SemanticKITTI

| 数据 | 官方来源 | 本轮用途 |
|---|---|---|
| 原始 Velodyne 点云 | [KITTI 官方 S3](https://s3.eu-central-1.amazonaws.com/avg-kitti/data_odometry_velodyne.zip)，也由 [TULIP 作者仓库](https://github.com/ethz-asl/TULIP#data-preparation)引用 | 00 的 4390–4530、01 的 150–250、02 的 860–950，均包含端点，共 333 帧 |
| 语义标签与 SuMa 位姿 | [SemanticKITTI 原始 ZIP](https://www.semantic-kitti.org/assets/data_odometry_labels.zip) | 作者默认预处理与静态/动态 GT；低 16 位为类别，高 16 位为实例 |
| 标定 | [KITTI 官方 ZIP](https://s3.eu-central-1.amazonaws.com/avg-kitti/data_odometry_calib.zip) | 将提供的相机位姿转换至 LiDAR 坐标系 |
| KITTI 真值位姿 | [KITTI 官方 ZIP](https://s3.eu-central-1.amazonaws.com/avg-kitti/data_odometry_poses.zip) | 单独保留，供位姿来源实验；不覆盖 SemanticKITTI 位姿 |

官方点云归档为 84,786,535,790 字节。下载器从原始 ZIP64 目录定位所需成员，通过严格 HTTP Range / ETag 获取，每个成员核对 ZIP CRC、字节数并记录本地 SHA-256。未下载整份点云归档，不能宣称核验了整包 SHA-256。标签、标定及真值位姿的 ZIP 则全量下载并检查全部 CRC。依据：[SemanticKITTI 数据格式与许可](https://www.semantic-kitti.org/dataset.html#download)。数据保留其非商业署名、相同方式共享许可。

作者当前 `extract_semkitti.py` 的 01/02 帧段被注释。本轮只在副本中启用这两行，保留原来的 50 m 范围、近车体标签处理、SuMa 位姿变换与二进制 PCD 写出，保存配置 diff。先重建 00 并逐帧比较发布包的几何和标签，再运行 01/02。执行记录中会明确一致项和差异，不能仅凭帧数相同宣称与论文完全一致。

协议检查已发现差异：00 的 004390 原始帧和发布帧均为 125,883 点，当前作者 50 m 过滤后为 124,662 点。完整重建后，141 个扫描的点数均与发布包不同。发布 `VIEWPOINT` 与本轮官方 SuMa 位姿也有差异；用第一帧确定一个固定左乘 SE3 后，141 帧最大平移残差仍约 0.273 m。这是两份输入约定的比较，不是定位 ATE，原因尚未确定。[协议检查及输入哈希](../evidence/runs/kitti-protocol-comparison-01/protocol-comparison.json)、[完整 00 预处理验证](../evidence/runs/kitti-author-selected-02/00-validation/validation.json)。原始发布包上的论文匹配结果保留，新预处理结果单列，暂不认定数据版本等价。

01/02 两种方法与三组 BeautyMap XY 网格的原始评分现已全部完成，见 [结果与论文数值差距](KITTI_SELECTED_RESULTS.zh-CN.md)。

在 Windows 打开 Ubuntu 后，设置 [运行手册](RUNBOOK.zh-CN.md)中的 `RUNTIME` / `DOCS`，新建运行名重做：

```bash
python3 "$DOCS/scripts/fetch_kitti_intervals.py" --runtime "$RUNTIME" --name kitti-selected-inputs-manual-01
python3 "$DOCS/scripts/run_kitti_original.py" --runtime "$RUNTIME" \
  --download-name kitti-selected-inputs-manual-01 --name kitti-author-selected-manual-01
```

预处理单独使用 `envs/kitti-prep`，其中 `av2==0.2.1` 提供作者导入的 SE3，完整解析版本保存在 `kitti-prep-environment.txt`。原始方法仍使用已验证的 `envs/lidar` 与 C++ 二进制。在新工作区需先创建预处理环境：

```bash
uv venv --python /usr/bin/python3 "$RUNTIME/envs/kitti-prep"
uv pip install --python "$RUNTIME/envs/kitti-prep/bin/python" \
  av2==0.2.1 numpy==1.26.4 scipy==1.14.1 fire==0.7.0 tqdm==4.66.5
```

为减少逐文件连接等待，本轮还运行 `prefetch_kitti_points.py --runtime "$RUNTIME" --workers 6` 并行取得同一组原始成员。它检查本地 ZIP 头、中央目录长度、ETag 和 CRC 后原子写入；主下载器仍独立复查每个文件和标签点数。预取传输记录在 `kitti-point-prefetch.json`，主读取器字节数单列，不能将其中一个数字当作所有连接的总流量。

01/02 默认运行之外，02 另比较公开 `xy_resolution=0.5/1/2 m` 参数，保持 README 的 `h_res=0.5 m`、`dis_range=40 m`。论文表 III 未单列 z 分辨率，本轮将这一选择写入记录，不把未知参数说成已验证；并行任务与 CPU 限额下的耗时不用于论文速度对照。

## ScanNet：需要本人申请访问

[ScanNet 官方仓库](https://github.com/ScanNet/ScanNet#scannet-data)要求申请人使用机构邮箱，填写并签署 [Terms of Use](https://kaldir.vc.cit.tum.de/scannet/ScanNet_TOS.pdf)，发送至 `scannet@googlegroups.com`。空白表已下载到本机 `D:\workspace\be2\SLAM_Private\ScanNet_TOS.blank.pdf`，SHA-256 为 `aba2dbeb1e71bede5261d965c844d1e4861c26ca2cf23c9077e6d16013167715`。当前未提交申请、未签署协议，尚无 ScanNet 数据访问授权。

HOV-SG 固定版 [README](https://github.com/hovsg/HOV-SG/blob/d6e65a53c8be6faec3f01f00d1644d967f89e605/README.md#scannet)使用：

| 场景 | 至少需要的原始输入 |
|---|---|
| scene0011_00 | `.sens` 与 `_vh_clean_2.labels.ply` |
| scene0050_00 | `.sens` 与 `_vh_clean_2.labels.ply` |
| scene0231_00 | `.sens` 与 `_vh_clean_2.labels.ply` |
| scene0378_00 | `.sens` 与 `_vh_clean_2.labels.ply` |
| scene0518_00 | `.sens` 与 `_vh_clean_2.labels.ply` |

获批后，用官方回复提供的下载器按场景下载至 `data/scannet/scans/<scene>/`；下载器的具体版本、参数与校验信息将在获得文件后记录。不要用非官方镜像代替数据访问申请。

然后按 [官方 SensReader](https://github.com/ScanNet/ScanNet/tree/master/SensReader/python)导出每个 `.sens`：

```bash
python reader.py --filename "$RUNTIME/data/scannet/scans/scene0011_00/scene0011_00.sens" \
  --output_path "$RUNTIME/data/scannet/rgbd/scene0011_00" \
  --export_depth_images --export_color_images --export_poses --export_intrinsics
```

官方导出器注明开发测试环境为 Python 2.7；本机尚未执行这一入口。拿到数据后须先验证兼容环境，保留必要兼容副本的 diff。导出应包含 `color/*.jpg`、`depth/*.png`、`pose/*.txt` 和 `intrinsic/`，深度尺度为 1000；HOV-SG 读取两个内参文件。评价还必须保留每个场景对应的 GT labels PLY。

ScanNet 只补齐语义分割数据。HOV-SG 多楼层/房间/对象的层级评价仍需要单独获授权的 HM3D / HM3DSem；Replica 或 ScanNet 语义图不能代替该评价。
