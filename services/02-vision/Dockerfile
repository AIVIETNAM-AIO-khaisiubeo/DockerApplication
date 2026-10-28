# BẢN NAIVE (baseline cho Audit 2) - cố ý chưa tối ưu.
# P2: BƯỚC ĐẦU TIÊN -> `cp Dockerfile Dockerfile.naive` để giữ baseline, rồi viết lại Dockerfile này:
#   - multi-stage build + base image slim
#   - copy requirements.txt & pip install TRƯỚC khi copy mã nguồn (Layer Caching)
#   - tạo và chạy bằng USER không phải root (Audit 4)
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
