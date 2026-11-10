"""P1 + P4 — Giao diện MedTriage AI (demo).

Luồng tích hợp: ảnh -> Vision -> triệu chứng + kết quả Vision -> LLM
-> lưu PostgreSQL. Module 4 bổ sung mã bệnh nhân GIẢ LẬP và tra cứu
các ca phân tích trước đó.

UI_MOCK_BACKENDS=1: tất cả kết quả và lịch sử chỉ tồn tại trong
st.session_state; không gọi API bên ngoài hoặc truy cập PostgreSQL.

Chỉ dành cho nghiên cứu/demo, KHÔNG sử dụng dữ liệu bệnh nhân thật.
"""

from datetime import datetime, timezone
import hashlib
import os
import re
import time

import pandas as pd
import requests
import streamlit as st

import db


VISION_URL = os.getenv("VISION_URL", "http://vision:8000")
LLM_URL = os.getenv("LLM_URL", "http://llm:8000")
ICON = {"EMERGENT": "🔴", "URGENT": "🟠", "ROUTINE": "🟢"}
UI_MOCK_BACKENDS = os.getenv("UI_MOCK_BACKENDS", "0") == "1"
PATIENT_CODE_PATTERN = re.compile(r"[A-Z0-9_-]{1,64}")
SOAP_SECTIONS = [
    ("S", "Subjective"),
    ("O", "Objective"),
    ("A", "Assessment"),
    ("P", "Plan"),
]


def normalize_patient_code(raw_code: str) -> str:
    """Chuẩn hóa mã giả lập trước khi lưu/truy vấn."""
    return raw_code.strip().upper()


def valid_patient_code(code: str) -> bool:
    """Chỉ cho phép ký tự cơ bản trong mã giả lập (mã trống là tùy chọn)."""
    return not code or bool(PATIENT_CODE_PATTERN.fullmatch(code))


def make_ui_mock_vision(image_bytes: bytes) -> dict:
    """Kết quả cố định theo hash ảnh; chỉ phục vụ thử giao diện."""
    digest = hashlib.sha256(image_bytes).digest()
    labels = [
        "Pneumonia",
        "Pleural Effusion",
        "Cardiomegaly",
        "Atelectasis",
        "Pneumothorax",
    ]
    probabilities = {
        label: round(0.05 + (digest[i] / 255) * 0.65, 3)
        for i, label in enumerate(labels)
    }
    probabilities["No Finding"] = round(
        max(0.0, 1 - max(probabilities.values())), 3
    )
    return {
        "probabilities": probabilities,
        "metadata_removed": True,
        "mode": "ui-demo-mock",
        "latency_ms": 1,
    }


def make_ui_mock_llm(symptoms: str, findings: dict) -> dict:
    """SOAP giả lập phục vụ thử UI; không phải đánh giá y khoa."""
    top_label, top_probability = max(
        ((key, value) for key, value in findings.items() if key != "No Finding"),
        key=lambda item: item[1],
        default=("Unknown", 0.0),
    )
    return {
        "soap": {
            "S": f"[DEMO MOCK] Synthetic note for test input: {symptoms.strip()}",
            "O": "[DEMO MOCK] Synthetic findings supplied by the UI development stub.",
            "A": (
                f"[DEMO MOCK] Example label {top_label} "
                f"({top_probability:.0%}); not a model prediction."
            ),
            "P": "[DEMO MOCK] UI-only test plan. Do not use for clinical decisions.",
        },
        "priority": "URGENT",
        "mode": "ui-demo-mock",
        "latency_ms": 1,
    }


def show_soap(soap: dict) -> None:
    """Hiển thị bốn phần của bản ghi SOAP."""
    for key, title in SOAP_SECTIONS:
        st.write(f"**{key} — {title}:**", soap.get(key, "") or "Chưa có")


def show_case_details(record: dict) -> None:
    """Hiển thị chi tiết một bản ghi đã lưu, dù từ DB hoặc UI mock."""
    st.write("**Triệu chứng:**", record.get("symptoms") or "Chưa có")
    st.write("**Mức ưu tiên:**", record.get("priority") or "Chưa có")
    st.markdown("**Kết quả SOAP**")
    show_soap(record.get("soap") or {})
    probabilities = record.get("probabilities") or {}
    if probabilities:
        st.markdown("**Kết quả Vision**")
        st.json(probabilities)


def show_patient_history(records: list, *, mock: bool) -> None:
    """Hiển thị các ca thuộc một mã bệnh nhân đã được tra cứu."""
    if not records:
        st.info("Chưa có ca phân tích nào cho mã bệnh nhân giả lập này.")
        return

    st.success(f"Tìm thấy {len(records)} ca phân tích (tối đa 50 ca gần nhất).")
    if mock:
        st.caption("Lịch sử mock chỉ tồn tại trong phiên Streamlit hiện tại.")

    for record in records:
        case_id = record.get("case_id", record.get("id"))
        created_at = str(record.get("created_at", ""))
        priority = record.get("priority", "")
        title = f"Ca #{case_id} | {created_at} | {priority}"
        with st.expander(title):
            show_case_details(record)


