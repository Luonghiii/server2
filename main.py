import os
import uuid
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
from dotenv import load_dotenv

app = FastAPI()

# Load environment variables
load_dotenv()

# --- SỬA 1: Cho phép tất cả các nguồn gọi API ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép gọi từ mọi website khác
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/download")
async def download_video(url: str = Query(...), format: str = Query("best")):
    try:
        # Đường dẫn cookie để lách luật YouTube
        cookie_path = 'cookies.txt'
        
        # --- SỬA 2: Thêm cookiefile vào opts ---
        common_opts = {
            'quiet': True,
            'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
            'nocheckcertificate': True,
        }

        # Extract metadata
        with yt_dlp.YoutubeDL({'skip_download': True, **common_opts}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title", "video").replace("/", "-").replace("\\", "-")
            extension = "mp4"
            filename = f"{title}.{extension}"

        # Create a unique output template
        uid = uuid.uuid4().hex[:8]
        output_template = f"/tmp/{uid}.%(ext)s"

        ydl_opts = {
            'format': format,
            'outtmpl': output_template,
            'merge_output_format': 'mp4',
            **common_opts
        }

        # Download video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find actual downloaded file
        actual_file_path = None
        for f in os.listdir("/tmp"):
            if f.startswith(uid):
                actual_file_path = os.path.join("/tmp", f)
                break

        if not actual_file_path or not os.path.exists(actual_file_path):
            raise HTTPException(status_code=500, detail="Download failed or file not found.")

        # Stream file to client
        def iterfile():
            with open(actual_file_path, "rb") as f:
                yield from f
            try:
                os.unlink(actual_file_path)  # Xóa file tạm sau khi gửi xong
            except:
                pass

        return StreamingResponse(
            iterfile(),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi rồi ní ơi: {str(e)}")

@app.get("/")
async def root():
    return {"message": "API is online! Use /download?url=YOUR_URL"}

# --- SỬA 3: Nhận PORT từ Render ---
if __name__ == "__main__":
    import uvicorn
    # Render cấp PORT qua môi trường, mặc định dùng 10000
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)