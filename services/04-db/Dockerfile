# P4 — Database PostgreSQL 16.
# Dùng image PostgreSQL có sẵn, sau đó đưa init.sql vào thư mục đặc biệt.
# Khi PostgreSQL khởi tạo vùng dữ liệu trống lần đầu, nó chạy init.sql để tạo bảng.
# Nếu sửa init.sql sau khi database đã khởi tạo, script thường không tự chạy lại.
FROM postgres:16-alpine
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
