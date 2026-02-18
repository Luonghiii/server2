from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

# Hàm hỗ trợ đổi bytes sang MB cho FE dễ hiển thị
def format_size(bytes):
    if bytes:
        return f"{bytes / (1024 * 1024):.2f} MB"
    return "Unknown size"

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
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            for f in info.get('formats', []):
                # Chỉ lấy các định dạng có cả video và audio cho đơn giản (progressive)
                # Hoặc lấy các bản video-only nhưng ghi chú rõ để FE xử lý
                if f.get('url'):
                    formats_list.append({
                        "format_id": f.get('format_id'),
                        "resolution": f.get('resolution') or f"{f.get('height')}p",
                        "ext": f.get('ext'),
                        "size": format_size(f.get('filesize')),
                        "url": f.get('url'), # Đây là direct link để user bấm tải luôn
                        "note": f.get('format_note', 'Standard')
                    })

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "formats": formats_list[::-1] # Đảo ngược để chất lượng cao lên đầu
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)