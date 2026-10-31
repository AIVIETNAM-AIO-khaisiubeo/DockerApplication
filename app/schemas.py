from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(description="'ok' khi service đã sẵn sàng")
    mode: Literal["mock", "real"] = Field(description="Kết quả từ phần giả lập hay model thật")
    model_load_ms: float = Field(description="Thời gian nạp model lúc khởi động (ms)")


class PredictResponse(BaseModel):
    probabilities: dict[str, float] = Field(
        description="Điểm dự đoán theo từng nhãn của contract, gồm cả 'No Finding'"
    )
    metadata_removed: bool = Field(description="Đã loại metadata khỏi ảnh hay chưa")
    mode: Literal["mock", "real"]
    latency_ms: float = Field(description="Thời gian xử lý (ms)")