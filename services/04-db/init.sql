-- Schema lịch sử ca bệnh (P4 sở hữu). KHÔNG lưu tên/ID bệnh nhân - dữ liệu đã được ẩn danh từ module 02.
CREATE TABLE IF NOT EXISTS cases (
    id                SERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    symptoms          TEXT        NOT NULL,
    probabilities     JSONB       NOT NULL,
    soap              JSONB       NOT NULL,
    priority          TEXT        NOT NULL CHECK (priority IN ('EMERGENT', 'URGENT', 'ROUTINE')),
    vision_latency_ms INTEGER,
    llm_latency_ms    INTEGER
);
CREATE INDEX IF NOT EXISTS idx_cases_created_at ON cases (created_at DESC);
-- TODO(P4): tài khoản DB quyền tối thiểu cho ứng dụng (chỉ INSERT/SELECT), tách khỏi tài khoản admin.
