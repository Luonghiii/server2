from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    # Trang chủ để Render Health Check, tránh lỗi 404
    return jsonify({
        "status": "API is running",
        "message": "Chào Cậu! Hãy dùng /api/resolve?url=LINK để lấy JSON nhé."
    })

@app.route('/api/resolve', methods=['GET', 'POST'])
def resolve_video():
    # Lấy URL linh hoạt từ query hoặc JSON body
    url = request.args.get('url') or (request.json.get('url') if request.json else None)
    
    if not url:
        return jsonify({"error": "Cậu chưa dán link kìa!"}), 400

    try:
        # Sử dụng instance chính thức của Cobalt v10
        cobalt_api = "https://api.cobalt.tools/"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Cấu hình Payload theo chuẩn v10
        payload = {
            "url": url,
            "videoQuality": "720", # v10 hỗ trợ "max", "1080", "720"...
            "filenameStyle": "pretty"
        }

        response = requests.post(cobalt_api, json=payload, headers=headers)
        data = response.json()

        # Xử lý phản hồi từ Cobalt
        if data.get('status') == 'stream':
            return jsonify({
                "title": "Video đã xử lý",
                "formats": [
                    {
                        "resolution": "Best Available",
                        "url": data.get('url'),
                        "ext": "mp4"
                    }
                ]
            })
        elif data.get('status') == 'picker':
            return jsonify({
                "title": "Nhiều lựa chọn",
                "formats": data.get('picker')
            })

        # Nếu có lỗi từ phía Cobalt (như link không hỗ trợ)
        return jsonify({"error": data.get('text', 'Lỗi không xác định từ server Cobalt')}), 400

    except Exception as e:
        return jsonify({"error": f"Lỗi hệ thống: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
