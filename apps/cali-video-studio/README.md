# Cali Video & Media Studio (Standalone Module)

A completely decoupled, native video creation suite built for Antony and the Cali ecosystem.

## Highlights
- **Decoupled Architecture:** Runs as its own standalone process on port 8790. Does not interfere with or reset Cali core, SEO, or other departmental suites.
- **Local Piper Voice Synthesis:** High-quality local neural speech using approved character voice models (Cali, Jenny, Northern English, Cori, Alan). No ElevenLabs or third-party cloud subscriptions required.
- **Hardware GPU Video Assembly:** Leverages your workstation's NVIDIA NVENC encoder (`h264_nvenc`) via FFmpeg for high-speed video rendering.
- **EBU R128 Loudness Normalization:** Automatically masters all dialog to streaming broadcast standard (`-16 LUFS`, `-1.5 dBTP`).
- **3-Second Branded Opener:** Renders the approved Arthur/Cali v6 standard branded bumper.
- **Omni Video Client:** High-volume multimodal video scene generation with fallback to local library assets.
- **Google Colab GPU Hub:** Staging exporter to offload bulk rendering to Google Colab GPU units (`D:/Tools/colab-cli`).
- **Consolidated Library Access:** Direct indexing and streaming of 766 mascot videos and 241 guide previews from `D:/Cali-media-ltd/Local-video-studio`.

## Quick Start
1. Double-click **`Launch-Studio.cmd`** or run:
   ```powershell
   python server.py
   ```
2. Open your browser at **`http://127.0.0.1:8790`**.

