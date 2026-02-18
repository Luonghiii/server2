from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

def format_size(bytes):
    # Chuyển đổi dung lượng từ byte sang MB
    if bytes:
        return f"{bytes / (1024 * 1024):.2f} MB"
    return "Unknown size"

@app.route('/')
def home():
    # Trang chủ để Render Health Check
    return jsonify({
        "status": "API is running",
        "message": "Chào Cậu! Dùng /api/resolve?url=LINK để lấy JSON nhé."
    })

@app.route('/api/resolve', methods=['GET', 'POST'])
def resolve_video():
    # Lấy URL linh hoạt từ tham số query hoặc body JSON
    if request.method == 'POST':
        data = request.json or {}
        url = data.get('url')
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({"error": "Cậu chưa cung cấp link video nè!"}), 400

    try:
        # Đường dẫn file cookie nằm cùng thư mục gốc
        cookie_path = 'cookies.txt'
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            # KHÔNG để cấu hình 'format' ở đây để tránh lỗi "format not available"
            'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # [cite_start]Chỉ trích xuất thông tin, không tải video [cite: 4]
            info = ydl.extract_info(url, download=False)
            
            if '_type' in info and info['_type'] == 'playlist':
                return jsonify({"error": "Hiện tại tớ chỉ hỗ trợ video đơn lẻ."}), 400
            
            formats_list = []
            # [cite_start]Duyệt qua danh sách formats để lấy URL trực tiếp [cite: 4]
            for f in info.get('formats', []):
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
    # Nhận cổng PORT động từ Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
