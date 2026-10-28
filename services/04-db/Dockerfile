# Module 04 - PostgreSQL 16 (P4).
# TODO(P4): cân nhắc chạy non-root (user: postgres trong compose), healthcheck, tối ưu cấu hình.
FROM postgres:16-alpine
COPY init.sql /docker-entrypoint-initdb.d/01-init.sql
