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
            'format': 'best',
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
            
            return jsonify({
                "title": info.get('title', 'Unknown Title'),
                "url": info.get('url') or (info.get('entries')[0].get('url') if info.get('entries') else None),
                "thumbnail": info.get('thumbnail')
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
