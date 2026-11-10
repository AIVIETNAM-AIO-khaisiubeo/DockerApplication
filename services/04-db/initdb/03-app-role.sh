#!/bin/sh
# P4 - Tạo role quyền tối thiểu cho UI khi khởi tạo DB LẦN ĐẦU (volume trống).
# Với DB đã có dữ liệu, dùng: bash services/04-db/scripts/provision_app_role.sh
# Mật khẩu truyền qua biến psql (:'app_pass'), không in ra log.
set -eu

APP_USER="${APP_POSTGRES_USER:-medtriage_app}"

if [ -z "${APP_POSTGRES_PASSWORD:-}" ]; then
  echo "[03-app-role] APP_POSTGRES_PASSWORD trống -> bỏ qua tạo role ứng dụng" >&2
else
  psql -X -v ON_ERROR_STOP=1 \
       --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
       -v app_user="$APP_USER" -v app_pass="$APP_POSTGRES_PASSWORD" <<'SQL'
SELECT format(
         'CREATE ROLE %I WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %L',
         :'app_user', :'app_pass')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :'app_user')
\gexec

SELECT format('GRANT CONNECT ON DATABASE %I TO %I', current_database(), :'app_user')
\gexec

GRANT USAGE ON SCHEMA public TO :"app_user";
REVOKE ALL PRIVILEGES ON TABLE public.patients, public.cases FROM :"app_user";
GRANT SELECT, INSERT ON TABLE public.patients, public.cases TO :"app_user";
GRANT UPDATE (medical_history) ON TABLE public.patients TO :"app_user";
GRANT USAGE ON SEQUENCE public.patients_id_seq, public.cases_id_seq TO :"app_user";
SQL
  echo "[03-app-role] Đã tạo/cấp quyền cho role $APP_USER"
fi
