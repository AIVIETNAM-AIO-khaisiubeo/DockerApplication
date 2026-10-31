import io

import numpy as np
import torchxrayvision as xrv # type: ignore
from PIL import Image, UnidentifiedImageError

MODEL_INPUT_SIZE = 224
MIN_SIDE = 32  # ảnh nhỏ hơn mức này coi như không hợp lệ

_center_crop = xrv.datasets.XRayCenterCrop()
_resize = xrv.datasets.XRayResizer(MODEL_INPUT_SIZE)


class InvalidImageError(ValueError):
    """Ảnh không hợp lệ: rỗng, hỏng, không phải ảnh, hoặc quá nhỏ."""


def decode_to_gray(raw: bytes) -> np.ndarray:
    """bytes -> mảng 2D uint8 (ảnh xám). Chỉ giữ pixel; EXIF/metadata bị bỏ lại."""
    if not raw:
        raise InvalidImageError("File rỗng")

    try:
        img = Image.open(io.BytesIO(raw))
        if img.mode.startswith("I") or img.mode == "F":
            # ảnh 16/32-bit: convert("L") sẽ cắt cụt giá trị, nên co dãn về 0..255
            arr = np.asarray(img, dtype=np.float32)
            lo, hi = float(arr.min()), float(arr.max())
            if hi == lo:
                gray = np.zeros(arr.shape, dtype=np.uint8)
            else:
                gray = ((arr - lo) / (hi - lo) * 255).astype(np.uint8)
        else:
            gray = np.asarray(img.convert("L"))
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError) as e:
        raise InvalidImageError("Không đọc được file ảnh") from e

    if min(gray.shape) < MIN_SIDE:
        raise InvalidImageError(f"Ảnh quá nhỏ: {gray.shape[1]}x{gray.shape[0]}")
    return gray


def prepare_for_model(raw: bytes) -> np.ndarray:
    """bytes -> mảng float32 shape (1, 224, 224), thang [-1024, 1024] cho model."""
    gray = decode_to_gray(raw)                 # (H, W) uint8
    img = xrv.utils.normalize(gray, 255)       # float32, [-1024, 1024]
    img = img[None, :, :]                      # (1, H, W)
    img = _center_crop(img)                    # (1, S, S) vuông
    return _resize(img)                        # (1, 224, 224) float32