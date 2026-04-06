import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Enable CORS for the application so it can be called from mobile/web clients (music player)
CORS(app)

def get_audio_stream_url(video_url: str) -> str:
    """Extract the best audio stream URL using yt-dlp."""
    # Production-ready yt-dlp options
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,          # Process only a single video, not the whole playlist
        'extract_flat': False,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(video_url, download=False)
            
            # If extracting from a playlist, yt_dlp might return a list of entries
            if 'entries' in info_dict:
                # Take the first video from the playlist
                info_dict = info_dict['entries'][0]
                
            stream_url = info_dict.get('url')
            if not stream_url:
                raise ValueError("Stream URL not found in extracted info.")
                
            return stream_url
            
        except Exception as e:
            logger.error(f"Error extracting stream for {video_url}: {e}")
            raise Exception(f"Failed to extract audio stream: {str(e)}")

@app.route('/api/v1/stream', methods=['POST'])
def stream_audio():
    """
    Endpoint to get direct audio stream link.
    JSON Body:
        yt_url (str): The video url to extract audio from (e.g., YouTube link)
    """
    data = request.get_json()
    
    if not data or 'yt_url' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing "yt_url" parameter in JSON body.'
        }), 400
        
    video_url = data.get('yt_url')

    logger.info(f"Received request to extract audio for: {video_url}")
    
    try:
        stream_link = get_audio_stream_url(video_url)
        
        return jsonify({
            'success': True,
            'stream_url': stream_link,
            'original_url': video_url
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for production monitoring."""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # Determine port from environment or default to 5000
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Check if running in development mode
    if os.environ.get('FLASK_ENV') == 'development':
        logger.info(f"Starting development server on {host}:{port}")
        app.run(host=host, port=port, debug=True)
    else:
        # Use Waitress for production-ready WSGI server on Windows
        from waitress import serve
        logger.info(f"Starting production server (Waitress) on {host}:{port}")
        serve(app, host=host, port=port)