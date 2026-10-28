"""Module 03 - LLM API (FastAPI)   [P3]

Hiện tại chạy chế độ MOCK dựa trên luật đơn giản để pipeline chạy được ngay.
Việc của P3:
  1. generate_soap_real(): gọi LLM (API ngoài hoặc model local trong /models) với prompt SOAP;
     ép đầu ra JSON hợp lệ, nếu lỗi parse thì có fallback.
  2. decide_priority(): chốt cách gán nhãn EMERGENT / URGENT / ROUTINE (nêu rõ trong báo cáo).
  3. Audit 3: dùng /debug/crash và /debug/allocate (cần ENABLE_DEBUG=1) để giả lập sự cố.
  Giữ nguyên hợp đồng API trong docs/CONTRACT.md.
"""
import os
import time

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

LLM_MODE = os.getenv("LLM_MODE", "mock")
RED_FLAGS = ["khó thở", "đau ngực", "ho ra máu", "tím tái", "dyspnea", "chest pain", "hemoptysis", "cyanosis"]
CRITICAL = {"Pneumothorax": 0.6, "Pneumonia": 0.7, "Pleural Effusion": 0.8}

app = FastAPI(title="MedTriage - LLM API")


class SoapRequest(BaseModel):
    symptoms: str
    findings: dict[str, float]


def decide_priority(symptoms: str, findings: dict[str, float]) -> str:
    s = symptoms.lower()
    flag = any(k in s for k in RED_FLAGS)
    critical = any(findings.get(k, 0) >= t for k, t in CRITICAL.items())
    top = max((v for k, v in findings.items() if k != "No Finding"), default=0)
    if critical and flag:
        return "EMERGENT"
    if critical or flag or top >= 0.5:
        return "URGENT"
    return "ROUTINE"


def generate_soap_mock(symptoms: str, findings: dict[str, float], priority: str) -> dict:
    ranked = sorted(((k, v) for k, v in findings.items() if k != "No Finding"), key=lambda kv: -kv[1])
    top_label, top_p = ranked[0] if ranked else ("Không rõ", 0.0)
    plan = {
        "EMERGENT": "Chuyển đánh giá/cấp cứu ngay bởi bác sĩ.",
        "URGENT": "Bác sĩ đánh giá trong ngày; cân nhắc chẩn đoán hình ảnh bổ sung.",
        "ROUTINE": "Theo dõi, tái khám theo lịch.",
    }[priority]
    return {
        "S": f"Bệnh nhân khai: {symptoms.strip()}",
        "O": "Mô hình thị giác ghi nhận: " + ", ".join(f"{k} {v:.0%}" for k, v in ranked[:3]),
        "A": f"[MOCK] Nghi ngờ {top_label} (xác suất {top_p:.0%}). Kết quả hỗ trợ, cần bác sĩ xác nhận.",
        "P": plan,
    }


def generate_soap_real(symptoms: str, findings: dict[str, float], priority: str) -> dict:
    """TODO(P3): gọi LLM thật, trả về dict có đủ 4 khóa S, O, A, P."""
    raise NotImplementedError("P3: chưa cài đặt generate_soap_real()")


@app.get("/health")
def health():
    return {"status": "ok", "mode": LLM_MODE}


@app.post("/soap")
def soap(req: SoapRequest):
    t0 = time.perf_counter()
    priority = decide_priority(req.symptoms, req.findings)
    try:
        note = (generate_soap_mock if LLM_MODE == "mock" else generate_soap_real)(req.symptoms, req.findings, priority)
    except NotImplementedError as e:
        raise HTTPException(501, str(e))
    return {"soap": note, "priority": priority, "mode": LLM_MODE, "latency_ms": int((time.perf_counter() - t0) * 1000)}


# ---- Chỉ phục vụ Audit 3 - tuyệt đối không bật khi demo/triển khai thật ----
if os.getenv("ENABLE_DEBUG") == "1":
    _hog: list = []

    @app.post("/debug/crash")
    def debug_crash():
        os._exit(1)

    @app.post("/debug/allocate")
    def debug_allocate(mb: int = 100):
        _hog.append(bytearray(b"\x01") * (mb * 1024 * 1024))
        return {"allocated_mb": sum(len(x) for x in _hog) // (1024 * 1024)}
