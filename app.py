from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

@app.route('/api/resolve', methods=['POST'])
def resolve_video():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            # Default format selection (don't force 'best[ext=mp4]/best' as it can fail)
            # 'format': 'best', 
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'ignoreerrors': False, # Changed to False to catch the actual error
            'logtostderr': False,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'force_generic_extractor': False,
            'extract_flat': False,
            # MIMIC A REAL BROWSER (Crucial for avoiding "Sign in to confirm you’re not a bot")
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Sec-Fetch-Mode': 'navigate',
            }
        }

        # Check for cookies.txt
        import os
        if os.path.exists('cookies.txt'):
             ydl_opts['cookiefile'] = 'cookies.txt'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                 return jsonify({"error": "Failed to extract video info"}), 500
            
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    # Filter: Only keep mp4/webm, must have video.
                    # Ideally we want video+audio, but sometimes high quality is video-only.
                    # For simple direct download, we prioritize video+audio (acodec != 'none').
                    if f.get('vcodec') != 'none' and f.get('url'):
                        resolution = f.get('resolution') or f"{f.get('height')}p"
                        note = f.get('format_note') or ''
                        ext = f.get('ext')
                        has_audio = f.get('acodec') != 'none'
                        
                        # Label it clearly
                        label = f"{resolution} ({ext})"
                        if not has_audio:
                            label += " [No Audio]"
                        
                        formats.append({
                            "resolution": label,
                            "url": f['url'],
                            "ext": ext,
                            "has_audio": has_audio,
                            "filesize": f.get('filesize'),
                            "tbr": f.get('tbr') # bitrate for sorting
                        })
            
            # Sort best first
            formats.sort(key=lambda x: x.get('tbr') or 0, reverse=True)

            return jsonify({
                "title": info.get('title', 'Unknown Title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats, # Return list of formats
                "url": info.get('url') or (info.get('entries')[0].get('url') if info.get('entries') else None) # Default fallback
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Debug checks on startup
    import os
    import shutil
    import yt_dlp.version

    print(f"--- SERVER 2 STARTUP ---")
    print(f"yt-dlp version: {yt_dlp.version.__version__}")
    
    ffmpeg_path = shutil.which('ffmpeg')
    if ffmpeg_path:
        print(f"FFmpeg found at: {ffmpeg_path}")
    else:
        print("WARNING: FFmpeg NOT FOUND! High quality video merging will fail. Please install FFmpeg.")
    
    if os.path.exists('cookies.txt'):
         print("Cookies.txt FOUND! YouTube should work.")
    else:
         print("WARNING: Cookies.txt NOT FOUND! YouTube might block requests (Sign in error).")
    
    app.run(host='0.0.0.0', port=5000)
