# syntax=docker/dockerfile:1

############################
# Stage 1: builder - cài thư viện vào một venv
############################
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build
# Chỉ copy requirements trước: sửa code không làm mất cache của bước cài thư viện
COPY requirements.txt .
RUN pip install -r requirements.txt \
 && python -c "import torch; assert '+cpu' in torch.__version__, 'Cài nhầm torch bản CUDA: ' + torch.__version__"

############################
# Stage 2: runtime - chỉ giữ thứ cần để chạy
############################
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    MODEL_DIR=/models \
    MAX_UPLOAD_MB=10

# User thường (không root) + thư mục weights thuộc quyền user đó
RUN useradd --create-home --uid 10001 appuser \
 && mkdir -p /models \
 && chown appuser:appuser /models

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY app ./app

USER appuser
EXPOSE 8000

# slim không có curl nên dùng Python để gọi /health
HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1

# Một worker duy nhất để không nạp model nhiều lần
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]