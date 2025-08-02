# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY trade_batch/requirements.docker.txt requirements.txt
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# 런타임 의존성만 설치
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# builder에서 설치된 패키지 복사
COPY --from=builder /root/.local /root/.local

# trade_common과 소스 코드 복사
COPY trade_common/ /app/trade_common/
COPY trade_batch/src/ ./src/
COPY trade_batch/sql/ ./sql/

# trade_common 설치
RUN cd /app/trade_common && pip install --user -e .

# 환경 변수
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# 포트 노출
EXPOSE 8082

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; r = requests.get('http://localhost:8082/health'); exit(0 if r.status_code == 200 else 1)"

# 실행
CMD ["python", "-m", "src.main"]