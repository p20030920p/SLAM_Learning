# WSL environment for the next reproductions

English | [中文](WSL.zh-CN.md)

On 7 October 2026 this host has WSL 3.0.1 and firmware virtualization enabled, but no registered Linux distribution. WSL reports that its virtual-machine platform is not active. The current process is not elevated. This is preparation status, separate from the successful Ubuntu CI runs.

## 1. Activate the platform

Run from an **administrator PowerShell** in this checkout:

```powershell
.\scripts\setup_wsl.ps1 -EnablePlatform
```

The script requests VirtualMachinePlatform with `/norestart`. It never elevates itself or restarts Windows. Complete the required restart yourself before the next step. These requirements follow [Microsoft's platform activation instructions](https://learn.microsoft.com/en-us/windows/wsl/install-manual).

## 2. Install Ubuntu 22.04

```powershell
.\scripts\setup_wsl.ps1 -InstallUbuntu
wsl -d Ubuntu-22.04
```

The first launch creates your Linux username/password interactively. Check `wsl --list --verbose`; the distribution should use version 2. The install uses `--no-launch`, as documented in [Microsoft's WSL commands](https://learn.microsoft.com/en-us/windows/wsl/basic-commands). The default script invocation only inspects state.

## 3. Keep the Linux checkout on Linux storage

Inside Ubuntu:

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

The [official uv installer](https://docs.astral.sh/uv/getting-started/installation/) is pinned to the CI version. Create a fresh Linux environment. Keeping active code/cache under the Linux filesystem avoids repeated cross-filesystem I/O; this follows [Microsoft's filesystem guidance](https://learn.microsoft.com/en-gb/windows/wsl/filesystems). Windows data may be copied from `/mnt/d/workspace/be2/SLAM_Learning/.cache/downloads/00.zip` into the new `.cache/downloads/`, then reverified by `fetch`.

## 4. Reproduce before experimenting

```bash
bash scripts/run_reproduction.sh --smoke
bash scripts/run_reproduction.sh
```

The second command downloads/verifies data and runs the two author methods, then writes English and Chinese ledgers. It does not automatically run the candidate-hypothesis experiments. Save each run ID before changing parameters. [Stages R1–R3](PLAN.md) specify the next reproduction work.

## GPU and media later

The CPU suite requires no CUDA. Before a semantic frontend, check `nvidia-smi` inside WSL and test that frontend's GPU environment separately; Windows GPU availability alone is not a completed WSL CUDA check. See [Microsoft GPU support](https://learn.microsoft.com/en-us/windows/wsl/tutorials/gpu-compute). Keep the future semantic environment separate from the current lockfile. GIF/video positions and input requirements are in [the media index](figures/README.md).
