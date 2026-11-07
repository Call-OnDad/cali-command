"""
asset_bridge.py - Direct asset connector between Cali Video Studio and Social Hub.
Enables 1-click attachment of rendered MP4 shorts, full videos, and preview thumbnails.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger("cali.social.assets")

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEO_STUDIO_EXPORTS = Path("/opt/cali/apps/cali-video-studio/exports") if Path("/opt/cali/apps/cali-video-studio/exports").exists() else Path("D:/The Cali Project/apps/cali-video-studio/exports")
MEDIA_LIBRARY_VIDEOS = Path("/opt/cali/media/videos") if Path("/opt/cali/media/videos").exists() else Path("D:/Cali-media-ltd/Local-video-studio/Videos")


class AssetBridge:
    def __init__(self):
        pass

    def list_available_media(self) -> List[Dict]:
        """Discovers all rendered MP4s, clips, and images ready for social publishing."""
        assets = []

        # 1. Video Studio Exports
        if VIDEO_STUDIO_EXPORTS.exists():
            for f in VIDEO_STUDIO_EXPORTS.glob("*.mp4"):
                assets.append({
                    "id": f.name,
                    "title": f.stem.replace("_final", "").replace("_", " "),
                    "path": str(f),
                    "type": "video",
                    "source": "Video Studio Exports",
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "modified": f.stat().st_mtime
                })
            for img in VIDEO_STUDIO_EXPORTS.glob("*.png"):
                assets.append({
                    "id": img.name,
                    "title": img.stem.replace("_", " "),
                    "path": str(img),
                    "type": "image",
                    "source": "Video Studio Exports",
                    "size_mb": round(img.stat().st_size / (1024 * 1024), 2),
                    "modified": img.stat().st_mtime
                })

        # 2. Local Media Library
        if MEDIA_LIBRARY_VIDEOS.exists():
            for f in list(MEDIA_LIBRARY_VIDEOS.glob("*.mp4"))[:15]:
                assets.append({
                    "id": f.name,
                    "title": f.stem.replace("_", " "),
                    "path": str(f),
                    "type": "video",
                    "source": "Local Media Library",
                    "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                    "modified": f.stat().st_mtime
                })

        assets.sort(key=lambda x: x["modified"], reverse=True)
        return assets