st.set_page_config(page_title="MedTriage AI", page_icon="🩺", layout="wide")
st.title("🩺 MedTriage AI")
st.caption(
    "Nguyên mẫu nghiên cứu, không phải thiết bị y tế. "
    "Chỉ sử dụng mã bệnh nhân và dữ liệu GIẢ LẬP; không nhập dữ liệu định danh thật."
)

if UI_MOCK_BACKENDS:
    st.warning(
        "UI ISOLATION MODE: Vision, LLM và lịch sử được mô phỏng trong UI. "
        "Không có model thực chạy và không có dữ liệu lưu vào PostgreSQL."
    )

# Hai tab của P1 vẫn được giữ nguyên.
tab_new, tab_hist = st.tabs(["Ca mới", "Lịch sử"])

with tab_new:
    left, right = st.columns(2)

    with left:
        patient_code = normalize_patient_code(
            st.text_input(
                "Mã bệnh nhân (giả lập, không bắt buộc)",
                placeholder="Ví dụ: PAT-DEMO-001",
                max_chars=64,
                help="Chỉ dùng mã demo. Để trống nếu ca không cần liên kết lịch sử.",
            )
        )
        patient_code_ok = valid_patient_code(patient_code)
        if not patient_code_ok:
            st.warning("Mã chỉ được chứa chữ A-Z, số 0-9, dấu - hoặc dấu _.")

        up = st.file_uploader(
            "Ảnh X-quang ngực (PNG/JPG)",
            type=["png", "jpg", "jpeg"],
        )
        if up is not None:
            st.image(up, use_column_width=True)

        symptoms = st.text_area(
            "Ghi chú triệu chứng (giả lập)",
            height=140,
            placeholder="Ví dụ: sốt 3 ngày, ho có đờm, khó thở khi gắng sức",
        )
        run = st.button(
            "Phân tích",
            type="primary",
            disabled=(up is None or not symptoms.strip() or not patient_code_ok),
        )

    with right:
        if run:
            try:
                t0 = time.perf_counter()
                if UI_MOCK_BACKENDS:
                    with st.spinner("Tạo kết quả UI giả lập..."):
                        vision = make_ui_mock_vision(up.getvalue())
                        llm = make_ui_mock_llm(symptoms, vision["probabilities"])
                    total_ms = int((time.perf_counter() - t0) * 1000)

                    # UI mock không chạm vào DB. Lưu kết quả ở phiên Streamlit.
                    history = st.session_state.setdefault("ui_mock_history", [])
                    case_id = st.session_state.get("ui_mock_next_id", 1)
                    st.session_state["ui_mock_next_id"] = case_id + 1
                    history.insert(
                        0,
                        {
                            "id": case_id,
                            "patient_code": patient_code or None,
                            "priority": llm["priority"],
                            "symptoms": symptoms,
                            "probabilities": vision["probabilities"],
                            "soap": llm["soap"],
                            "vision_latency_ms": vision["latency_ms"],
                            "llm_latency_ms": llm["latency_ms"],
                            "created_at": datetime.now(timezone.utc).strftime(
                                "%Y-%m-%d %H:%M:%S UTC"
                            ),
                        },
                    )
                else:
                    with st.spinner("Đang phân tích ảnh..."):
                        r1 = requests.post(
                            f"{VISION_URL}/predict",
                            files={"file": (up.name, up.getvalue(), up.type)},
                            timeout=120,
                        )
                        r1.raise_for_status()
                        vision = r1.json()

                    with st.spinner("Đang soạn ghi chú SOAP..."):
                        r2 = requests.post(
                            f"{LLM_URL}/soap",
                            json={
                                "symptoms": symptoms,
                                "findings": vision["probabilities"],
                            },
                            timeout=300,
                        )
                        r2.raise_for_status()
                        llm = r2.json()

                    # db.save_case() đã được P4 mở rộng với patient_code tùy chọn.
                    case_id = db.save_case(
                        symptoms,
                        vision["probabilities"],
                        llm["soap"],
                        llm["priority"],
                        # Vision trả float (ms), cột DB là INTEGER
                        int(round(vision["latency_ms"])),
                        int(round(llm["latency_ms"])),
                        patient_code=patient_code or None,
                    )
                    total_ms = int((time.perf_counter() - t0) * 1000)

                st.subheader(
                    f"{ICON.get(llm['priority'], '')} Mức ưu tiên: {llm['priority']}"
                )
                case_label = "Demo" if UI_MOCK_BACKENDS else "Ca"
                st.caption(
                    f"{case_label} #{case_id} | "
                    f"vision {vision['latency_ms']} ms | "
                    f"llm {llm['latency_ms']} ms | tổng {total_ms} ms | "
                    f"mode: {vision['mode']}/{llm['mode']}"
                )
                if patient_code:
                    st.write("**Mã bệnh nhân giả lập:**", patient_code)
                st.markdown("**Xác suất bệnh lý (chỉ phục vụ nghiên cứu/demo)**")
                st.bar_chart(pd.Series(vision["probabilities"]))
                st.markdown("**Ghi chú SOAP**")
                show_soap(llm["soap"])
                st.info(
                    "Kết quả nghiên cứu/demo, không sử dụng để chẩn đoán "
                    "hoặc đưa ra quyết định điều trị."
                )
            except requests.RequestException as exc:
                st.error(f"Lỗi gọi dịch vụ Vision/LLM: {exc}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Lỗi phân tích hoặc lưu dữ liệu: {exc}")

