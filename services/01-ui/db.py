"""Các hàm giúp UI đọc và lưu lịch sử trong PostgreSQL.

- save_case(): lưu một ca thử nghiệm và kết quả.
- list_cases(): đọc các ca gần đây để hiển thị trong UI.
P4 quản lý cấu trúc bảng trong services/04-db/init.sql. Trao đổi với P4 trước khi đổi tên cột.
"""
import os
import time

import psycopg2
from psycopg2.extras import Json, RealDictCursor


def get_conn(retries: int = 10, delay: float = 2.0):
    for i in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "db"),
                dbname=os.getenv("POSTGRES_DB", "medtriage"),
                user=os.getenv("POSTGRES_USER", "medtriage"),
                password=os.getenv("POSTGRES_PASSWORD", "change_me"),
                connect_timeout=5,
            )
        except psycopg2.OperationalError:
            if i == retries - 1:
                raise
            time.sleep(delay)


def save_case(symptoms, probabilities, soap, priority, vision_ms, llm_ms) -> int:
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO cases (symptoms, probabilities, soap, priority, vision_latency_ms, llm_latency_ms)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (symptoms, Json(probabilities), Json(soap), priority, vision_ms, llm_ms),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def list_cases(limit: int = 50):
    conn = get_conn()
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, created_at, priority, symptoms, vision_latency_ms, llm_latency_ms "
                "FROM cases ORDER BY created_at DESC LIMIT %s",
                (limit,),
            )
            return cur.fetchall()
    finally:
        conn.close()
