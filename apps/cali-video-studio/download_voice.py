"""
download_voice.py - Download official Piper voice models for Cali Video Studio.
"""
import shutil
import urllib.request
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

VOICES = {
    "jenny": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium",
    "northern": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium",
    "cori": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/cori/medium/en_GB-cori-medium",
    "alan": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium"
}

def download():
    for name, base in VOICES.items():
        for ext in (".onnx", ".onnx.json"):
            dst = MODELS_DIR / f"{name}{ext}"
            if not dst.exists() or dst.stat().st_size < 1000:
                url = f"{base}{ext}"
                print(f"Downloading {url} -> {dst.name}...")
                urllib.request.urlretrieve(url, dst)
                print(f"Saved {dst.name} ({dst.stat().st_size} bytes)")
            else:
                print(f"Already present: {dst.name}")

    # Copy jenny as cali (approved voice)
    cali_onnx = MODELS_DIR / "cali.onnx"
    cali_json = MODELS_DIR / "cali.onnx.json"
    jenny_onnx = MODELS_DIR / "jenny.onnx"
    jenny_json = MODELS_DIR / "jenny.onnx.json"

    if jenny_onnx.exists():
        shutil.copy2(jenny_onnx, cali_onnx)
        shutil.copy2(jenny_json, cali_json)
        print("Set Cali voice to approved Jenny model.")

if __name__ == "__main__":
    download()
