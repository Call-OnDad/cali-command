"""
server.py - Standalone Local Backend Server for Cali Video & Media Studio.
Zero-dependency, multi-threaded HTTP server running on port 8790.
Provides REST APIs for Piper TTS, GPU NVENC rendering, storyboard management,
and media library streaming.
"""

import json
import logging
import mimetypes
import os
import sys
import threading
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Add engine directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from engine.tts_piper import synthesize_speech
from engine.video_renderer import assemble_video_story, has_nvenc
from engine.omni_client import OmniClient
from engine.colab_bridge import export_colab_manifest
from engine.project_manager import ProjectManager
from engine.trend_video_pipeline import TrendVideoPipeline, CAST_PROFILES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("cali.video.server")

# Load configuration
CONFIG_PATH = BASE_DIR / "config.json"
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

PROJECT_MGR = ProjectManager(CONFIG)
OMNI = OmniClient(CONFIG.get("omni", {}).get("api_endpoint"), CONFIG.get("omni", {}).get("api_key"))
TREND_PIPELINE = TrendVideoPipeline(CONFIG)

ACTIVE_JOBS = {}


class StudioRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR / "ui"), **kwargs)

    def end_headers(self):
        # Enable CORS and disable aggressive caching for local dashboard
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def resolve_media_path(self, path: str) -> Path:
        """Resolves a media stream URL to a valid file on disk."""
        rel_media_path = urllib.parse.unquote(path.replace("/stream/", "")).lstrip("/\\")
        # 1. Studio base dir (exports, locked_voices, projects)
        cand = (BASE_DIR / rel_media_path).resolve()
        if cand.exists() and cand.is_file():
            return cand
        # 2. Local Media Library
        cand = (PROJECT_MGR.media_lib / rel_media_path).resolve()
        if cand.exists() and cand.is_file():
            return cand
        # 3. Direct absolute or relative path
        cand = Path(rel_media_path).resolve()
        if cand.exists() and cand.is_file():
            return cand
        return None

    def do_HEAD(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        if path.startswith("/stream/"):
            file_path = self.resolve_media_path(path)
            if file_path:
                self.serve_file(file_path, is_head=True)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        super().do_HEAD()

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path
        query = urllib.parse.parse_qs(url.query)

        # 1. API Status
        if path == "/api/status":
            self.send_json({
                "status": "ONLINE",
                "module": "cali-video-studio",
                "nvenc_accelerated": has_nvenc(),
                "piper_available": True,
                "local_library": str(PROJECT_MGR.media_lib),
                "ct127_status": "Ready to Retire (All core features native)",
                "port": CONFIG.get("server", {}).get("port", 8790)
            })
            return

        # 2. Voice Profiles
        if path == "/api/voices":
            self.send_json(PROJECT_MGR.list_voice_profiles())
            return

        # 2b. Voice Audition Samples & Clones Vault (Only Canonical Locked-in 7)
        if path == "/api/voice-auditions":
            locked_dir = BASE_DIR / "locked_voices"
            auditions = [
                {
                    "name": "Arthur · Natural Master",
                    "character": "Arthur",
                    "stream_url": "/stream/locked_voices/arthur.mp3",
                    "size_kb": (locked_dir / "arthur.mp3").stat().st_size // 1024 if (locked_dir / "arthur.mp3").exists() else 91,
                    "desc": "Calm, methodical British male auditor"
                },
                {
                    "name": "Hilda · Mum Locked Reference",
                    "character": "Hilda",
                    "stream_url": "/stream/locked_voices/hilda.mp3",
                    "size_kb": (locked_dir / "hilda.mp3").stat().st_size // 1024 if (locked_dir / "hilda.mp3").exists() else 88,
                    "desc": "Warm, reassuring British motherly voice (Antony's late mum)"
                },
                {
                    "name": "The Director · Antony Clone Master",
                    "character": "The Director (Antony)",
                    "stream_url": "/stream/locked_voices/director.mp3",
                    "size_kb": (locked_dir / "director.mp3").stat().st_size // 1024 if (locked_dir / "director.mp3").exists() else 168,
                    "desc": "Direct executive leadership voice (Antony's cloned voice)"
                },
                {
                    "name": "Trevor · Approved Audition Take 2",
                    "character": "Trevor",
                    "stream_url": "/stream/locked_voices/trevor.mp3",
                    "size_kb": (locked_dir / "trevor.mp3").stat().st_size // 1024 if (locked_dir / "trevor.mp3").exists() else 115,
                    "desc": "Practical, energetic Northern English craftsman"
                },
                {
                    "name": "Dexter · Approved Audition Take 3",
                    "character": "Dexter",
                    "stream_url": "/stream/locked_voices/dexter.mp3",
                    "size_kb": (locked_dir / "dexter.mp3").stat().st_size // 1024 if (locked_dir / "dexter.mp3").exists() else 108,
                    "desc": "Snappy, fast-paced creative studio director"
                },
                {
                    "name": "Odin · Michael Approved Master",
                    "character": "Odin",
                    "stream_url": "/stream/locked_voices/odin.mp3",
                    "size_kb": (locked_dir / "odin.mp3").stat().st_size // 1024 if (locked_dir / "odin.mp3").exists() else 70,
                    "desc": "Deep, resonant deadpan British bass"
                },
                {
                    "name": "Cali · Approved High-Fidelity",
                    "character": "Cali",
                    "stream_url": "/stream/locked_voices/cali.mp3",
                    "size_kb": (locked_dir / "cali.mp3").stat().st_size // 1024 if (locked_dir / "cali.mp3").exists() else 84,
                    "desc": "Official intelligent assistant voice (Jenny model)"
                }
            ]
            self.send_json(auditions)
            return

        # 3. Project Listing
        if path == "/api/projects":
            self.send_json(PROJECT_MGR.list_projects())
            return

        # 4. Single Project
        if path.startswith("/api/project/"):
            proj_id = path.replace("/api/project/", "").strip()
            proj = PROJECT_MGR.get_project(proj_id)
            if proj:
                self.send_json(proj)
            else:
                self.send_json({"error": "Project not found"}, status=404)
            return

        # 5. Media Collections & Library
        if path == "/api/collections":
            self.send_json(PROJECT_MGR.list_collections())
            return

        if path == "/api/library":
            coll = query.get("collection", [None])[0]
            limit = int(query.get("limit", [100])[0])
            self.send_json(PROJECT_MGR.list_library_videos(collection_path=coll, limit=limit))
            return

        # 6. Autonomous Trends Pipeline
        if path == "/api/trends/live":
            trends = TREND_PIPELINE.fetch_live_trends()
            self.send_json(trends)
            return

        if path == "/api/trends/projects":
            projects = TREND_PIPELINE.list_autonomous_projects()
            self.send_json(projects)
            return

        if path == "/api/faceless/themes":
            from engine.broll_manager import THEME_COLORS
            themes = [
                {"id": k, "title": v["title"], "icon": v["icon"]} for k, v in THEME_COLORS.items()
            ]
            self.send_json(themes)
            return

        # 7. Stream Media (Exports or Local Media Library)
        if path.startswith("/stream/"):
            file_path = self.resolve_media_path(path)
            if file_path:
                self.serve_file(file_path, is_head=False)
                return
            else:
                logger.warning(f"Media stream 404: {path}")
                self.send_response(404)
                self.end_headers()
                return

        # 7. Serve Static UI
        super().do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        path = url.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_length).decode("utf-8")
        data = {}
        if post_body:
            try:
                data = json.loads(post_body)
            except Exception:
                try:
                    import ast
                    data = ast.literal_eval(post_body)
                except Exception:
                    data = {}

        # 1. Voice Audition
        if path == "/api/tts/audition":
            text = data.get("text", "Hello, this is a Cali local voice audition.")
            voice = data.get("voice", "cali")
            speed = float(data.get("speed", 1.0))

            out_dir = BASE_DIR / "exports" / "auditions"
            out_file = out_dir / f"audition_{voice}_{int(threading.get_native_id())}.wav"

            try:
                meta = synthesize_speech(
                    text=text,
                    output_wav=out_file,
                    voice_name=voice,
                    speed=speed,
                    models_dir=BASE_DIR / "models",
                    use_cuda=CONFIG.get("audio", {}).get("use_cuda", True)
                )
                rel_url = f"/stream/exports/auditions/{out_file.name}"
                meta["stream_url"] = rel_url
                self.send_json(meta)
            except Exception as e:
                logger.error(f"TTS audition error: {e}")
                self.send_json({"error": str(e)}, status=500)
            return

        # 2. Save Project
        if path == "/api/project/save":
            proj_id = PROJECT_MGR.save_project(data)
            self.send_json({"status": "saved", "id": proj_id})
            return

        # 3. Trigger Video Render
        if path == "/api/render":
            proj_id = data.get("project_id")
            proj_data = data.get("project") or PROJECT_MGR.get_project(proj_id)
            if not proj_data:
                self.send_json({"error": "No project data provided"}, status=400)
                return

            job_id = f"render_{int(threading.get_native_id())}"
            ACTIVE_JOBS[job_id] = {"status": "processing", "progress": 0.1}

            def render_worker():
                try:
                    logger.info(f"Starting render job {job_id}...")
                    scenes = proj_data.get("scenes", [])
                    voice = proj_data.get("voice", "cali")
                    speed = float(proj_data.get("speed", 1.0))
                    full_script = " ".join([s.get("text", "") for s in scenes])

                    # Step 1: Synthesize narration
                    audio_out = BASE_DIR / "exports" / f"{proj_data.get('title', 'video')}_narration.wav"
                    tts_meta = synthesize_speech(
                        text=full_script,
                        output_wav=audio_out,
                        voice_name=voice,
                        speed=speed,
                        models_dir=BASE_DIR / "models"
                    )

                    # Step 2: Ensure scene visual assets
                    library_images = Path(CONFIG.get("paths", {}).get("images_dir", ""))
                    processed_scenes = []
                    scene_dur = tts_meta["duration"] / max(1, len(scenes))

                    for idx, s in enumerate(scenes):
                        img_path = s.get("image_path")
                        if not img_path or not Path(img_path).exists():
                            img_path = str(OMNI.generate_scene_asset(
                                prompt=s.get("prompt", s.get("text", "Scene")),
                                scene_idx=idx,
                                output_dir=BASE_DIR / "projects" / "assets",
                                library_images_dir=library_images
                            ))
                        processed_scenes.append({
                            "image_path": img_path,
                            "duration": scene_dur
                        })

                    # Step 3: Render and Assemble
                    out_video = BASE_DIR / "exports" / f"{proj_data.get('title', 'video')}_final.mp4"
                    fmt = CONFIG.get("video", {}).get("formats", {}).get(proj_data.get("format", "9:16"), {"width": 1080, "height": 1920})

                    res = assemble_video_story(
                        scenes=processed_scenes,
                        full_audio_wav=audio_out,
                        srt_subtitles=Path(tts_meta["srt_path"]),
                        output_video_path=out_video,
                        width=fmt["width"],
                        height=fmt["height"],
                        include_bumper=proj_data.get("include_bumper", True)
                    )

                    ACTIVE_JOBS[job_id] = {
                        "status": "completed",
                        "video_path": str(out_video),
                        "stream_url": f"/stream/exports/{out_video.name}",
                        "duration": tts_meta["duration"] + (3.0 if proj_data.get("include_bumper", True) else 0.0)
                    }
                    logger.info(f"Render job {job_id} finished successfully!")
                except Exception as e:
                    logger.error(f"Render job {job_id} failed: {e}")
                    ACTIVE_JOBS[job_id] = {"status": "failed", "error": str(e)}

            threading.Thread(target=render_worker, daemon=True).start()
            self.send_json({"status": "queued", "job_id": job_id})
            return

        # 4. Check Job Status
        if path == "/api/job/status":
            job_id = data.get("job_id")
            self.send_json(ACTIVE_JOBS.get(job_id, {"status": "unknown"}))
            return

        # 5. Export Colab Package
        if path == "/api/export-colab":
            proj_data = data.get("project", {})
            colab_dir = Path(CONFIG.get("paths", {}).get("colab_sync_dir", "D:/Tools/colab-cli/render_staging"))
            staging = export_colab_manifest(
                project_name=proj_data.get("title", "batch_job"),
                scenes=proj_data.get("scenes", []),
                audio_path=Path(proj_data.get("audio_path", "")),
                output_dir=colab_dir
            )
            self.send_json({"status": "exported", "colab_staging_path": str(staging)})
            return

        # 6. Autonomous Trend Scripting & Video Generation Dispatch
        if path == "/api/trends/script":
            topic = data.get("topic", "Winter Boiler Maintenance Tips")
            char_id = data.get("character_id")
            char = CAST_PROFILES.get(char_id) if char_id else TREND_PIPELINE.match_character(topic)
            script = TREND_PIPELINE.generate_short_script(topic, char)
            self.send_json(script)
            return

        if path == "/api/trends/dispatch":
            topic = data.get("topic", "Winter Boiler Maintenance Tips")
            char_id = data.get("character_id")
            res = TREND_PIPELINE.dispatch_autonomous_video(topic, char_id)
            self.send_json(res)
            return

        if path == "/api/faceless/generate":
            topic = data.get("topic", "Boiler Pressure Dropping in Sub-Zero Weather")
            theme = data.get("theme")
            res = TREND_PIPELINE.dispatch_faceless_video(topic, theme)
            self.send_json(res)
            return

        self.send_json({"error": "Endpoint not found"}, status=404)

    def serve_file(self, file_path: Path, is_head: bool = False):
        """Streams a binary file with HTTP 206 Partial Content support for seeking in HTML5 audio/video."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = "audio/mpeg" if str(file_path).endswith(".mp3") else "application/octet-stream"

        file_size = file_path.stat().st_size
        range_header = self.headers.get("Range")

        if range_header and range_header.startswith("bytes="):
            # Parse Range: bytes=start-end
            try:
                ranges = range_header.replace("bytes=", "").split("-")
                start = int(ranges[0]) if ranges[0] else 0
                end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header("Content-Type", mime_type)
                self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                self.send_header("Content-Length", str(length))
                self.send_header("Accept-Ranges", "bytes")
                self.end_headers()

                if is_head:
                    return

                with open(file_path, "rb") as f:
                    f.seek(start)
                    bytes_to_send = length
                    while bytes_to_send > 0:
                        chunk_size = min(64 * 1024, bytes_to_send)
                        data = f.read(chunk_size)
                        if not data:
                            break
                        self.wfile.write(data)
                        bytes_to_send -= len(data)
                return
            except (ConnectionResetError, BrokenPipeError):
                return
            except Exception as e:
                logger.warning(f"Range request handling exception: {e}")

        # Full file fallback
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Length", str(file_size))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        if is_head:
            return

        with open(file_path, "rb") as f:
            shutil.copyfileobj(f, self.wfile)


def run_server():
    port = CONFIG.get("server", {}).get("port", 8790)
    host = CONFIG.get("server", {}).get("host", "127.0.0.1")
    server = ThreadingHTTPServer((host, port), StudioRequestHandler)
    print(f"\n=======================================================")
    print(f"  🎬 CALI VIDEO & MEDIA STUDIO (STANDALONE SUITE)     ")
    print(f"  Running on: http://{host}:{port}                    ")
    print(f"  GPU NVENC: {'ENABLED' if has_nvenc() else 'DISABLED'}              ")
    print(f"  Local Media Library: {PROJECT_MGR.media_lib}        ")
    print(f"=======================================================\n")
    server.serve_forever()


if __name__ == "__main__":
    run_server()

