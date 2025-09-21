FROM python:3.11-slim

# 시스템 라이브러리 (오디오/코덱)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 성능/캐시: 모델 파일이 컨테이너마다 다시 받아지는 걸 줄이고 싶으면 볼륨 마운트 권장
RUN mkdir -p /data && chmod -R 777 /data

COPY app app

EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
