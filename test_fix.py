import os
import yt_dlp
from pytubefix import YouTube
from pytubefix.cli import on_progress

# Test configuration
video_url = "https://www.youtube.com/watch?v=9wTEmuv6SvU"
cookies_path = os.path.abspath("cookies.txt")

def test_ytdlp():
    print("\n--- Testing yt-dlp ---")
    ydl_opts = {
        'quiet': False,
        'no_warnings': False,
        'skip_download': True,
        'noplaylist': True,
        'cookiefile': cookies_path if os.path.exists(cookies_path) else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android', 'ios', 'mweb'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            print(f"✅ yt-dlp Success: {info.get('title')}")
            return True
        except Exception as e:
            print(f"❌ yt-dlp Failed: {e}")
            return False

def test_pytube():
    print("\n--- Testing pytubefix ---")
    try:
        # Note: use_po_token=True will use Node.js
        yt = YouTube(
            video_url, 
            on_progress_callback=on_progress,
            use_po_token=True,
            client='WEB'
        )
        print(f"✅ pytubefix Success: {yt.title}")
        return True
    except Exception as e:
        print(f"❌ pytubefix Failed: {e}")
        return False

if __name__ == "__main__":
    ytdlp_res = test_ytdlp()
    if not ytdlp_res:
        test_pytube()
