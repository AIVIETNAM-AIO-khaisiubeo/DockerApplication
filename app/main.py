import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, Request, UploadFile

from app import model as vision
from app import preprocess, schemas

MODE = "real"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Chạy MỘT LẦN lúc khởi động. Mọi thứ trước `yield` là "startup".
    t0 = time.perf_counter()
    app.state.model = vision.load_model()
    app.state.model_load_ms = round((time.perf_counter() - t0) * 1000, 1)
    print(f"[startup] model loaded in {app.state.model_load_ms} ms")
    yield
    print("[shutdown] bye")  # phần sau `yield` chạy khi tắt server


app = FastAPI(title="MedTriage - Vision API", lifespan=lifespan)


@app.get("/health", response_model=schemas.HealthResponse)
def health(request: Request):
    return {
        "status": "ok",
        "mode": MODE,
        "model_load_ms": request.app.state.model_load_ms,
    }


@app.post("/predict", response_model=schemas.PredictResponse)
def predict(request: Request, file: UploadFile = File(...)):
    t0 = time.perf_counter()

    # 1. Đọc file, tối đa giới hạn + 1 byte để biết có vượt không
    raw = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, "File quá lớn")

    # 2. Tiền xử lý (file rỗng/hỏng/quá nhỏ -> InvalidImageError -> 400)
    try:
        x = preprocess.prepare_for_model(raw)
    except preprocess.InvalidImageError as e:
        raise HTTPException(400, str(e)) from e

    # 3. Dự đoán rồi lọc về 5 nhãn của contract
    scores = vision.predict(request.app.state.model, x)
    probs = {k: round(v, 3) for k, v in vision.to_contract(scores).items()}
    probs["No Finding"] = round(max(0.0, 1 - max(probs.values())), 3)

    # 4. Đóng gói response
    return {
        "probabilities": probs,
        "metadata_removed": True,
        "mode": MODE,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }

import uvicorn

# Khai báo các route FastAPI của bạn ở trên...

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)