# --- 1. 빌드 스테이지 ---
# 라이브러리를 설치할 빌드 전용 환경을 만듭니다.
FROM python:3.11-slim as builder

WORKDIR /app

# 시스템 라이브러리 설치 (SciPy 빌드를 위한 LAPACK/BLAS 포함)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 git \
    gcc gfortran \
    liblapack-dev libblas-dev \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

# numba 캐시 폴더 지정 (이전 에러 해결)
ENV NUMBA_CACHE_DIR=/tmp
# pip 캐시 비활성화
ENV PIP_NO_CACHE_DIR=off

# requirements.txt를 먼저 복사하여 Docker 캐시 활용 극대화
COPY requirements.txt .

# 라이브러리 설치
# --prefix를 사용해 특정 폴더에 라이브러리를 설치합니다.
RUN pip install --prefix=/install -r requirements.txt


# --- 2. 최종 스테이지 ---
# 실제 서버를 실행할 최종 이미지를 만듭니다.
FROM python:3.11-slim

WORKDIR /app

# 시스템 라이브러리 (runtime용 LAPACK/BLAS 및 curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg libsndfile1 \
    liblapack3 libblas3 && \
    rm -rf /var/lib/apt/lists/*

# 환경 변수 설정
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV NUMBA_CACHE_DIR=/tmp

# 비-루트 사용자 생성
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# 빌드 스테이지에서 설치한 라이브러리만 복사
COPY --from=builder /install /usr/local

# 애플리케이션 코드 복사
COPY app app

# 디렉토리 생성 및 소유권 변경 (root로 실행)
RUN mkdir -p /data/models /data/raw /data/prep /data/out && \
    chown -R appuser:appgroup /data && \
    chmod -R 755 /data && \
    chown -R appuser:appgroup /app

# 비-루트 사용자로 전환
USER appuser

# 런타임에 권한을 다시 확인하는 엔트리포인트 스크립트 생성
USER root
RUN echo '#!/bin/bash\n\
mkdir -p /data/models /data/raw /data/prep /data/out\n\
chown -R appuser:appgroup /data\n\
chmod -R 755 /data\n\
exec "$@"' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

EXPOSE 8081

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8081/docs || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["su", "appuser", "-c", "uvicorn app.main:app --host 0.0.0.0 --port 8081"]