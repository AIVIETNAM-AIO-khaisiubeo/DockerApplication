"""P1 integration boundary: isolated mock, Vision API and LLM API clients.

Only uses the contracts in docs/CONTRACT.md. No Streamlit/DB dependencies.
"""
from __future__ import annotations

import hashlib
import math
import os
import time
from typing import Any, Mapping

import requests

LABELS = ("Pneumonia", "Pleural Effusion", "Cardiomegaly", "Atelectasis", "Pneumothorax")
ALL_LABELS = (*LABELS, "No Finding")
PRIORITIES = ("EMERGENT", "URGENT", "ROUTINE")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024
VISION_TIMEOUT = (5, 120)  # connect, read (s)
LLM_TIMEOUT = (5, int(os.getenv("P1_LLM_TIMEOUT_S", "180")))


class ServiceError(Exception):
    """Error displayed by the UI without exposing request contents or credentials."""

    def __init__(self, service: str, detail: str):
        super().__init__(f"{service}: {detail}")
        self.service = service
        self.detail = detail


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ServiceError("API contract", f"Trường {name} phải là số.")
    result = float(value)
    if not math.isfinite(result):
        raise ServiceError("API contract", f"Trường {name} không hữu hạn.")
    return result


def validate_findings(findings: Any) -> dict[str, float]:
    if not isinstance(findings, dict):
        raise ServiceError("Vision", "Response 'probabilities' không phải JSON object.")
    missing = set(ALL_LABELS) - set(findings)
    if missing:
        raise ServiceError("Vision", f"Thiếu nhãn theo contract: {', '.join(sorted(missing))}.")
    output = {}
    for key in ALL_LABELS:
        score = _number(findings[key], f"probabilities.{key}")
        if not 0 <= score <= 1:
            raise ServiceError("Vision", f"Giá trị {key} ngoài khoảng [0, 1].")
        output[key] = score
    return output


