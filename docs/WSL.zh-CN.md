# 后续复现的 WSL 环境

[English](WSL.md) | 中文

2026 年 10 月 7 日，本机已有 WSL 3.0.1、固件虚拟化已开，但没有注册 Linux 发行版，WSL 提示虚拟机平台未启动，当前进程不是管理员。这是准备状态，与成功的 Ubuntu CI 分开记录。

## 1. 启用平台

在仓库根目录的**管理员 PowerShell** 执行：

```powershell
.\scripts\setup_wsl.ps1 -EnablePlatform
```

脚本用 `/norestart` 请求启用 VirtualMachinePlatform，不自行提权或重启 Windows。你完成必要重启后再继续。[Microsoft 平台启用说明](https://learn.microsoft.com/en-us/windows/wsl/install-manual)给出了这一前提。

## 2. 安装 Ubuntu 22.04

```powershell
.\scripts\setup_wsl.ps1 -InstallUbuntu
wsl -d Ubuntu-22.04
```

首次启动交互创建 Linux 用户名／密码。用 `wsl --list --verbose` 检查版本 2。安装使用 `--no-launch`，依据 [Microsoft WSL 命令](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)。不加参数的脚本仅检查状态。

## 3. Linux 工作副本放在 Linux 存储

进入 Ubuntu：

```bash
sudo apt-get update
sudo apt-get install -y git curl libgl1 libgomp1 libglib2.0-0
curl -LsSf https://astral.sh/uv/0.9.2/install.sh -o /tmp/slam-study-uv-install.sh
sh /tmp/slam-study-uv-install.sh
source "$HOME/.local/bin/env"
mkdir -p ~/projects
cd ~/projects
git clone --branch codex/structural-slam-refactor https://github.com/p20030920p/SLAM_Learning.git
cd SLAM_Learning
bash scripts/setup_linux.sh
```

[uv 官方安装器](https://docs.astral.sh/uv/getting-started/installation/)固定为 CI 使用的版本。创建新的 Linux 环境，活跃代码与缓存放 Linux 文件系统，减少跨系统 I/O，依据 [Microsoft 文件系统建议](https://learn.microsoft.com/en-gb/windows/wsl/filesystems)。已有压缩包可从 `/mnt/d/workspace/be2/SLAM_Learning/.cache/downloads/00.zip` 复制到新 `.cache/downloads/`，再由 fetch 校验，不必重复下载。

## 4. 先复现，再实验

```bash
bash scripts/run_reproduction.sh --smoke
bash scripts/run_reproduction.sh
```

第二条下载／校验数据、执行两个作者方法，生成中英文汇总，不自动运行候选假设实验。改参数前保存每个运行编号。[R1–R3 阶段](PLAN.zh-CN.md)规定接下来要补的复现。

## GPU 与媒体放到后续

CPU 实验无需 CUDA。语义前端前，先在 WSL 内检查 `nvidia-smi`，再单独测试该前端 GPU 环境；Windows 有 GPU 不等于 WSL CUDA 已通过。[Microsoft GPU 支持](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute)可核查。未来语义环境与当前锁文件分开，GIF／视频位置与输入要求见[媒体索引](figures/README.zh-CN.md)。
