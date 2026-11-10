FROM postgres:16-alpine

# Các file trong /docker-entrypoint-initdb.d chạy theo thứ tự tên, CHỈ khi volume trống.
# 01: schema cases ban đầu
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql

# 02: bảng patients và liên kết lịch sử
COPY migrations/001_patient_history.sql \
     /docker-entrypoint-initdb.d/02-patient-history.sql

# 03: role quyền tối thiểu cho UI (medtriage_app)
COPY initdb/03-app-role.sh /docker-entrypoint-initdb.d/03-app-role.sh
RUN sed -i 's/\r$//' /docker-entrypoint-initdb.d/03-app-role.sh \
 && chmod 0755 /docker-entrypoint-initdb.d/03-app-role.sh
