# BẢN NAIVE (baseline cho Audit 2/3) - cố ý chưa tối ưu.
# P3: `cp Dockerfile Dockerfile.naive` rồi tối ưu: multi-stage, cache layer, USER non-root.
FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
