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
    # Lấy URL linh hoạt từ query hoặc JSON 
    if request.method == 'POST':
        data = request.json or {}
        url = data.get('url')
    else:
        url = request.args.get('url')

    if not url:
        return jsonify({"error": "Cậu chưa cung cấp link video nè!"}), 400

    try:
        # Tối ưu ydl_opts để không bị lỗi "format not available" 
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            # Xóa cấu hình 'format': 'best' để tránh ép buộc định dạng không tồn tại
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Chỉ lấy thông tin, không ép buộc định dạng tải lúc này 
            info = ydl.extract_info(url, download=False)
            
            if '_type' in info and info['_type'] == 'playlist':
                return jsonify({"error": "Hiện tại tớ chỉ hỗ trợ video đơn lẻ."}), 400
            
            formats_list = []
            # Duyệt qua tất cả định dạng có sẵn mà YouTube cung cấp 
            for f in info.get('formats', []):
                if f.get('url'):
                    # Thu thập thông tin định dạng để trả về cho Cậu 
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
                "formats": formats_list[::-1] # Đảo ngược để chất lượng cao lên đầu 
            })
    except Exception as e:
        # Trả về thông báo lỗi chi tiết nếu có sự cố 
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Tự động nhận diện cổng từ Render 
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
