"""Module 01 - Giao diện (Streamlit)   [P1]
Luồng: ảnh + triệu chứng -> VISION /predict -> LLM /soap -> lưu DB -> hiển thị.
Việc của P1: làm đẹp/hoàn thiện UI, xử lý lỗi khi service sập, trang lịch sử, hiển thị độ trễ.
"""
import os
import time

import pandas as pd
import requests
import streamlit as st

import db

VISION_URL = os.getenv("VISION_URL", "http://vision:8000")
LLM_URL = os.getenv("LLM_URL", "http://llm:8000")
ICON = {"EMERGENT": "🔴", "URGENT": "🟠", "ROUTINE": "🟢"}

st.set_page_config(page_title="MedTriage AI", page_icon="🩺", layout="wide")
st.title("🩺 MedTriage AI")
st.caption("Nguyên mẫu nghiên cứu - chỉ hỗ trợ ra quyết định, không phải thiết bị y tế. Không nhập thông tin định danh bệnh nhân.")

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
                st.caption(f"Ca #{case_id} | vision {vision['latency_ms']} ms | llm {llm['latency_ms']} ms | tổng {total_ms} ms | "
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
        rows = db.list_cases(50)
        st.dataframe(pd.DataFrame(rows), use_container_width=True) if rows else st.info("Chưa có ca nào.")
    except Exception as e:  # noqa: BLE001
        st.error(f"Không đọc được lịch sử: {e}")
