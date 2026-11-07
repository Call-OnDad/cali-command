"""
video_renderer.py - GPU-Accelerated Video Rendering Engine (NVENC / FFmpeg).
Assembles multi-scene video stories with Ken-Burns pan/zoom easing,
Piper TTS speech narration, subtitle burn-in, and Cali 3s branded bumper.
"""

import json
import logging
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("cali.video.renderer")


def has_nvenc() -> bool:
    """Checks if NVIDIA NVENC hardware encoder is actively working with drivers."""
    try:
        # Run a 1-frame null test with h264_nvenc
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.04",
            "-c:v", "h264_nvenc",
            "-f", "null", "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False


def create_branded_bumper(
    output_mp4: Path,
    width: int,
    height: int,
    fps: int = 30,
    duration: float = 3.0,
    background: str = "#0d2130",
    tagline: str = "Cali Media · Intelligent Systems",
    logo_path: Path = None,
    use_nvenc: bool = True
):
    """
    Renders a 3-second locked branded intro bumper matching the approved Arthur/Cali standard.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="bumper_frames_"))
    try:
        total_frames = math.ceil(duration * fps)
        for i in range(total_frames):
            t = i / fps
            im = Image.new("RGB", (width, height), background)
            draw = ImageDraw.Draw(im)

            # Draw brand text / logo
            fade_in = min(1.0, t / 0.5)
            fade_out = min(1.0, (duration - t) / 0.5)
            alpha = max(0.0, min(fade_in, fade_out))

            title_font_size = max(36, round(width * 0.05))
            tagline_font_size = max(20, round(width * 0.025))

            try:
                font_title = ImageFont.truetype("arialbd.ttf", title_font_size)
                font_tag = ImageFont.truetype("arial.ttf", tagline_font_size)
            except Exception:
                font_title = ImageFont.load_default()
                font_tag = ImageFont.load_default()

            color = tuple(round(c * alpha) for c in (255, 247, 232))
            accent_color = tuple(round(c * alpha) for c in (20, 184, 166)) # Teal accent

            draw.text((width / 2, height * 0.42), "CALI MEDIA", font=font_title, anchor="mm", fill=accent_color)
            draw.text((width / 2, height * 0.42 + title_font_size * 1.5), tagline, font=font_tag, anchor="mm", fill=color)

            frame_file = temp_dir / f"frame_{i:04d}.png"
            im.save(frame_file)

        encoder = "h264_nvenc" if use_nvenc else "libx264"
        cmd = [
            "ffmpeg", "-v", "error", "-y",
            "-framerate", str(fps),
            "-i", str(temp_dir / "frame_%04d.png"),
            "-c:v", encoder,
            "-pix_fmt", "yuv420p",
            "-t", str(duration),
            str(output_mp4)
        ]
        subprocess.run(cmd, check=True)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_scene_clip(
    image_path: Path,
    output_mp4: Path,
    duration: float,
    width: int,
    height: int,
    fps: int = 30,
    use_nvenc: bool = False
):
    """
    Renders a single scene still cleanly into a solid, crisp video clip.
    No Ken-Burns warping or artificial motion -- preserves exact pixel clarity.
    Pads/fits cleanly to target canvas size without stretching.
    """
    # Clean scaling filter: fit inside canvas, pad with black if needed, zero weird motion
    vf = (
        f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,"
        "format=yuv420p"
    )

    encoder = "h264_nvenc" if use_nvenc else "libx264"
    cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", vf,
        "-t", str(duration),
        "-r", str(fps),
        "-c:v", encoder
    ]
    if not use_nvenc:
        cmd.extend(["-preset", "veryfast", "-crf", "20"])

    cmd.append(str(output_mp4))
    subprocess.run(cmd, check=True)


def assemble_video_story(
    scenes: list,
    full_audio_wav: Path,
    srt_subtitles: Path,
    output_video_path: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    include_bumper: bool = True,
    tagline: str = "Cali Media · Intelligent Systems",
    music_bed: Path = None,
    music_gain_db: float = -22.0
) -> dict:
    """
    Assembles a full narrated video story:
    1. Generates animated clips for each scene.
    2. Concatenates scene clips.
    3. Adds bumper intro (if requested).
    4. Muxes speech audio (with optional ducked music).
    5. Burns in stylized subtitles.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="cali_render_"))
    use_nvenc = has_nvenc()
    logger.info(f"Rendering with NVENC acceleration: {use_nvenc}")

    try:
        scene_clips = []
        concat_txt = temp_dir / "concat_list.txt"
        concat_lines = []

        # 1. Bumper Intro
        if include_bumper:
            bumper_mp4 = temp_dir / "bumper.mp4"
            create_branded_bumper(bumper_mp4, width, height, fps=fps, duration=3.0, tagline=tagline, use_nvenc=use_nvenc)
            concat_lines.append(f"file '{bumper_mp4.as_posix()}'")

        # 2. Render each scene cleanly without artificial zoom
        for idx, scene in enumerate(scenes):
            img_path = Path(scene.get("image_path"))
            dur = float(scene.get("duration", 4.0))
            clip_path = temp_dir / f"scene_{idx:03d}.mp4"
            render_scene_clip(img_path, clip_path, dur, width, height, fps=fps, use_nvenc=use_nvenc)
            scene_clips.append(clip_path)
            concat_lines.append(f"file '{clip_path.as_posix()}'")

        concat_txt.write_text("\n".join(concat_lines), encoding="utf-8")

        # 3. Concatenate visual tracks
        concat_mp4 = temp_dir / "visual_merged.mp4"
        cmd_concat = [
            "ffmpeg", "-v", "error", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(concat_mp4)
        ]
        subprocess.run(cmd_concat, check=True)

        # 4. Audio track assembly (offset speech if bumper is present)
        final_audio = temp_dir / "final_audio.wav"
        audio_offset = 3.0 if include_bumper else 0.0

        if audio_offset > 0:
            cmd_delay = [
                "ffmpeg", "-v", "error", "-y",
                "-i", str(full_audio_wav),
                "-af", f"adelay={int(audio_offset*1000)}|{int(audio_offset*1000)}",
                str(final_audio)
            ]
            subprocess.run(cmd_delay, check=True)
        else:
            shutil.copy(full_audio_wav, final_audio)

        # Optional background music mixing
        if music_bed and Path(music_bed).exists():
            mixed_audio = temp_dir / "mixed_audio.wav"
            filt = (
                f"[1:a]aloop=loop=-1:size=2e9,volume={music_gain_db}dB[bed];"
                "[0:a]asplit=2[voice_out][voice_sc];"
                "[bed][voice_sc]sidechaincompress=threshold=0.04:ratio=10:attack=5:release=350:makeup=1[ducked];"
                "[voice_out][ducked]amix=inputs=2:duration=first:weights=1 1[out]"
            )
            subprocess.run([
                "ffmpeg", "-v", "error", "-y",
                "-i", str(final_audio), "-i", str(music_bed),
                "-filter_complex", filt, "-map", "[out]",
                "-ar", "24000", "-ac", "1", "-c:a", "pcm_s16le",
                str(mixed_audio)
            ], check=True)
            final_audio = mixed_audio

        # 5. Burn in subtitles & mux final video
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        encoder = "h264_nvenc" if use_nvenc else "libx264"

        # Format subtitles filter
        # Pixel-perfect scaling with PlayResX/Y, bold yellow text with translucent background box
        font_size = 46 if height >= 1920 else max(24, round(height * 0.032))
        srt_escaped = str(srt_subtitles).replace("\\", "/").replace(":", "\\:")
        
        # Subtitle styling with PlayResX/PlayResY to prevent font blowout
        margin_v = 400 if height >= 1920 else 120
        sub_filter = f"subtitles='{srt_escaped}':force_style='PlayResX={width},PlayResY={height},FontSize={font_size},PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BackColour=&H90000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV={margin_v}'"

        cmd_final = [
            "ffmpeg", "-v", "error", "-y",
            "-i", str(concat_mp4),
            "-i", str(final_audio),
            "-vf", sub_filter,
            "-c:v", encoder,
            "-pix_fmt", "yuv420p"
        ]
        if not use_nvenc:
            cmd_final.extend(["-preset", "veryfast", "-crf", "20"])

        cmd_final.extend([
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_video_path)
        ])
        subprocess.run(cmd_final, check=True)

        return {
            "status": "success",
            "video_path": str(output_video_path),
            "width": width,
            "height": height,
            "nvenc_used": use_nvenc
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
