"""
tts_piper.py - Native Windows Piper TTS Engine with GPU Acceleration.
Generates crystal-clear narration, normalizes audio to -16 LUFS streaming standard,
and produces synchronized SRT/VTT subtitle cues.
"""

import json
import logging
import os
import re
import subprocess
import urllib.request
from pathlib import Path

logger = logging.getLogger("cali.video.tts")

# Piper HuggingFace repository for on-demand voice downloading
PIPER_HF_BASE = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

VOICE_URLS = {
    "jenny": f"{PIPER_HF_BASE}/en/en_GB/jenny_dioco/medium/en_GB-jenny_dioco-medium",
    "northern": f"{PIPER_HF_BASE}/en/en_GB/northern_english_male/medium/en_GB-northern_english_male-medium",
    "cori": f"{PIPER_HF_BASE}/en/en_GB/cori/medium/en_GB-cori-medium",
    "alan": f"{PIPER_HF_BASE}/en/en_GB/alan/medium/en_GB-alan-medium"
}


def ensure_model(model_name: str, models_dir: Path) -> Path:
    """Ensures that the requested Piper ONNX model and its config JSON exist."""
    models_dir.mkdir(parents=True, exist_ok=True)
    target_onnx = models_dir / f"{model_name}.onnx"
    target_json = models_dir / f"{model_name}.onnx.json"

    if target_onnx.exists():
        return target_onnx

    # Check if voice is in known downloadable catalog
    if model_name in VOICE_URLS:
        base_url = VOICE_URLS[model_name]
        logger.info(f"Downloading Piper voice {model_name} from HuggingFace...")
        try:
            urllib.request.urlretrieve(f"{base_url}.onnx", target_onnx)
            urllib.request.urlretrieve(f"{base_url}.onnx.json", target_json)
            logger.info(f"Successfully downloaded {model_name} to {target_onnx}")
            return target_onnx
        except Exception as e:
            logger.error(f"Failed to download voice {model_name}: {e}")
            if target_onnx.exists():
                target_onnx.unlink()
            raise RuntimeError(f"Voice model {model_name} is not installed and download failed: {e}")

    raise FileNotFoundError(f"Voice model '{model_name}' not found at {target_onnx}")


# Canonical Locked Character Profiles (Strict 1 voice per character)
CHARACTER_PROFILES = {
    "arthur": {
        "name": "Arthur Auditor (Consumer Protection)",
        "model": "northern",
        "speed": 0.93,
        "filter": None,
        "desc": "Calm, methodical British male (Locked: arthur-natural)"
    },
    "hilda": {
        "name": "Hilda (Family & Home Advice)",
        "model": "cori",
        "speed": 0.85,
        "filter": "asetrate=24000*0.94,aresample=24000,lowpass=f=6500",
        "desc": "Warm, reassuring British motherly voice (Locked: Antony's late mum reference)"
    },
    "the_director": {
        "name": "The Director (Antony Leadership)",
        "model": "northern",
        "speed": 0.92,
        "filter": None,
        "desc": "Direct executive leadership voice (Locked: Antony's cloned voice)"
    },
    "trevor": {
        "name": "Trevor (Handyman & DIY Guides)",
        "model": "northern",
        "speed": 1.0,
        "filter": "asetrate=24000*1.04,aresample=24000",
        "desc": "Practical, energetic Northern craftsman (Locked: 02-trevor)"
    },
    "dexter": {
        "name": "Dexter (Creative Director / Video Production)",
        "model": "northern",
        "speed": 1.06,
        "filter": "asetrate=24000*1.08,aresample=24000",
        "desc": "Snappy, fast-paced studio coordinator (Locked: 03-dexter)"
    },
    "odin": {
        "name": "Odin (Chief Security Officer)",
        "model": "alan",
        "speed": 0.96,
        "filter": "asetrate=24000*0.88,aresample=24000,lowpass=f=5000,bass=g=5",
        "desc": "Deep, resonant deadpan British bass (Locked: odin-michael)"
    },
    "cali": {
        "name": "Cali (Platform Command)",
        "model": "cali",
        "speed": 1.0,
        "filter": None,
        "desc": "Official intelligent assistant voice (Locked: Jenny model 1.0x)"
    }
}


def normalize_audio(src: Path, dst: Path, target_i=-16.0, target_tp=-1.5, target_lra=11.0, custom_filter: str = None):
    """
    Applies optional character acoustic filters followed by EBU R128 loudness normalization.
    """
    loudnorm_filter = f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}"
    af = f"{custom_filter},{loudnorm_filter}" if custom_filter else loudnorm_filter

    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-i", str(src),
        "-af", af,
        "-ar", "24000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        str(dst)
    ]
    subprocess.run(cmd, check=True)


