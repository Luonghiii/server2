from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

def format_size(bytes):
    if bytes:
        return f"{bytes / (1024 * 1024):.2f} MB"
    return "Unknown size"

@app.route('/')
def home():
    return jsonify({"status": "API is running", "message": "Chào Cậu! Hãy dùng endpoint /api/resolve để lấy link nhé."})

@app.route('/api/resolve', methods=['POST'])
def resolve_video():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            # Tự động nhận diện file cookies.txt nếu có
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Kiểm tra nếu là Playlist
            if '_type' in info and info['_type'] == 'playlist':
                return jsonify({"error": "Hiện tại API chỉ hỗ trợ link video đơn lẻ."}), 400
            
            formats_list = []
            for f in info.get('formats', []):
                # Ưu tiên lấy định dạng có URL trực tiếp
                if f.get('url'):
                    formats_list.append({
                        "format_id": f.get('format_id'),
                        "resolution": f.get('resolution') or f"{f.get('height')}p",
                        "ext": f.get('ext'),
                        "size": format_size(f.get('filesize')),
                        "url": f.get('url'),
                        "has_audio": f.get('acodec') != 'none',
                        "note": f.get('format_note', '')
                    })

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats_list[::-1] # Chất lượng cao lên đầu
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Tự động nhận Port từ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)