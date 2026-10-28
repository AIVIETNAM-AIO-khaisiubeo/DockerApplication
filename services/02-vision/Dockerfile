# P2 — Bản Dockerfile đơn giản ban đầu, dùng làm mốc so sánh ở Audit 2.
# Trước khi tối ưu, hãy sao chép file này thành Dockerfile.naive để giữ bản gốc.
# Hiện tại, code được copy trước khi cài thư viện nên mỗi thay đổi code có thể làm Docker
# phải chạy lại bước cài thư viện. Đây là điều nhóm sẽ đo và cải thiện trong Audit 2.
# FROM: chọn môi trường Python có sẵn.
# WORKDIR: chọn thư mục làm việc trong container.
# COPY/RUN: copy file và cài thư viện từ requirements.txt.
# EXPOSE: ghi chú cổng bên trong container; file Compose mới mở cổng ra máy local.
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
