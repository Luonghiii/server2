from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

def format_size(bytes):
    # Chuyển đổi bytes sang đơn vị MB để dễ đọc 
    if bytes:
        return f"{bytes / (1024 * 1024):.2f} MB"
    return "Unknown size"

@app.route('/')
def home():
    # Trang chủ chỉ trả về thông tin trạng thái đơn giản 
    return jsonify({
        "status": "API is running",
        "usage": "GET/POST to /api/resolve?url=YOUR_LINK"
    })

@app.route('/api/resolve', methods=['GET', 'POST'])
def resolve_video():
    # Lấy URL từ tham số query (?url=) hoặc từ JSON body 
    if request.method == 'POST':
        data = request.json or {}
        url = data.get('url')
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({"error": "Cậu chưa cung cấp link video nè!"}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            # Sử dụng cookies nếu có file cookies.txt trong thư mục gốc 
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin metadata mà không tải file về server 
            info = ydl.extract_info(url, download=False)
            
            # Chặn nếu người dùng dán link danh sách phát 
            if '_type' in info and info['_type'] == 'playlist':
                return jsonify({"error": "Hiện tại tớ chỉ hỗ trợ video đơn lẻ."}), 400
            
            formats_list = []
            for f in info.get('formats', []):
                # Chỉ lấy các định dạng có URL tải trực tiếp 
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

            # Trả về kết quả JSON với chất lượng cao nhất ở đầu danh sách 
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats_list[::-1]
            })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Tự động nhận diện cổng từ Render hoặc dùng cổng mặc định 10000 [cite: 2, 3]
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)