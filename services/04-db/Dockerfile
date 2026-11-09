FROM postgres:16-alpine

# Tạo schema cases ban đầu
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql

# Tạo bảng patients và liên kết lịch sử
COPY migrations/001_patient_history.sql \
     /docker-entrypoint-initdb.d/02-patient-history.sql