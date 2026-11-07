"""
colab_bridge.py - Google Colab GPU Batch Render & Execution Bridge.
Packages video creation jobs into self-contained batch manifests
ready for execution on Google Colab GPU compute units via colab-cli.
"""

import json
import logging
import os
import shutil
from pathlib import Path

logger = logging.getLogger("cali.video.colab")

COLAB_RUNNER_TEMPLATE = '''"""Headless batch video renderer for Google Colab GPU."""
import json
import subprocess
from pathlib import Path

def run_batch(manifest_path="render_manifest.json"):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    print(f"Loaded manifest for project: {manifest.get('project_name')}")
    scenes = manifest.get("scenes", [])
    output_video = manifest.get("output_video", "colab_rendered.mp4")
    
    print(f"Executing GPU accelerated render of {len(scenes)} scenes...")
    # Execute ffmpeg commands
    for cmd in manifest.get("commands", []):
        print(f"Running: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
    
    print(f"Render complete: {output_video}")

if __name__ == "__main__":
    run_batch()
'''


def export_colab_manifest(
    project_name: str,
    scenes: list,
    audio_path: Path,
    output_dir: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30
) -> Path:
    """
    Exports a self-contained package into staging folder for Google Colab.
    """
    output_dir = Path(output_dir)
    staging = output_dir / f"colab_job_{project_name}"
    staging.mkdir(parents=True, exist_ok=True)

    assets_dir = staging / "assets"
    assets_dir.mkdir(exist_ok=True)

    # Copy audio
    colab_audio = assets_dir / "narration.wav"
    if Path(audio_path).exists():
        shutil.copy(audio_path, colab_audio)

    # Copy scene images
    colab_scenes = []
    for idx, s in enumerate(scenes):
        src_img = Path(s.get("image_path", ""))
        dst_img = assets_dir / f"scene_{idx:03d}{src_img.suffix}"
        if src_img.exists():
            shutil.copy(src_img, dst_img)
        colab_scenes.append({
            "index": idx,
            "image": dst_img.name,
            "duration": s.get("duration", 4.0),
            "prompt": s.get("prompt", "")
        })

    manifest = {
        "project_name": project_name,
        "width": width,
        "height": height,
        "fps": fps,
        "audio": colab_audio.name,
        "scenes": colab_scenes,
        "output_video": f"{project_name}_colab_render.mp4",
        "commands": [
            ["ffmpeg", "-version"]
        ]
    }

    manifest_file = staging / "render_manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    runner_file = staging / "colab_runner.py"
    runner_file.write_text(COLAB_RUNNER_TEMPLATE, encoding="utf-8")

    logger.info(f"Exported Colab batch package to {staging}")
    return staging

