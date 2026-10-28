# P1 — UI: môi trường để chạy trang web Streamlit.
# Docker cài các thư viện trong requirements.txt, sau đó khởi động app.py.
# Khi phát triển, file docker-compose.override.yml chia sẻ code từ laptop vào container.
FROM python:3.11-slim
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
