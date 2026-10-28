# P3 — Bản Dockerfile đơn giản ban đầu, dùng làm mốc so sánh ở Audit 2/3.
# Trước khi tối ưu, hãy sao chép file này thành Dockerfile.naive để giữ bản gốc.
# Bản này copy code trước rồi mới cài thư viện; khi sửa code, Docker có thể phải cài
# thư viện lại. Audit 2 sẽ giúp nhóm đo sự khác biệt trước và sau khi tối ưu.
# Sau khi đã lưu bản gốc, P3 có thể cải thiện thứ tự COPY/RUN, dung lượng image và quyền chạy.
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
