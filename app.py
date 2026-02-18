from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/api/resolve', methods=['GET', 'POST'])
def resolve_video():
    # Lấy URL linh hoạt
    url = request.args.get('url') or (request.json.get('url') if request.json else None)
    
    if not url:
        return jsonify({"error": "Cậu quên dán link rồi kìa!"}), 400

    try:
        # Gọi tới API của Cobalt (Instance công khai)
        cobalt_api = "https://api.cobalt.tools/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "vQuality": "1080", # Cậu có thể chỉnh 720, 1080, 4k...
            "isAudioOnly": False
        }

        response = requests.post(cobalt_api, json=payload, headers=headers)
        data = response.json()

        # Kiểm tra nếu Cobalt trả về link trực tiếp
        if data.get('status') == 'stream':
            return jsonify({
                "title": "Video từ Cobalt",
                "thumbnail": "", 
                "formats": [
                    {
                        "resolution": "Định dạng tốt nhất",
                        "ext": "mp4",
                        "url": data.get('url'),
                        "note": "Link tải trực tiếp từ Cobalt"
                    }
                ]
            })
        
        # Nếu Cobalt trả về danh sách (Pick)
        elif data.get('status') == 'picker':
            formats = []
            for item in data.get('picker', []):
                formats.append({
                    "resolution": item.get('type', 'video'),
                    "ext": "url",
                    "url": item.get('url')
                })
            return jsonify({ "formats": formats[::-1] })

        return jsonify({"error": data.get('text', 'Lỗi không xác định từ Cobalt')}), 500

    except Exception as e:
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
