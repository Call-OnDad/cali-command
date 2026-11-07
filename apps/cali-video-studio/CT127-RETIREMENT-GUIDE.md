# CT127 Retirement & Decommissioning Guide

## Overview
Previously, Cali's video rendering and audio pipeline ran on a dedicated Proxmox container **CT127** (`4 vCPU / 6GiB RAM / 64GiB disk`).

With the deployment of the standalone **Cali Video & Media Studio** (`apps/cali-video-studio`), all capabilities now run natively on Antony's desktop workstation with NVIDIA GPU NVENC acceleration.

---

## 1. Feature Parity Verification

| Capability | Old CT127 Container | New Native Cali Video Studio |
| :--- | :--- | :--- |
| **Speech Engine** | VoiceStudio (CPU loopback) / Piper | **Native Piper TTS** with CUDA GPU / CPU (`-16 LUFS` normalized) |
| **Video Assembly** | FFmpeg CPU (slow, 4-core limit) | **Local FFmpeg with NVIDIA NVENC (`h264_nvenc`)** |
| **Pan / Zoom Easing** | `camera.py` Ken Burns crop | **Hardware zoompan & Lanczos scaling** |
| **Subtitle Burn-in** | Rhubarb / custom SRT | **High-visibility styled subtitles (SRT)** |
| **Branded Bumper** | 3s Arthur/Cali v6 standard | **Native 3s Cali Media opener bumper** |
| **Media Library** | Web interface on port 8780 | **Direct playback of 766 mascot videos + 241 guides** |
| **Batch GPU Offload** | None (limited to CT127 CPU) | **1-Click Google Colab Batch Manifest Export** |

---

## 2. Safe Decommissioning Steps on Proxmox

Follow these simple steps to decommission CT127 and recover 64GB of storage and 6GB of RAM:

### Step 1: Run a Test Render
1. Double-click `Launch-Studio.cmd` in `d:\The Cali Project\apps\cali-video-studio`.
2. In the browser (`http://127.0.0.1:8790`), click **"Render with NVENC GPU"**.
3. Confirm video playback and audio clarity.

### Step 2: Stop Container CT127
Open your Proxmox web shell or SSH to your Proxmox host:
```bash
pct stop 127
```

### Step 3: Verify Independence
Verify that:
- Core Cali command center (`cali.call-on.media` or local desktop) remains fully functional.
- The new Video Studio at `http://127.0.0.1:8790` generates speech and renders video without any network connection to CT127.

### Step 4: Destroy Container CT127
Once verified, destroy the container to free server resources:
```bash
pct destroy 127
```
*(Optionally take a Proxmox Backup Server snapshot first if you want an archival record).*

