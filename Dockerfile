FROM python:3.9-slim

WORKDIR /app

# Cài đặt ffmpeg để yt-dlp hoạt động tốt nhất 
RUN apt-get update && apt-get install -y ffmpeg git && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt [cite: 3]

COPY . .

# Lắng nghe cổng từ biến môi trường của Render
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:$PORT app:app"]