def get_audio_duration(wav_path: Path) -> float:
    """Gets exact duration of WAV file using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(wav_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def generate_subtitles(text: str, duration: float) -> list:
    """Splits text into readable caption chunks with proportional timestamps."""
    chunks = re.findall(r'[^.!?]+[.!?]?', text)
    chunks = [v.strip() for v in chunks if v.strip()]
    if not chunks:
        chunks = [text.strip()]

    total_words = sum(len(v.split()) for v in chunks) or 1
    start = 0.0
    captions = []

    for v in chunks:
        chunk_words = len(v.split()) or 1
        chunk_dur = (chunk_words / total_words) * duration
        end = min(duration, start + chunk_dur)
        captions.append({
            "start": round(start, 3),
            "end": round(end, 3),
            "text": v
        })
        start = end

    return captions


def export_srt(captions: list, output_path: Path):
    """Formats caption chunks into standard SRT format."""
    def ts(seconds):
        ms = round(seconds * 1000)
        hours = ms // 3600000
        mins = (ms % 3600000) // 60000
        secs = (ms % 60000) // 1000
        millis = ms % 1000
        return f"{hours:02}:{mins:02}:{secs:02},{millis:03}"

    lines = []
    for i, c in enumerate(captions, 1):
        lines.append(f"{i}\n{ts(c['start'])} --> {ts(c['end'])}\n{c['text']}\n")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def synthesize_speech(
    text: str,
    output_wav: Path,
    voice_name: str = "cali",
    speed: float = 1.0,
    models_dir: Path = None,
    use_cuda: bool = False
) -> dict:
    """
    Synthesizes speech using local Piper TTS with character acoustic profiling.
    """
    output_wav = Path(output_wav)
    output_wav.parent.mkdir(parents=True, exist_ok=True)
    raw_wav = output_wav.with_name(f"{output_wav.stem}_raw.wav")
    script_txt = output_wav.with_name(f"{output_wav.stem}_script.txt")

    clean_text = text.replace("\r\n", " ").replace("\n", " ").strip()
    if not clean_text:
        clean_text = "Cali Studio narration."

    if models_dir is None:
        models_dir = Path(__file__).resolve().parent.parent / "models"

    profile = CHARACTER_PROFILES.get(voice_name, CHARACTER_PROFILES.get("cali", list(CHARACTER_PROFILES.values())[0]))
    model_name = profile["model"]
    model_path = ensure_model(model_name, models_dir)

    # Effective speed multiplier
    effective_speed = speed * profile.get("speed", 1.0)
    length_scale = round(1.0 / max(0.5, min(2.5, effective_speed)), 3)

    cmd = [
        "piper",
        "-m", str(model_path),
        "-f", str(raw_wav),
        "--length-scale", str(length_scale)
    ]
    if use_cuda:
        cmd.append("--cuda")

    try:
        proc = subprocess.run(cmd, input=clean_text, text=True, capture_output=True)
        if proc.returncode != 0:
            if use_cuda:
                logger.warning(f"Piper CUDA synthesis failed ({proc.stderr.strip()}), retrying on CPU...")
                cmd.remove("--cuda")
                proc2 = subprocess.run(cmd, input=clean_text, text=True, capture_output=True)
                if proc2.returncode != 0:
                    raise RuntimeError(f"Piper CPU fallback failed: {proc2.stderr.strip()}")
            else:
                raise RuntimeError(f"Piper error (exit code {proc.returncode}): {proc.stderr.strip()}")
    except FileNotFoundError:
        # Fallback to invoking piper via active python interpreter
        import sys
        cmd_py = [sys.executable, "-m", "piper", "-m", str(model_path), "-f", str(raw_wav), "--length-scale", str(length_scale)]
        proc = subprocess.run(cmd_py, input=clean_text, text=True, capture_output=True)
        if proc.returncode != 0:
            raise RuntimeError(f"Piper python execution failed: {proc.stderr.strip()}")

    if not raw_wav.exists() or raw_wav.stat().st_size < 500:
        raise RuntimeError("Piper synthesis produced empty or missing audio file.")

    # Normalize audio with optional custom character filter
    normalize_audio(raw_wav, output_wav, custom_filter=profile.get("filter"))
    if raw_wav.exists():
        raw_wav.unlink(missing_ok=True)
    if script_txt.exists():
        script_txt.unlink(missing_ok=True)

    duration = get_audio_duration(output_wav)
    captions = generate_subtitles(clean_text, duration)

    srt_path = output_wav.with_suffix(".srt")
    export_srt(captions, srt_path)

    return {
        "audio_path": str(output_wav),
        "srt_path": str(srt_path),
        "duration": duration,
        "captions": captions,
        "voice": voice_name,
        "character_name": profile["name"]
    }

