import sys
from pathlib import Path

STUDIO_DIR = Path(r"d:\The Cali Project\apps\cali-video-studio")
sys.path.insert(0, str(STUDIO_DIR))

from engine.tts_piper import synthesize_speech, generate_subtitles, export_srt
from engine.video_renderer import assemble_video_story

test_text = "Right lads, Trevor here. If your boiler pressure drops in sub-zero weather, check your filling loop before you call anyone out. Proper jobs, zero nonsense."
out_dir = STUDIO_DIR / "exports" / "trend_videos"
out_dir.mkdir(parents=True, exist_ok=True)

wav_path = out_dir / "test_trevor.wav"
srt_path = out_dir / "test_trevor.srt"
mp4_path = out_dir / "test_trevor.mp4"

print("1. Synthesizing Trevor speech...")
res = synthesize_speech(test_text, wav_path, voice_name="trevor", speed=0.95)
dur = res["duration"]
print(f"Speech generated: {dur}s")

print("2. Generating subtitles...")
caps = generate_subtitles(test_text, dur)
export_srt(caps, srt_path)

print("3. Assembling video story with Trevor portrait...")
portrait = STUDIO_DIR / "locked_images" / "portraits" / "trevor.webp"
scenes = [
    {"image_path": str(portrait), "duration": dur}
]

assemble_video_story(
    scenes=scenes,
    full_audio_wav=wav_path,
    srt_subtitles=srt_path,
    output_video_path=mp4_path,
    width=1080,
    height=1920,
    fps=30,
    include_bumper=False
)

print(f"VIDEO RENDERED SUCCESSFULLY: {mp4_path} (size: {mp4_path.stat().st_size} bytes)")

