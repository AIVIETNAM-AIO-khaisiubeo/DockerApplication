"""P1 — Giao diện web.

Khi chạy toàn hệ thống, UI gửi ảnh tới Vision, gửi triệu chứng và kết quả Vision tới LLM,
sau đó lưu kết quả vào PostgreSQL. Khi UI_MOCK_BACKENDS=1, các phản hồi chỉ được giả lập
để P1 kiểm tra giao diện độc lập; không gọi model thật hoặc lưu vào database.
"""
import hashlib
import os
import time

import pandas as pd
import requests
import streamlit as st

import db

VISION_URL = os.getenv("VISION_URL", "http://vision:8000")
LLM_URL = os.getenv("LLM_URL", "http://llm:8000")
ICON = {"EMERGENT": "🔴", "URGENT": "🟠", "ROUTINE": "🟢"}
UI_MOCK_BACKENDS = os.getenv("UI_MOCK_BACKENDS", "0") == "1"


def make_ui_mock_vision(image_bytes: bytes) -> dict:
    """Deterministic synthetic response for isolated UI development only."""
    digest = hashlib.sha256(image_bytes).digest()
    labels = ["Pneumonia", "Pleural Effusion", "Cardiomegaly", "Atelectasis", "Pneumothorax"]
    probabilities = {label: round(0.05 + (digest[i] / 255) * 0.65, 3) for i, label in enumerate(labels)}
    probabilities["No Finding"] = round(max(0.0, 1 - max(probabilities.values())), 3)
    return {
        "probabilities": probabilities,
        "metadata_removed": True,
        "mode": "ui-demo-mock",
        "latency_ms": 1,
    }


def make_ui_mock_llm(symptoms: str, findings: dict) -> dict:
    """Synthetic SOAP response for visual testing; not a medical assessment."""
    top_label, top_probability = max(
        ((key, value) for key, value in findings.items() if key != "No Finding"),
        key=lambda item: item[1],
        default=("Unknown", 0.0),
    )
    return {
        "soap": {
            "S": f"[DEMO MOCK] Synthetic note for test input: {symptoms.strip()}",
            "O": "[DEMO MOCK] Synthetic findings supplied by the UI development stub.",
            "A": f"[DEMO MOCK] Example label {top_label} ({top_probability:.0%}); not a model prediction.",
            "P": "[DEMO MOCK] UI-only test plan. Do not use for clinical decisions.",
        },
        "priority": "URGENT",
        "mode": "ui-demo-mock",
        "latency_ms": 1,
    }


st.set_page_config(page_title="MedTriage AI", page_icon="🩺", layout="wide")
st.title("🩺 MedTriage AI")
st.caption("Nguyên mẫu nghiên cứu - không phải thiết bị y tế. Không nhập thông tin định danh bệnh nhân.")
if UI_MOCK_BACKENDS:
    st.warning("UI ISOLATION MODE: Vision, LLM và lịch sử được mô phỏng trong UI. Không có model chạy và không có dữ liệu được lưu vào PostgreSQL.")

tab_new, tab_hist = st.tabs(["Ca mới", "Lịch sử"])

with tab_new:
    left, right = st.columns(2)
    with left:
        up = st.file_uploader("Ảnh X-quang ngực (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if up:
            st.image(up, use_column_width=True)
        symptoms = st.text_area("Ghi chú triệu chứng", height=140, placeholder="Ví dụ: sốt 3 ngày, ho có đờm, khó thở khi gắng sức")
        run = st.button("Phân tích", type="primary", disabled=(up is None or not symptoms.strip()))

    with right:
        if run:
            try:
                t0 = time.perf_counter()
                if UI_MOCK_BACKENDS:
                    with st.spinner("Tạo kết quả UI giả lập..."):
                        vision = make_ui_mock_vision(up.getvalue())
                        llm = make_ui_mock_llm(symptoms, vision["probabilities"])
                    total_ms = int((time.perf_counter() - t0) * 1000)
                    history = st.session_state.setdefault("ui_mock_history", [])
                    case_id = len(history) + 1
                    history.insert(0, {
                        "id": case_id,
                        "priority": llm["priority"],
                        "symptoms": symptoms,
                        "vision_latency_ms": vision["latency_ms"],
                        "llm_latency_ms": llm["latency_ms"],
                        "created_at": "UI demo session",
                    })
                else:
                    with st.spinner("Đang phân tích ảnh..."):
                        r1 = requests.post(f"{VISION_URL}/predict", files={"file": (up.name, up.getvalue(), up.type)}, timeout=120)
                        r1.raise_for_status()
                        vision = r1.json()
                    with st.spinner("Đang soạn bệnh án SOAP..."):
                        r2 = requests.post(f"{LLM_URL}/soap", json={"symptoms": symptoms, "findings": vision["probabilities"]}, timeout=300)
                        r2.raise_for_status()
                        llm = r2.json()
                    case_id = db.save_case(symptoms, vision["probabilities"], llm["soap"], llm["priority"],
                                           vision["latency_ms"], llm["latency_ms"])
                    total_ms = int((time.perf_counter() - t0) * 1000)

                st.subheader(f"{ICON.get(llm['priority'], '')} Mức ưu tiên: {llm['priority']}")
                case_label = "Demo" if UI_MOCK_BACKENDS else "Ca"
                st.caption(f"{case_label} #{case_id} | vision {vision['latency_ms']} ms | llm {llm['latency_ms']} ms | tổng {total_ms} ms | "
                           f"mode: {vision['mode']}/{llm['mode']}")
                st.markdown("**Xác suất bệnh lý**")
                st.bar_chart(pd.Series(vision["probabilities"]))
                st.markdown("**Bệnh án SOAP**")
                for key, title in [("S", "Subjective"), ("O", "Objective"), ("A", "Assessment"), ("P", "Plan")]:
                    st.markdown(f"**{key} - {title}:** {llm['soap'].get(key, '')}")
            except requests.RequestException as e:
                st.error(f"Lỗi gọi dịch vụ: {e}")  # TODO(P1): thông báo thân thiện theo từng service
            except Exception as e:  # noqa: BLE001
                st.error(f"Lỗi: {e}")

with tab_hist:
    if st.button("Làm mới"):
        st.rerun()
    try:
        rows = st.session_state.get("ui_mock_history", []) if UI_MOCK_BACKENDS else db.list_cases(50)
        st.dataframe(pd.DataFrame(rows), use_container_width=True) if rows else st.info("Chưa có ca nào trong phiên này.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Không đọc được lịch sử: {e}")
