"""Các hàm lưu, đọc lịch sử ca phân tích và hồ sơ bệnh nhân GIẢ LẬP.

P4 mở rộng db.py, giữ tương thích lời gọi save_case() của P1.
Chỉ dùng dữ liệu mô phỏng; không nhập hồ sơ bệnh nhân thật.
"""

import os
import re
import time

import psycopg2
from psycopg2.extras import Json, RealDictCursor

PATIENT_CODE_PATTERN = re.compile(r"[A-Z0-9_-]{1,64}")
MAX_MEDICAL_HISTORY_CHARS = 2000


def normalize_patient_code(patient_code: str) -> str:
    """Chuẩn hoá và xác thực mã demo, không chấp nhận mã định dạng tự do."""
    if not isinstance(patient_code, str):
        raise ValueError("Mã bệnh nhân giả lập phải là chuỗi")
    code = patient_code.strip().upper()
    if not PATIENT_CODE_PATTERN.fullmatch(code):
        raise ValueError("Mã chỉ chứa A-Z, 0-9, '-' hoặc '_' (tối đa 64 ký tự)")
    return code


def get_conn(retries: int = 10, delay: float = 2.0):
    for i in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "db"),
                port=int(os.getenv("POSTGRES_PORT", "5432")),
                dbname=os.getenv("POSTGRES_DB", "medtriage"),
                user=os.getenv("POSTGRES_USER", "medtriage"),
                password=os.getenv("POSTGRES_PASSWORD", "change_me"),
                connect_timeout=5,
            )
        except psycopg2.OperationalError:
            if i == retries - 1:
                raise
            time.sleep(delay)


def save_case(
    symptoms,
    probabilities,
    soap,
    priority,
    vision_ms,
    llm_ms,
    patient_code=None,
) -> int:
    """Lưu ca phân tích, có thể liên kết với hồ sơ mã bệnh nhân giả lập."""
    code = normalize_patient_code(patient_code) if patient_code else None
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                patient_id = None
                if code:
                    cur.execute(
                        """
                        INSERT INTO patients (patient_code)
                        VALUES (%s)
                        ON CONFLICT (patient_code) DO NOTHING
                        """,
                        (code,),
                    )
                    cur.execute(
                        "SELECT id FROM patients WHERE patient_code = %s",
                        (code,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise RuntimeError("Không tìm thấy hồ sơ demo sau khi tạo")
                    patient_id = row[0]

                cur.execute(
                    """
                    INSERT INTO cases (
                        patient_id, symptoms, probabilities, soap, priority,
                        vision_latency_ms, llm_latency_ms
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        patient_id,
                        symptoms,
                        Json(probabilities),
                        Json(soap),
                        priority,
                        vision_ms,
                        llm_ms,
                    ),
                )
                return cur.fetchone()[0]
    finally:
        conn.close()


def list_cases(limit: int = 50):
    """Đọc các ca gần nhất, giữ API dùng trong giao diện P1."""
    limit = max(1, min(int(limit), 100))
    conn = get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, created_at, priority, symptoms,
                       vision_latency_ms, llm_latency_ms
                FROM cases
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_patient_history(patient_code: str, limit: int = 50):
    """Các ca trước của một mã demo, từ mới nhất đến cũ nhất."""
    code = normalize_patient_code(patient_code)
    limit = max(1, min(int(limit), 100))
    conn = get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT p.patient_code, p.medical_history,
                       c.id AS case_id, c.created_at, c.symptoms,
                       c.probabilities, c.soap, c.priority
                FROM patients p
                JOIN cases c ON c.patient_id = p.id
                WHERE p.patient_code = %s
                ORDER BY c.created_at DESC, c.id DESC
                LIMIT %s
                """,
                (code, limit),
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_patient(patient_code: str):
    """Đọc hồ sơ ngay cả khi bệnh nhân demo chưa có ca phân tích nào."""
    code = normalize_patient_code(patient_code)
    conn = get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, patient_code, medical_history, created_at
                FROM patients
                WHERE patient_code = %s
                """,
                (code,),
            )
            row = cur.fetchone()
            return dict(row) if row is not None else None
    finally:
        conn.close()


def upsert_patient(patient_code: str, medical_history: str = ""):
    """Tạo/cập nhật hồ sơ demo bằng một lệnh UPSERT có tham số."""
    code = normalize_patient_code(patient_code)
    if not isinstance(medical_history, str):
        raise ValueError("Tiền sử giả lập phải là chuỗi")
    history = medical_history.strip()
    if len(history) > MAX_MEDICAL_HISTORY_CHARS:
        raise ValueError("Tiền sử giả lập tối đa 2000 ký tự")

    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO patients (patient_code, medical_history)
                    VALUES (%s, %s)
                    ON CONFLICT (patient_code) DO UPDATE
                    SET medical_history = EXCLUDED.medical_history
                    RETURNING id, patient_code, medical_history, created_at
                    """,
                    (code, history),
                )
                return dict(cur.fetchone())
    finally:
        conn.close()
