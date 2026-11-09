
import os

import httpx
import streamlit as st

VISION_URL = os.getenv("VISION_URL", "http://127.0.0.1:8000")
LLM_URL = os.getenv("LLM_URL", "http://127.0.0.1:8001")
LABELS = ["Pneumonia", "Pleural Effusion", "Cardiomegaly", "Atelectasis", "Pneumothorax"]
PRIORITY_STYLE = {
    "EMERGENT": ("#dc2626", "CẤP CỨU"),
    "URGENT": ("#f59e0b", "KHẨN"),
    "ROUTINE": ("#16a34a", "THƯỜNG QUY"),
}
SOAP_TITLES = {"S": "Subjective - Chủ quan", "O": "Objective - Khách quan",
               "A": "Assessment - Đánh giá", "P": "Plan - Kế hoạch"}

st.set_page_config(page_title="MedTriage", page_icon="🩺", layout="wide")
st.markdown("""
<style>
.badge {padding: 14px 18px; border-radius: 10px; color: white; font-size: 1.4rem;
        font-weight: 700; text-align: center; margin-bottom: 8px;}
.soap {border-left: 5px solid #2563eb; background: rgba(37,99,235,.07);
       padding: 10px 14px; border-radius: 6px; margin-bottom: 10px;}
.soap b {color: #2563eb;}
</style>
""", unsafe_allow_html=True)


def check_health(url: str) -> dict | None:
    try:
        r = httpx.get(f"{url.rstrip('/')}/health", timeout=3)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def call_predict(url: str, name: str, data: bytes, mime: str) -> dict:
    r = httpx.post(f"{url.rstrip('/')}/predict",
                   files={"file": (name, data, mime or "application/octet-stream")}, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"Vision API {r.status_code}: {r.json().get('detail', r.text)}")
    return r.json()


def call_soap(url: str, symptoms: str, findings: dict[str, float]) -> dict:
    r = httpx.post(f"{url.rstrip('/')}/soap",
                   json={"symptoms": symptoms, "findings": findings}, timeout=120)
    if r.status_code >= 400:
        raise RuntimeError(f"LLM API {r.status_code}: {r.text}")
    return r.json()


# ---------------- Sidebar: cấu hình + trạng thái service ----------------
with st.sidebar:
    st.header("⚙️ Cấu hình")
    vision_url = st.text_input("Vision API (Demo 2)", VISION_URL)
    llm_url = st.text_input("LLM API (Demo 3)", LLM_URL)

    st.subheader("Trạng thái")
    vh, lh = check_health(vision_url), check_health(llm_url)
    if vh:
        st.success(f"Vision: {vh['status']} · mode={vh['mode']} · load {vh['model_load_ms']} ms")
    else:
        st.error("Vision: không kết nối được")
    if lh:
        st.success(f"LLM: {lh['status']} · mode={lh['mode']}")
    else:
        st.error("LLM: không kết nối được")
    if st.button("🔄 Kiểm tra lại"):
        st.rerun()

    st.divider()
    manual = st.toggle("Nhập điểm X-quang thủ công", value=not vh,
                       help="Dùng khi Vision API chưa chạy: bỏ qua bước /predict")

# ---------------- Main ----------------
st.title("🩺 MedTriage - Phân loại ưu tiên bệnh nhân")
st.caption("Ảnh X-quang ngực + triệu chứng → AI gợi ý mức ưu tiên và ghi chú SOAP. "
           "Kết quả chỉ mang tính hỗ trợ, cần bác sĩ xác nhận.")

col_in, col_out = st.columns([1, 1.3], gap="large")

with col_in:
    st.subheader("1. Dữ liệu đầu vào")
    upload, manual_scores = None, {}
    if manual:
        st.info("Chế độ thủ công: kéo thanh trượt điểm cho từng nhãn.")
        for label in LABELS:
            manual_scores[label] = st.slider(label, 0.0, 1.0, 0.1, 0.01)
    else:
        upload = st.file_uploader("Ảnh X-quang ngực", type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"])
        if upload:
            st.image(upload, caption=upload.name, use_container_width=True)

    symptoms = st.text_area("Triệu chứng bệnh nhân khai", height=120,
                            placeholder="VD: Ho, sốt cao 3 ngày, khó thở khi gắng sức...")
    run = st.button("🔍 Phân tích", type="primary", use_container_width=True)

with col_out:
    st.subheader("2. Kết quả")
    if not run:
        st.write("Nhập dữ liệu rồi bấm **Phân tích**.")
    elif not symptoms.strip():
        st.warning("Vui lòng nhập triệu chứng.")
    elif not manual and not upload:
        st.warning("Vui lòng tải ảnh X-quang lên.")
    else:
        try:
            # Bước 1: Vision API (Demo 2)
            if manual:
                probs = dict(manual_scores)
                probs["No Finding"] = round(max(0.0, 1 - max(probs.values())), 3)
                vision_info = "nhập thủ công"
            else:
                with st.spinner("Đang chạy model X-quang (Demo 2)..."):
                    pred = call_predict(vision_url, upload.name, upload.getvalue(), upload.type)
                probs = pred["probabilities"]
                vision_info = f"mode={pred['mode']} · {pred['latency_ms']} ms"

            # Bước 2: LLM API (Demo 3)
            with st.spinner("Đang tạo ghi chú SOAP (Demo 3)..."):
                soap = call_soap(llm_url, symptoms, probs)
        except (httpx.HTTPError, RuntimeError) as e:
            st.error(f"Lỗi: {e}")
            st.stop()

        color, text = PRIORITY_STYLE.get(soap["priority"], ("#6b7280", soap["priority"]))
        st.markdown(f'<div class="badge" style="background:{color}">{text}</div>',
                    unsafe_allow_html=True)

        st.markdown("**Điểm dự đoán X-quang** " f"<small>({vision_info})</small>",
                    unsafe_allow_html=True)
        for label, p in sorted(probs.items(), key=lambda kv: -kv[1]):
            flag = " 🔴" if label != "No Finding" and p > 0.5 else ""
            st.progress(min(max(p, 0.0), 1.0), text=f"{label}: {p * 100:.1f}%{flag}")

        st.markdown(f"**Ghi chú SOAP** <small>(mode={soap['mode']} · {soap['latency_ms']} ms)</small>",
                    unsafe_allow_html=True)
        for k in "SOAP":
            st.markdown(f'<div class="soap"><b>{SOAP_TITLES[k]}</b><br>{soap["soap"][k]}</div>',
                        unsafe_allow_html=True)

        with st.expander("JSON thô"):
            st.json({"predict": probs, "soap": soap})
