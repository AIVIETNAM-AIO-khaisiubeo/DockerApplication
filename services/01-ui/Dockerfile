# P1 — UI: môi trường để chạy trang web Streamlit.
# Docker cài các thư viện trong requirements.txt, sau đó khởi động app.py.
# Khi phát triển, file docker-compose.override.yml chia sẻ code từ laptop vào container.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# User thường (không root) - Audit 4
RUN useradd --create-home --uid 10000 appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY --chown=appuser:appuser . .

USER appuser
EXPOSE 8501

HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=3)" || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
