"""
omni_client.py - Omni Video & Scene Asset Generation Client.
Provides high-volume, cost-effective multimodal video generation.
Supports fallback to local character/scene assets from D:/Cali-media-ltd/Local-video-studio.
"""

import json
import logging
import os
import urllib.request
import urllib.error
from pathlib import Path

logger = logging.getLogger("cali.video.omni")


class OmniClient:
    def __init__(self, api_endpoint: str = "https://api.omni.ai/v1/generate", api_key: str = ""):
        self.api_endpoint = api_endpoint
        self.api_key = api_key or os.environ.get("OMNI_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_scene_asset(self, prompt: str, scene_idx: int, output_dir: Path, library_images_dir: Path = None) -> Path:
        """
        Generates or selects an asset for a video scene.
        If Omni API key is present, calls Omni generation endpoint.
        Otherwise, intelligently selects an appropriate asset from local media library.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        target_path = output_dir / f"scene_{scene_idx:03d}.png"

        if self.is_configured():
            try:
                logger.info(f"Submitting scene {scene_idx} to Omni API: {prompt[:60]}...")
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
                payload = json.dumps({
                    "prompt": prompt,
                    "aspect_ratio": "9:16",
                    "duration": 5.0,
                    "quality": "standard"
                }).encode("utf-8")

                req = urllib.request.Request(self.api_endpoint, data=payload, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    asset_url = data.get("asset_url") or data.get("url")
                    if asset_url:
                        urllib.request.urlretrieve(asset_url, target_path)
                        return target_path
            except Exception as e:
                logger.warning(f"Omni API generation failed ({e}), falling back to local library assets...")

        # Fallback to local image library
        if library_images_dir and Path(library_images_dir).exists():
            images = list(Path(library_images_dir).glob("*.png")) + list(Path(library_images_dir).glob("*.webp"))
            if images:
                # Pick deterministic image based on prompt hash
                chosen = images[abs(hash(prompt)) % len(images)]
                from PIL import Image
                im = Image.open(chosen).convert("RGB")
                im.save(target_path)
                return target_path

        # Generate a styled fallback title card if no images exist
        from PIL import Image, ImageDraw, ImageFont
        im = Image.new("RGB", (1080, 1920), "#0f172a")
        draw = ImageDraw.Draw(im)
        draw.text((540, 960), f"Scene {scene_idx + 1}\n{prompt[:80]}", fill="#38bdf8", anchor="mm")
        im.save(target_path)
        return target_path

