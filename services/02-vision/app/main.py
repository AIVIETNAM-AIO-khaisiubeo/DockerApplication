"""Module 02 - Vision API (FastAPI)   [P2]

Hiện tại chạy ở chế độ MOCK: kết quả giả nhưng ổn định (cùng ảnh -> cùng kết quả), để cả pipeline chạy được ngay.
Việc của P2:
  1. strip_metadata(): hỗ trợ DICOM (pydicom) ngoài PNG/JPG; xóa EXIF/DICOM tags thật sự.
  2. load_model() + predict_real(): nạp mô hình thị giác y khoa từ MODEL_DIR (/models = Named Volume).
  3. Giữ nguyên hợp đồng API trong docs/CONTRACT.md (đổi phải báo cả nhóm).
"""
import hashlib
import io
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, HTTPException, UploadFile
from PIL import Image

LABELS = ["Pneumonia", "Pleural Effusion", "Cardiomegaly", "Atelectasis", "Pneumothorax"]
MODEL_MODE = os.getenv("MODEL_MODE", "mock")
MODEL_DIR = os.getenv("MODEL_DIR", "/models")

_state = {"model": None, "model_load_ms": 0}


def load_model():
    """TODO(P2): nạp mô hình thật khi MODEL_MODE=real.
    Gợi ý: thư viện torchxrayvision (DenseNet huấn luyện trên nhiều bộ CXR). Đảm bảo weights được
    lưu trong MODEL_DIR (Named Volume) để lần khởi động sau không phải tải lại -> đo ở Audit 2.
    """
    if MODEL_MODE != "real":
        return None
    raise NotImplementedError("P2: chưa cài đặt load_model() cho chế độ real")


@asynccontextmanager
async def lifespan(_: FastAPI):
    t0 = time.perf_counter()
    _state["model"] = load_model()
    _state["model_load_ms"] = int((time.perf_counter() - t0) * 1000)
    yield


app = FastAPI(title="MedTriage - Vision API", lifespan=lifespan)


def strip_metadata(raw: bytes) -> Image.Image:
    """Trả về ảnh xám chỉ chứa pixel (không EXIF/metadata)."""
    if raw[128:132] == b"DICM":
        # TODO(P2): đọc DICOM bằng pydicom, lấy pixel_array, bỏ toàn bộ tag định danh
        raise HTTPException(415, "DICOM chưa được hỗ trợ trong bản scaffold (TODO P2)")
    try:
        img = Image.open(io.BytesIO(raw)).convert("L")
    except Exception:
        raise HTTPException(400, "Không đọc được file ảnh")
    return Image.frombytes("L", img.size, img.tobytes())  # dựng lại từ pixel -> bỏ metadata


def predict_mock(img: Image.Image) -> dict:
    digest = hashlib.sha256(img.tobytes() + str(img.size).encode()).digest()
    return {label: round(digest[i] / 255 * 0.95, 3) for i, label in enumerate(LABELS)}


def predict_real(model, img: Image.Image) -> dict:
    """TODO(P2): trả về dict {label: xác suất 0..1} cho đúng các nhãn trong LABELS."""
    raise NotImplementedError("P2: chưa cài đặt predict_real()")


@app.get("/health")
def health():
    return {"status": "ok", "mode": MODEL_MODE, "model_load_ms": _state["model_load_ms"]}


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    raw = await file.read()
    t0 = time.perf_counter()
    img = strip_metadata(raw)
    probs = predict_mock(img) if MODEL_MODE == "mock" else predict_real(_state["model"], img)
    probs["No Finding"] = round(max(0.0, 1 - max(probs.values())), 3)
    return {
        "probabilities": probs,
        "metadata_removed": True,
        "mode": MODEL_MODE,
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }
