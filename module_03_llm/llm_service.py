#llm_service.py
import json
import os
import time
import unicodedata

import httpx

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://host.docker.internal:11434/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen2.5:3b")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "60"))

THRESHOLD = 0.5                                                 
DANGEROUS = ["Pneumothorax", "Pneumonia", "Pleural Effusion"]  
SEVERE = ["tim tai", "lo mo", "hon me", "ngat", "kho tho nang", "ho ra mau nhieu"]
RED_FLAGS = ["kho tho", "dau nguc", "ho ra mau", "sot cao", "tho nhanh",
             "dyspnea", "chest pain", "hemoptysis", "cyanosis", "high fever"]
PLAN = {
    "EMERGENT": "Chuyển đánh giá/cấp cứu ngay bởi bác sĩ.",
    "URGENT": "Bác sĩ đánh giá trong ngày; cân nhắc chẩn đoán hình ảnh bổ sung.",
    "ROUTINE": "Theo dõi, tái khám theo lịch.",
}


def no_accent(text: str) -> str:
    """'Khó Thở' -> 'kho tho', để so khớp từ khóa dù gõ có dấu hay không."""
    text = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def positives(findings: dict[str, float]) -> list[str]:
    """Các nhãn bất thường có điểm > 0.5, xếp từ cao xuống thấp."""
    labels = [k for k, v in findings.items() if k != "No Finding" and v > THRESHOLD]
    return sorted(labels, key=lambda k: -findings[k])


def decide_priority(symptoms: str, findings: dict[str, float]) -> str:

    s = no_accent(symptoms)
    severe = any(k in s for k in SEVERE)
    flag = any(k in s for k in RED_FLAGS)
    found = positives(findings)
    danger = any(k in DANGEROUS for k in found)
    if severe or (danger and flag):
        return "EMERGENT"
    if found or flag:
        return "URGENT"
    return "ROUTINE"


def findings_text(findings: dict[str, float]) -> str:
    """'Pneumonia: 81%, Atelectasis: 55%'."""
    found = positives(findings)
    if not found:
        return "không có nhãn nào vượt ngưỡng 50%"
    return ", ".join("%s: %2.0f%%" % (k, findings[k] * 100) for k in found)


def soap_mock(symptoms: str, findings: dict[str, float], priority: str) -> dict:
    found = positives(findings)
    return {
        "S": f"Bệnh nhân khai: {symptoms.strip()}",
        "O": f"Mô hình X-quang ghi nhận: {findings_text(findings)}.",
        "A": (f"Nghi ngờ {', '.join(found)}." if found else "Chưa thấy bất thường rõ trên X-quang.")
             + " Kết quả hỗ trợ, cần bác sĩ xác nhận.",
        "P": PLAN[priority],
    }


def soap_real(symptoms: str, findings: dict[str, float], priority: str) -> dict:
    """Gọi LLM chuẩn OpenAI (Ollama/Groq/OpenAI). Lỗi gì cũng ném exception để /soap dùng template."""
    prompt = (
        "Viết ghi chú SOAP ngắn bằng tiếng Việt. Chỉ trả về JSON có 4 khóa S, O, A, P (giá trị là chuỗi).\n"
        f"Triệu chứng bệnh nhân khai: {symptoms}\n"
        f"Kết quả X-quang (điểm của model, chưa được bác sĩ kiểm chứng): {findings_text(findings)}\n"
        f"Mức ưu tiên đã chốt (không được đổi): {priority}\n"
        "Không bịa sinh hiệu hay xét nghiệm. Phần A ghi rõ đây là gợi ý của AI, cần bác sĩ xác nhận."
    )
    r = httpx.post(
        f"{LLM_BASE_URL.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {LLM_API_KEY}"} if LLM_API_KEY else {},
        json={"model": LLM_MODEL, "temperature": 0.2, "response_format": {"type": "json_object"},
              "messages": [{"role": "user", "content": prompt}]},
        timeout=LLM_TIMEOUT_S,
    )
    r.raise_for_status()
    note = json.loads(r.json()["choices"][0]["message"]["content"])
    return {k: str(note[k]) for k in "SOAP"}    


def spin(seconds: float) -> None:
    """Vòng lặp bận cho /debug/cpu (Audit 3)."""
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        pass
