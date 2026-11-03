"""MedTriage AI – P1 Streamlit UI.

Works in two modes:
  UI_MOCK_BACKENDS=1: completely isolated UI development; no HTTP or PostgreSQL calls.
  UI_MOCK_BACKENDS=0: calls Vision /predict, LLM /soap, saves non-manual runs to DB.

For software demonstration only; never make a clinical decision using this UI.
"""
from __future__ import annotations

import os
from datetime import datetime

import pandas as pd
import streamlit as st

import client
import db

VISION_URL = os.getenv("VISION_URL", "http://vision:8000")
LLM_URL = os.getenv("LLM_URL", "http://llm:8000")
UI_MOCK = os.getenv("UI_MOCK_BACKENDS", "0") == "1"
PRIORITY_LABELS = {"EMERGENT": "🔴 EMERGENT", "URGENT": "🟠 URGENT", "ROUTINE": "🟢 ROUTINE"}

st.set_page_config(page_title="MedTriage AI – P1", page_icon="🩺", layout="wide")


def _status(label: str, url: str) -> None:
    try:
        result = client.health(url, label)
        mode = result.get("mode", "unknown")
        st.success(f"{label}: online · mode={mode}")
    except client.ServiceError as exc:
        st.error(f"{label}: offline ({exc.detail})")


def _session_history_add(result: dict, symptoms: str) -> None:
    history = st.session_state.setdefault("p1_local_history", [])
    history.insert(0, {
        "id": f"session-{len(history) + 1}",
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "priority": result["llm"]["priority"],
        "symptoms": symptoms,
        "vision_latency_ms": result["vision"]["latency_ms"],
        "llm_latency_ms": result["llm"]["latency_ms"],
        "source": result["source"],
    })


def _render_result(result: dict, case_id: int | None, save_error: str | None) -> None:
    vision, llm = result["vision"], result["llm"]
    st.subheader("Kết quả lần phân tích gần nhất")
    priority = PRIORITY_LABELS[llm["priority"]]
    if llm["priority"] == "EMERGENT":
        st.error(f"**Mức ưu tiên minh họa: {priority}**")
    elif llm["priority"] == "URGENT":
        st.warning(f"**Mức ưu tiên minh họa: {priority}**")
    else:
        st.info(f"**Mức ưu tiên minh họa: {priority}**")

    modes = f"Vision: {vision['mode']} · LLM: {llm['mode']}"
    st.caption(modes + (f" · DB case #{case_id}" if case_id else " · Không ghi PostgreSQL"))
    if vision["mode"] != "real" or llm["mode"] != "real":
        st.warning("Kết quả có thành phần mock/manual. Không phải dự đoán hoặc ghi chú y khoa đã kiểm chứng.")
    if save_error:
        st.error(f"Phân tích đã trả kết quả, nhưng KHÔNG lưu được lịch sử: {save_error}")

    m1, m2, m3 = st.columns(3)
    m1.metric("Vision API", f"{vision['latency_ms']:.0f} ms")
    m2.metric("LLM API", f"{llm['latency_ms']:.0f} ms")
    m3.metric("Vision + LLM (E2E)", f"{result['elapsed_ms']:.0f} ms")

    st.markdown("**Điểm đầu ra từ Vision (không mặc định là xác suất đã hiệu chuẩn)**")
    for key, value in sorted(vision["probabilities"].items(), key=lambda item: -item[1]):
        st.progress(float(value), text=f"{key}: {value:.1%}")
    st.markdown("**Ghi chú SOAP**")
    for key, title in (("S", "Subjective"), ("O", "Objective"),
                       ("A", "Assessment"), ("P", "Plan")):
        with st.container(border=True):
            st.markdown(f"**{key} — {title}**")
            # Display plain markdown, not untrusted HTML from an LLM.
            st.write(llm["soap"][key])
    with st.expander("JSON API / thông tin kiểm thử"):
        st.json({"vision": vision, "llm": llm, "source": result["source"]})


st.title("🩺 MedTriage AI")
st.caption("Nguyên mẫu phần mềm nghiên cứu Docker – không phải thiết bị y tế. Chỉ dùng dữ liệu tổng hợp hoặc đã được phép sử dụng; không nhập thông tin định danh bệnh nhân.")

if UI_MOCK:
    st.warning("UI ISOLATION MODE — Vision, LLM và lịch sử đều được GIẢ LẬP trong UI. Không gọi API hoặc PostgreSQL.")

