import logging
import os
import traceback
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import yt_dlp
import requests

# -------------------- CONFIG --------------------
app = Flask(__name__)
CORS(app)
application = app  # cPanel WSGI requirement

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- HELPERS --------------------
def build_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"

COOKIES_PATH = os.path.abspath("cookies.txt")
DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

def get_audio_info(video_id: str):
    """
    Extract best audio info using yt_dlp Python API.
    Returns a dict with title, stream URL, ext, abr.
    """
    url = build_url(video_id)
    cookies_present = os.path.exists(COOKIES_PATH)
    if cookies_present:
        logger.info("Using cookies file at %s", COOKIES_PATH)
    else:
        logger.warning("cookies.txt not found at %s", COOKIES_PATH)

    ydl_opts = {
        # Avoid hard-failing when m4a isn't available for a given video.
        "format": "bestaudio/best",
        "quiet": True,
        "no_warnings": True,
        "ignoreconfig": True,
        "ignore_no_formats_error": True,
        "allow_unplayable_formats": True,
        "noplaylist": True,
        "skip_download": True,
        "cookiefile": COOKIES_PATH if cookies_present else None,
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "android", "ios", "mweb"],
            }
        },
        "http_headers": {
            "User-Agent": DEFAULT_UA,
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        # Some environments still throw "Requested format is not available".
        # Retry with a generic format to avoid hard failure.
        if "Requested format is not available" not in str(e):
            raise
        retry_opts = dict(ydl_opts)
        retry_opts.pop("format", None)
        retry_opts["format"] = "best"
        with yt_dlp.YoutubeDL(retry_opts) as ydl:
            info = ydl.extract_info(url, download=False)

    # Build a candidate list even when yt-dlp returns a single format dict.
    formats = []
    if isinstance(info, dict):
        if info.get("requested_formats"):
            formats = info.get("requested_formats") or []
        elif info.get("requested_downloads"):
            formats = info.get("requested_downloads") or []
        elif info.get("formats"):
            formats = info.get("formats") or []
        elif info.get("url"):
            formats = [info]

    def has_audio(fmt: dict) -> bool:
        acodec = fmt.get("acodec")
        return acodec is None or acodec != "none"

    # Prefer audio-only formats; if none exist, fall back to any format with audio.
    audio_formats = [
        f for f in formats
        if has_audio(f) and f.get("vcodec") == "none"
    ]
    if not audio_formats:
        audio_formats = [f for f in formats if has_audio(f)]
    if not audio_formats:
        raise Exception("No streams with audio found")

    best_audio = sorted(audio_formats, key=lambda x: x.get("abr") or 0, reverse=True)[0]

    return {
        "video_id": video_id,
        "title": info.get("title"),
        "stream_url": best_audio.get("url"),
        "ext": best_audio.get("ext"),
        "abr": best_audio.get("abr")
    }

# -------------------- API ENDPOINTS --------------------

@app.route("/api/audio", methods=["GET"])
def api_audio():
    """
    Returns metadata and direct audio URL.
    Example: /api/audio?video_id=dQw4w9WgXcQ
    """
    video_id = request.args.get("video_id")
    if not video_id:
        return jsonify({"success": False, "error": "Missing video_id"}), 400

    try:
        data = get_audio_info(video_id)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/play", methods=["GET"])
def api_play():
    """
    Stream audio bytes directly (Flutter AudioPlayers compatible).
    Example: /api/play?video_id=dQw4w9WgXcQ
    """
    video_id = request.args.get("video_id")
    if not video_id:
        return "Missing video_id", 400

    try:
        data = get_audio_info(video_id)
        url = data["stream_url"]

        # Forward Range headers for seeking
        headers = {
            "User-Agent": DEFAULT_UA,
            "Accept-Encoding": "identity",
        }
        range_header = request.headers.get("Range")
        if range_header:
            headers["Range"] = range_header

        # Stream from YouTube directly
        r = requests.get(url, headers=headers, stream=True, timeout=(5, 30))

        excluded_headers = ["content-encoding", "transfer-encoding", "connection"]
        response_headers = [(k, v) for k, v in r.headers.items() if k.lower() not in excluded_headers]

        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk

        mimetype = "audio/webm"
        if data.get("ext") in ["m4a", "mp4"]:
            mimetype = "audio/mp4"

        return Response(
            stream_with_context(generate()),
            status=r.status_code,
            headers=response_headers,
            mimetype=mimetype
        )

    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/test-yt", methods=["GET"])
def test_yt():
    """
    Test if YouTube extraction works.
    """
    try:
        video_id = "9wTEmuv6SvU"
        data = get_audio_info(video_id)
        return jsonify({
            "success": True,
            "message": "YouTube extraction working",
            "video_id": video_id,
            "title": data.get("title"),
            "stream_url_preview": (data.get("stream_url") or "")[:100]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/cookies-check", methods=["GET"])
def cookies_check():
    """
    Report whether cookies.txt is present, readable, and appears valid.
    """
    exists = os.path.exists(COOKIES_PATH)
    readable = os.access(COOKIES_PATH, os.R_OK)
    video_id = request.args.get("video_id") or "9wTEmuv6SvU"
    url = build_url(video_id)

    valid = False
    error = None
    if exists and readable:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "ignoreconfig": True,
            "noplaylist": True,
            "skip_download": True,
            "cookiefile": COOKIES_PATH,
            "extractor_args": {
                "youtube": {
                    "player_client": ["web", "android", "ios", "mweb"],
                }
            },
            "http_headers": {
                "User-Agent": DEFAULT_UA,
            },
            "socket_timeout": 10,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            formats = info.get("formats", []) if isinstance(info, dict) else []
            valid = any(f.get("acodec") != "none" for f in formats)
        except Exception as e:
            error = str(e)
    return jsonify({
        "success": True,
        "cookies_path": COOKIES_PATH,
        "exists": exists,
        "readable": readable,
        "valid": valid,
        "video_id_tested": video_id,
        "error": error,
    })

@app.route("/api/list-formats", methods=["GET"])
def list_formats():
    """
    Return a lightweight list of available formats for debugging.
    """
    video_id = request.args.get("video_id")
    if not video_id:
        return jsonify({"success": False, "error": "Missing video_id"}), 400

    url = build_url(video_id)
    cookies_present = os.path.exists(COOKIES_PATH)
    ydl_opts = {
        "format": "best",
        "quiet": True,
        "no_warnings": True,
        "ignoreconfig": True,
        "ignore_no_formats_error": True,
        "allow_unplayable_formats": True,
        "noplaylist": True,
        "skip_download": True,
        "cookiefile": COOKIES_PATH if cookies_present else None,
        "extractor_args": {
            "youtube": {
                "player_client": ["web", "android", "ios", "mweb"],
            }
        },
        "http_headers": {
            "User-Agent": DEFAULT_UA,
        },
        "socket_timeout": 10,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get("formats", []) or []:
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "acodec": f.get("acodec"),
                "vcodec": f.get("vcodec"),
                "abr": f.get("abr"),
                "filesize": f.get("filesize"),
                "tbr": f.get("tbr"),
            })

        return jsonify({
            "success": True,
            "video_id": video_id,
            "cookies_used": bool(cookies_present),
            "format_count": len(formats),
            "formats": formats,
            "yt_dlp_version": getattr(yt_dlp, "version", None) and getattr(yt_dlp.version, "__version__", None),
        })
    except Exception as e:
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok good friend"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
