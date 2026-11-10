CREATE TABLE IF NOT EXISTS patients (
    id BIGSERIAL PRIMARY KEY,
    patient_code VARCHAR(64) UNIQUE NOT NULL,
    medical_history TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Liên kết ca phân tích với bệnh nhân.
-- Cho phép NULL để tương thích các ca cũ.
ALTER TABLE cases
ADD COLUMN IF NOT EXISTS patient_id BIGINT
REFERENCES patients(id);

-- Tăng tốc truy vấn lịch sử bệnh nhân.
CREATE INDEX IF NOT EXISTS idx_cases_patient_date
ON cases(patient_id, created_at DESC);