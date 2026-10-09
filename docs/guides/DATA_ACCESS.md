# Data access and input versions

English | [中文](DATA_ACCESS.zh-CN.md)

Large files stay in `/home/qzl/projects/SLAM_Author_Originals/data`, outside Git. Windows can inspect the same directory through WSL File Explorer.

## 1. KITTI and SemanticKITTI

333 original scans cover inclusive 00:4390–4530, 01:150–250 and 02:860–950. The downloader checks ZIP64 directory metadata, strict HTTP Range/ETag, member CRC/size, label point counts and extracted SHA-256. The 84,786,535,790-byte cloud archive was not downloaded in full; no full-archive hash is claimed. Label/calibration/pose archives passed complete CRC checks.

[Manifest](../../results/kitti-selected-manifest.json) · [KITTI source](https://s3.eu-central-1.amazonaws.com/avg-kitti/data_odometry_velodyne.zip) · [SemanticKITTI](https://www.semantic-kitti.org/dataset.html#download).

Current preprocessing enables the two commented interval lines in a separate copy, preserving the author's 50 m filter, labels, SuMa transformation and PCD writer. All 141 reconstructed 00 scan counts differ from the older release. A fixed first-frame SE3 still leaves about 0.273 m maximum translation residual; this input comparison is not ATE or an identified localization defect.

Historical preprocessing restores point counts but not byte identity; only historical 02 matches the nine BeautyMap Table III values. [Protocol](../reports/KITTI_PAPER_PROTOCOL.md) · [Current results](../reports/KITTI_SELECTED_RESULTS.md).

The separate `kitti-prep` environment uses av2 0.2.1 for the author's SE3 import. Six-worker prefetch downloads the same members; the primary reader independently verifies them. Connection-specific byte counts are not total traffic.

## 2. ScanNet access

No application has been signed/submitted and no ScanNet access granted. The applicant must use an institutional email and the [official Terms of Use](https://github.com/ScanNet/ScanNet#scannet-data). The blank local form is not authorization.

HOV-SG needs `.sens` and `_vh_clean_2.labels.ply` for scene0011_00, scene0050_00, scene0231_00, scene0378_00 and scene0518_00. After approval, use the supplied downloader and official SensReader, retaining versions/hashes. The documented reader targets Python 2.7 and has not run here.

Export color/depth/poses/intrinsics; depth scale is 1000. ScanNet semantic mapping does not replace separately licensed HM3D/HM3DSem hierarchy evaluation. Retain each dataset's own terms. [Detailed access record](DATA_ACCESS.zh-CN.md).

## 3. Commands

Use the shell shown by each block. Keep the order, use new output names, and check whether the task has already run before starting it.

```bash
python3 "$DOCS/src/scripts/fetch_kitti_intervals.py" --runtime "$RUNTIME" --name kitti-selected-inputs-manual-01
python3 "$DOCS/src/scripts/run_kitti_original.py" --runtime "$RUNTIME" \
  --download-name kitti-selected-inputs-manual-01 --name kitti-author-selected-manual-01
```

```bash
uv venv --python /usr/bin/python3 "$RUNTIME/envs/kitti-prep"
uv pip install --python "$RUNTIME/envs/kitti-prep/bin/python" \
  av2==0.2.1 numpy==1.26.4 scipy==1.14.1 fire==0.7.0 tqdm==4.66.5
```

```bash
python reader.py --filename "$RUNTIME/data/scannet/scans/scene0011_00/scene0011_00.sens" \
  --output_path "$RUNTIME/data/scannet/rgbd/scene0011_00" \
  --export_depth_images --export_color_images --export_poses --export_intrinsics
```