def validate_vision(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ServiceError("Vision", "Response không phải JSON object.")
    findings = validate_findings(payload.get("probabilities"))
    if not isinstance(payload.get("metadata_removed"), bool):
        raise ServiceError("Vision", "Thiếu trường boolean metadata_removed.")
    if not isinstance(payload.get("mode"), str) or not payload["mode"]:
        raise ServiceError("Vision", "Thiếu trường mode.")
    latency = _number(payload.get("latency_ms"), "latency_ms")
    if latency < 0:
        raise ServiceError("Vision", "latency_ms không hợp lệ.")
    return {**payload, "probabilities": findings, "latency_ms": latency}


def validate_soap(payload: Any) -> dict:
    if not isinstance(payload, dict):
        raise ServiceError("LLM", "Response không phải JSON object.")
    soap = payload.get("soap")
    if not isinstance(soap, dict) or any(not isinstance(soap.get(k), str) or not soap[k].strip() for k in "SOAP"):
        raise ServiceError("LLM", "Trường soap phải có đủ S, O, A, P là chuỗi khác rỗng.")
    if payload.get("priority") not in PRIORITIES:
        raise ServiceError("LLM", "Trường priority phải là EMERGENT, URGENT hoặc ROUTINE.")
    if not isinstance(payload.get("mode"), str) or not payload["mode"]:
        raise ServiceError("LLM", "Thiếu trường mode.")
    latency = _number(payload.get("latency_ms"), "latency_ms")
    if latency < 0:
        raise ServiceError("LLM", "latency_ms không hợp lệ.")
    return {**payload, "latency_ms": latency}


def _http_json(service: str, method: str, url: str, **kwargs) -> dict:
    try:
        resp = requests.request(method, url, **kwargs)
    except requests.Timeout as exc:
        raise ServiceError(service, "Quá thời gian chờ. Kiểm tra log và trạng thái container.") from exc
    except requests.ConnectionError as exc:
        raise ServiceError(service, "Không kết nối được. Kiểm tra service và Docker network.") from exc
    except requests.RequestException as exc:
        raise ServiceError(service, f"Lỗi kết nối ({type(exc).__name__}).") from exc
    if resp.status_code >= 400:
        # Avoid dumping raw backend responses (may include input/user text).
        raise ServiceError(service, f"API trả HTTP {resp.status_code}. Kiểm tra endpoint và container logs.")
    try:
        data = resp.json()
    except ValueError as exc:
        raise ServiceError(service, "API không trả JSON hợp lệ.") from exc
    if not isinstance(data, dict):
        raise ServiceError(service, "API trả JSON không phải object.")
    return data


def health(url: str, service: str) -> dict:
    payload = _http_json(service, "GET", f"{url.rstrip('/')}/health", timeout=(2, 3))
    if payload.get("status") != "ok":
        raise ServiceError(service, "Healthcheck không báo status=ok.")
    return payload


def predict_image(url: str, filename: str, data: bytes, mime: str) -> dict:
    if not data:
        raise ServiceError("Vision", "Ảnh rỗng.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ServiceError("Vision", f"Ảnh lớn hơn giới hạn {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
    payload = _http_json(
        "Vision", "POST", f"{url.rstrip('/')}/predict",
        files={"file": (filename, data, mime or "application/octet-stream")}, timeout=VISION_TIMEOUT,
    )
    return validate_vision(payload)


def request_soap(url: str, symptoms: str, findings: Mapping[str, float]) -> dict:
    if not symptoms.strip():
        raise ServiceError("LLM", "Chưa nhập triệu chứng.")
    payload = _http_json(
        "LLM", "POST", f"{url.rstrip('/')}/soap",
        json={"symptoms": symptoms.strip(), "findings": dict(findings)}, timeout=LLM_TIMEOUT,
    )
    return validate_soap(payload)


def ui_mock_vision(data: bytes) -> dict:
    """Deterministic UI-only fixture; *not* an actual radiology model."""
    digest = hashlib.sha256(data).digest()
    findings = {label: round(0.05 + digest[i] / 255 * 0.65, 3) for i, label in enumerate(LABELS)}
    findings["No Finding"] = round(max(0., 1. - max(findings.values())), 3)
    return validate_vision({"probabilities": findings, "metadata_removed": False,
                            "mode": "ui-demo-mock", "latency_ms": 0.0})


def ui_mock_soap(symptoms: str, findings: Mapping[str, float]) -> dict:
    """A UI fixture only; intentionally avoids clinical interpretation."""
    return validate_soap({
        "soap": {"S": f"[MOCK UI] Đầu vào thử nghiệm: {symptoms.strip()}",
                 "O": "[MOCK UI] Đã nhận object findings từ dữ liệu thử nghiệm.",
                 "A": "[MOCK UI] Không có chẩn đoán thực; dữ liệu nhằm kiểm tra giao diện.",
                 "P": "[MOCK UI] Không sử dụng bản thử nghiệm cho quyết định lâm sàng."},
        "priority": "ROUTINE", "mode": "ui-demo-mock", "latency_ms": 0.0,
    })


def analyze(
    symptoms: str,
    *,
    image_name: str = "",
    image_bytes: bytes | None = None,
    image_mime: str = "image/png",
    manual_findings: dict[str, float] | None = None,
    ui_mock: bool = False,
    vision_url: str = "http://vision:8000",
    llm_url: str = "http://llm:8000",
) -> dict:
    """Single orchestrator used by UI and batch tests (without writing to database)."""
    symptoms = symptoms.strip()
    if not symptoms:
        raise ServiceError("P1", "Vui lòng nhập ghi chú thử nghiệm.")
    if len(symptoms) > 2000:
        raise ServiceError("P1", "Ghi chú tối đa 2000 ký tự, phù hợp Demo3.")
    started = time.perf_counter()
    if manual_findings is not None:
        findings = validate_findings(manual_findings)
        vision = {"probabilities": findings, "metadata_removed": False,
                  "mode": "manual", "latency_ms": 0.0}
        source = "manual"
    else:
        if image_bytes is None:
            raise ServiceError("P1", "Vui lòng tải ảnh hoặc chọn chế độ nhập điểm thủ công.")
        if not image_bytes:
            raise ServiceError("P1", "File tải lên rỗng.")
        if len(image_bytes) > MAX_UPLOAD_BYTES:
            raise ServiceError("P1", f"Ảnh vượt quá {MAX_UPLOAD_BYTES // (1024 * 1024)} MB.")
        vision = ui_mock_vision(image_bytes) if ui_mock else predict_image(vision_url, image_name, image_bytes, image_mime)
        source = "ui_mock" if ui_mock else "vision_api"
    llm = ui_mock_soap(symptoms, vision["probabilities"]) if ui_mock else request_soap(
        llm_url, symptoms, vision["probabilities"]
    )
    return {"vision": vision, "llm": llm, "source": source,
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 1)}