with st.sidebar:
    st.header("Trạng thái hệ thống")
    if UI_MOCK:
        st.info("Vision: UI mock")
        st.info("LLM: UI mock")
        st.info("PostgreSQL: không sử dụng")
    else:
        _status("Vision", VISION_URL)
        _status("LLM", LLM_URL)
        try:
            db.check_connection()
            st.success("PostgreSQL: online")
        except Exception:
            st.error("PostgreSQL: offline (xem log db)")
    if st.button("Kiểm tra lại trạng thái", key="refresh_health"):
        st.rerun()
    st.divider()
    manual = st.toggle(
        "Chế độ test: nhập điểm Vision thủ công", value=False,
        help="Bỏ qua bước gửi ảnh sang P2, hữu ích khi P2 chưa sẵn sàng. Ca này không lưu PostgreSQL.",
    )
    if manual:
        st.warning("MANUAL TEST: điểm do người dùng đặt, không phải kết quả X-quang.")
    st.caption("Trong Docker Compose, Vision ở http://vision:8000 và LLM ở http://llm:8000.")

new_tab, history_tab = st.tabs(["Ca mới", "Lịch sử"])

with new_tab:
    input_col, output_col = st.columns([1, 1.25], gap="large")
    with input_col:
        st.subheader("1. Dữ liệu thử nghiệm")
        uploaded = None
        scores = None
        if manual:
            st.info("Nhập điểm mô phỏng từng nhãn. Không cần tải ảnh.")
            scores = {key: st.slider(key, min_value=0.0, max_value=1.0,
                                     value=0.10, step=0.01, key=f"p1_{key}") for key in client.LABELS}
            scores["No Finding"] = round(max(0.0, 1.0 - max(scores.values())), 3)
        else:
            uploaded = st.file_uploader("Ảnh thử nghiệm (PNG/JPG)", type=["png", "jpg", "jpeg"])
            if uploaded is not None:
                st.image(uploaded, caption=uploaded.name, use_column_width=True)
                st.caption(f"Dung lượng: {uploaded.size / 1024:.1f} KiB; tối đa {client.MAX_UPLOAD_BYTES // (1024 * 1024)} MiB.")
        symptoms = st.text_area("Mô tả triệu chứng giả lập", height=130, max_chars=2000,
                                placeholder="Ví dụ dữ liệu giả lập: ho, sốt, khó thở...")
        can_run = bool(symptoms.strip()) and (manual or uploaded is not None)
        run = st.button("Phân tích", type="primary", disabled=not can_run, use_container_width=True)
        if run:
            try:
                with st.spinner("Đang xử lý dữ liệu thử nghiệm..."):
                    raw = uploaded.getvalue() if uploaded is not None else None
                    result = client.analyze(
                        symptoms,
                        image_name=uploaded.name if uploaded is not None else "",
                        image_bytes=raw,
                        image_mime=uploaded.type if uploaded is not None else "image/png",
                        manual_findings=scores,
                        ui_mock=UI_MOCK,
                        vision_url=VISION_URL,
                        llm_url=LLM_URL,
                    )
                case_id, save_error = None, None
                if UI_MOCK or manual:
                    _session_history_add(result, symptoms)
                else:
                    try:
                        case_id = db.save_case(symptoms.strip(), result["vision"]["probabilities"],
                                               result["llm"]["soap"], result["llm"]["priority"],
                                               result["vision"]["latency_ms"], result["llm"]["latency_ms"])
                    except Exception as exc:
                        # Results remain visible even if P4 is temporarily unavailable.
                        save_error = f"{type(exc).__name__}. Kiểm tra PostgreSQL và schema cases."
                st.session_state["p1_latest"] = (result, case_id, save_error)
            except client.ServiceError as exc:
                st.error(f"{exc.service} — {exc.detail}")
            except Exception as exc:
                st.error(f"Lỗi giao diện ({type(exc).__name__}). Kiểm tra log UI.")
    with output_col:
        if "p1_latest" in st.session_state:
            _render_result(*st.session_state["p1_latest"])
        else:
            st.info("Nhập dữ liệu ở bên trái và bấm Phân tích để xem kết quả.")

with history_tab:
    st.subheader("2. Lịch sử ca thử nghiệm")
    if st.button("Làm mới lịch sử", key="reload_history"):
        st.rerun()
    local = st.session_state.get("p1_local_history", [])
    if UI_MOCK:
        st.caption("Chỉ là lịch sử trong phiên Streamlit; không lưu PostgreSQL.")
    else:
        st.caption("Ca gửi đủ Vision → LLM được lưu trong PostgreSQL; ca nhập thủ công chỉ lưu trong phiên UI.")
        try:
            saved = db.list_cases(limit=50)
            if saved:
                st.markdown("**Lịch sử PostgreSQL**")
                st.dataframe(pd.DataFrame(saved), use_container_width=True, hide_index=True)
            else:
                st.info("PostgreSQL chưa có ca thử nghiệm.")
        except Exception as exc:
            st.error(f"Không thể đọc PostgreSQL ({type(exc).__name__}). Vui lòng xem log database.")
    if local:
        st.markdown("**Lịch sử thử nghiệm trong phiên này**")
        st.dataframe(pd.DataFrame(local), use_container_width=True, hide_index=True)
    elif UI_MOCK:
        st.info("Chưa có lượt thử nào trong phiên này.")
