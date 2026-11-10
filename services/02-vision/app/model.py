import math
import os

import numpy as np
import torch
import torchxrayvision as xrv # type: ignore

MODEL_NAME = "densenet121-res224-all"
DEFAULT_MODEL_DIR = os.getenv("MODEL_DIR", "models")

# nhãn của contract nhóm -> tên nhãn trong model (kiểm tra lại với CONTRACT.md)
CONTRACT_LABELS = {
    "Pneumonia": "Pneumonia",
    "Pleural Effusion": "Effusion",
    "Cardiomegaly": "Cardiomegaly",
    "Atelectasis": "Atelectasis",
    "Pneumothorax": "Pneumothorax",
}


def load_model(model_dir: str = DEFAULT_MODEL_DIR):
    """Nạp model một lần. Weights nằm trong model_dir; thiếu thì thư viện tự tải."""
    os.makedirs(model_dir, exist_ok=True)
    return xrv.models.get_model(MODEL_NAME, cache_dir=model_dir)


def predict(model, x: np.ndarray) -> dict[str, float]:
    """x: mảng float32 shape (1, H, W), đã chuẩn hóa/crop/resize bởi preprocess."""
    if x.ndim != 3 or x.shape[0] != 1:
        raise ValueError(f"Cần shape (1, H, W), nhận được {x.shape}")

    tensor = torch.from_numpy(np.ascontiguousarray(x, dtype=np.float32)).unsqueeze(0)
    with torch.no_grad():
        out = model(tensor)[0].cpu().numpy()

    return {
        name: float(score)
        for name, score in zip(model.pathologies, out)
        if name and not math.isnan(score)
    }


def to_contract(scores: dict[str, float]) -> dict[str, float]:
    """Lọc đúng 5 nhãn của contract. Thiếu nhãn thì báo lỗi ngay (KeyError)."""
    return {label: scores[src] for label, src in CONTRACT_LABELS.items()}