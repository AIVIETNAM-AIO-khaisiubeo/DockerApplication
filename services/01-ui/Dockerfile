# Module 01 - UI (P1). Bản đơn giản chạy được; tối ưu sau nếu cần (Audit 1 chủ yếu về tái lập + Bind Mount).
FROM python:3.11-slim
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
