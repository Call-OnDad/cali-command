"""
project_manager.py - Project, Storyboard & Media Library Management.
Coordinates local project storage, scene generation, and indexes the
766 mascot launch videos and 241 guide previews from D:/Cali-media-ltd/Local-video-studio.
"""

import json
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger("cali.video.projects")


class ProjectManager:
    def __init__(self, config: dict):
        self.config = config
        self.paths = config.get("paths", {})
        self.projects_dir = Path(self.paths.get("projects_dir", "projects"))
        self.exports_dir = Path(self.paths.get("exports_dir", "exports"))
        self.media_lib = Path(self.paths.get("media_library", "D:/Cali-media-ltd/Local-video-studio"))
        self.videos_dir = Path(self.paths.get("videos_dir", str(self.media_lib / "Videos")))
        self.images_dir = Path(self.paths.get("images_dir", str(self.media_lib / "Images")))
        self.active_series_dir = Path("D:/Cali-media-ltd/Social/mascot-launch/CURRENT")

        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list:
        """Returns all saved video creation projects."""
        projects = []
        for p in self.projects_dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                projects.append({
                    "id": p.stem,
                    "title": data.get("title", p.stem),
                    "scenes_count": len(data.get("scenes", [])),
                    "voice": data.get("voice", "cali"),
                    "updated_at": data.get("updated_at", p.stat().st_mtime)
                })
            except Exception:
                pass
        projects.sort(key=lambda x: x["updated_at"], reverse=True)
        return projects

    def get_project(self, project_id: str) -> dict:
        """Loads a project specification."""
        p = self.projects_dir / f"{project_id}.json"
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def save_project(self, project_data: dict) -> str:
        """Saves or updates a project specification."""
        project_id = project_data.get("id") or f"proj_{int(time.time())}"
        project_data["id"] = project_id
        project_data["updated_at"] = time.time()

        p = self.projects_dir / f"{project_id}.json"
        p.write_text(json.dumps(project_data, indent=2), encoding="utf-8")
        return project_id

    def list_collections(self) -> list:
        """Discovers distinct series, packs, and project folders."""
        collections = []

        # 1. Active Current Production Series in Social/mascot-launch/CURRENT
        if self.active_series_dir.exists():
            for d in self.active_series_dir.iterdir():
                if d.is_dir() and not d.name.startswith((".", "_", "audio", "artwork")):
                    mp4s = list(d.glob("*.mp4"))
                    if mp4s:
                        collections.append({
                            "id": f"current_{d.name}",
                            "name": d.name.replace("-", " ").title(),
                            "path": str(d),
                            "count": len(mp4s),
                            "source": "Active Production"
                        })

        # 2. Local Video Studio Library categories
        if self.videos_dir.exists():
            for d in self.videos_dir.iterdir():
                if d.is_dir():
                    mp4s = list(d.glob("*.mp4"))
                    if mp4s:
                        collections.append({
                            "id": f"lib_{d.name}",
                            "name": d.name.replace("-", " ").title(),
                            "path": str(d),
                            "count": len(mp4s),
                            "source": "Media Vault"
                        })

        return collections

    def list_library_videos(self, collection_path: str = None, limit: int = 100) -> list:
        """
        Lists videos belonging to a specific selected collection/series
        rather than dumping all files together.
        """
        results = []
        target_dir = Path(collection_path) if collection_path else self.active_series_dir

        if not target_dir.exists():
            target_dir = self.videos_dir

        if target_dir.exists():
            for v in target_dir.rglob("*.mp4"):
                try:
                    # Look for companion thumbnail or first-frame
                    thumb = v.with_suffix(".jpg")
                    if not thumb.exists():
                        ff = v.with_name(f"{v.stem}-first-frame.jpg")
                        thumb = ff if ff.exists() else None

                    results.append({
                        "name": v.name,
                        "full_path": str(v),
                        "rel_path": v.as_posix(),
                        "size_mb": round(v.stat().st_size / (1024 * 1024), 2),
                        "mtime": v.stat().st_mtime,
                        "collection": v.parent.name,
                        "has_thumb": thumb is not None
                    })
                    if len(results) >= limit:
                        break
                except Exception:
                    pass

        results.sort(key=lambda x: x["mtime"], reverse=True)
        return results

    def list_voice_profiles(self) -> list:
        """Lists all local character and narrator voice profiles."""
        from engine.tts_piper import CHARACTER_PROFILES
        profiles = []
        for key, p in CHARACTER_PROFILES.items():
            category = "Mascot Cast" if key in ("cali", "arthur", "trevor", "dexter", "hilda", "odin", "the_director") else "Standard Narrator"
            profiles.append({
                "id": key,
                "name": p["name"],
                "category": category,
                "engine": "piper",
                "desc": p["desc"],
                "ready": True
            })
        return profiles

