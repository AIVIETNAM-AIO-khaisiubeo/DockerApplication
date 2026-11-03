"""PostgreSQL access matching services/04-db/init.sql on main.

No DDL changes: DB schema stays P4's responsibility.
"""
import os
import time

import psycopg2
from psycopg2.extras import Json, RealDictCursor


def get_conn(retries: int = 3, delay: float = 1.0):
    for attempt in range(retries):
        try:
            return psycopg2.connect(
                host=os.getenv("POSTGRES_HOST", "db"),
                dbname=os.getenv("POSTGRES_DB", "medtriage"),
                user=os.getenv("POSTGRES_USER", "medtriage"),
                password=os.getenv("POSTGRES_PASSWORD", "change_me"),
                connect_timeout=3,
            )
        except psycopg2.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(delay)


def check_connection() -> bool:
    """One attempt for the UI status indicator, without DB writes."""
    conn = get_conn(retries=1)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            return cur.fetchone()[0] == 1
    finally:
        conn.close()


def save_case(symptoms: str, probabilities: dict, soap: dict,
              priority: str, vision_ms: float, llm_ms: float) -> int:
    conn = get_conn()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """INSERT INTO cases
                   (symptoms, probabilities, soap, priority, vision_latency_ms, llm_latency_ms)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (symptoms, Json(probabilities), Json(soap), priority, round(vision_ms), round(llm_ms)),
            )
            return cur.fetchone()[0]
    finally:
        conn.close()


def list_cases(limit: int = 50) -> list:
    conn = get_conn(retries=1)
    try:
        with conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, created_at, priority, symptoms, vision_latency_ms, llm_latency_ms "
                "FROM cases ORDER BY created_at DESC, id DESC LIMIT %s",
                (max(1, min(limit, 200)),),
            )
            return cur.fetchall()
    finally:
        conn.close()