with tab_hist:
    st.subheader("Tra cứu lịch sử theo mã bệnh nhân giả lập")
    search_code = normalize_patient_code(
        st.text_input(
            "Nhập mã bệnh nhân để xem hồ sơ và các ca trước đó",
            placeholder="PAT-DEMO-001",
            max_chars=64,
            key="lookup_patient_code",
        )
    )

    if st.button("Làm mới lịch sử"):
        st.rerun()

    if search_code and not valid_patient_code(search_code):
        st.warning("Mã chỉ được chứa chữ A-Z, số 0-9, dấu - hoặc dấu _.")
    elif search_code:
        try:
            if UI_MOCK_BACKENDS:
                # Chế độ UI riêng: không truy cập PostgreSQL.
                mock_profiles = st.session_state.setdefault("ui_mock_profiles", {})
                saved_history = mock_profiles.get(search_code, "")
                mock_rows = st.session_state.get("ui_mock_history", [])
                records = [
                    row for row in mock_rows
                    if row.get("patient_code") == search_code
                ][:50]
                profile_exists = search_code in mock_profiles
            else:
                # Đọc hồ sơ riêng: vẫn xem được tiền sử khi bệnh nhân chưa có ca nào.
                profile = db.get_patient(search_code)
                saved_history = (profile or {}).get("medical_history") or ""
                records = db.get_patient_history(search_code, limit=50)
                profile_exists = profile is not None
        except Exception as exc:  # noqa: BLE001
            st.error(f"Không tải được hồ sơ giả lập: {exc}")
        else:
            st.markdown("### Hồ sơ bệnh nhân giả lập")
            st.write("**Mã bệnh nhân:**", search_code)
            if not profile_exists:
                st.caption("Mã này chưa có hồ sơ. Bạn có thể tạo hồ sơ mới bên dưới.")

            with st.expander("Thêm / sửa tiền sử giả lập", expanded=not profile_exists):
                with st.form(key=f"patient_profile_form_{search_code}"):
                    new_history = st.text_area(
                        "Tiền sử bệnh (dữ liệu mô phỏng)",
                        value=saved_history,
                        max_chars=2000,
                        height=120,
                        key=f"medical_history_{search_code}",
                        help=(
                            "Chỉ nhập ví dụ giả lập. Để trống rồi lưu để xoá "
                            "tiền sử mô phỏng đã nhập."
                        ),
                    )
                    save_profile = st.form_submit_button("Lưu / cập nhật tiền sử")

                if save_profile:
                    try:
                        normalized_history = new_history.strip()
                        if UI_MOCK_BACKENDS:
                            mock_profiles[search_code] = normalized_history
                        else:
                            db.upsert_patient(search_code, normalized_history)
                        saved_history = normalized_history
                        profile_exists = True
                        st.success("Đã lưu hồ sơ giả lập thành công.")
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Không lưu được tiền sử giả lập: {exc}")

            st.write("**Tiền sử đã lưu (demo):**", saved_history or "Chưa có")
            st.markdown("### Các lần phân tích trước")
            show_patient_history(records, mock=UI_MOCK_BACKENDS)
    else:
        # Giữ nguyên danh sách các ca gần đây của P1 khi chưa nhập mã.
        st.markdown("**50 ca phân tích gần nhất**")
        try:
            rows = (
                st.session_state.get("ui_mock_history", [])[:50]
                if UI_MOCK_BACKENDS
                else db.list_cases(50)
            )
            if rows:
                summary_fields = [
                    "id", "patient_code", "created_at", "priority", "symptoms",
                    "vision_latency_ms", "llm_latency_ms",
                ]
                df = pd.DataFrame(rows)
                st.dataframe(
                    df[[col for col in summary_fields if col in df.columns]],
                    use_container_width=True,
                )
            else:
                st.info("Chưa có ca nào được lưu.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Không đọc được danh sách ca: {exc}")
