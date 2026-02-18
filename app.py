from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/resolve', methods=['GET', 'POST'])
def resolve_video():
    url = request.args.get('url') or (request.json.get('url') if request.json else None)
    
    if not url:
        return jsonify({"error": "Cậu chưa dán link kìa!"}), 400

    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            # 'extract_flat': True, # Bỏ comment nếu vẫn lỗi, nhưng sẽ ít thông tin hơn
            'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
            'nocheckcertificate': True,
            'ignoreerrors': True, # Cực kỳ quan trọng: Bỏ qua lỗi nhỏ để trả về kết quả
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            }
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin metadata
            info = ydl.extract_info(url, download=False)
            
            if not info:
                return jsonify({"error": "Không lấy được thông tin video rồi ní ơi!"}), 500

            # Lọc lại danh sách format để trả về JSON sạch
            formats = []
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('url'):
                        formats.append({
                            "quality": f.get('format_note') or f.get('resolution'),
                            "ext": f.get('ext'),
                            "url": f.get('url'),
                            "size": f.get('filesize')
                        })

            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "formats": formats[::-1]
            })
            
    except Exception as e:
        return jsonify({"error": f"Lỗi rồi: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
