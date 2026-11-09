#!/usr/bin/env bash
# MedTriage P4 — integrated-stack read-only security audit.
# No SQL writes, container recreation, Docker volume removal or password output.
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

compose=(docker compose -f docker-compose.yml)
if [[ -f docker-compose.override.yml ]]; then
  compose+=(-f docker-compose.override.yml)
fi
if [[ -f docker-compose.p4.local.yml ]]; then
  compose+=(-f docker-compose.p4.local.yml)
fi

passed=0
warned=0
pass() { printf '[PASS] %s\n' "$1"; passed=$((passed+1)); }
warn() { printf '[WARN] %s\n' "$1"; warned=$((warned+1)); }

printf '=== MedTriage P4 / AUDIT 4 — READ ONLY ===\n'
printf '[INFO] Checking the existing integrated stack; no data or volume will be changed.\n'

# Running services and healthchecks.
for service in db ui vision llm; do
  cid="$("${compose[@]}" ps -q "$service" 2>/dev/null || true)"
  if [[ -z "$cid" ]]; then
    warn "$service: container not found"
    continue
  fi
  health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid" 2>/dev/null || true)"
  if [[ "$health" == healthy ]]; then
    pass "$service: healthy"
  else
    warn "$service: state=${health:-unknown}"
  fi
done

db_cid="$("${compose[@]}" ps -q db 2>/dev/null || true)"
if [[ -n "$db_cid" ]]; then
  # An exposed port is not necessarily published; inspect effective host bindings.
  port_bindings="$(docker inspect --format '{{json (index .NetworkSettings.Ports "5432/tcp")}}' "$db_cid" 2>/dev/null || true)"
  if [[ -z "$port_bindings" || "$port_bindings" == null || "$port_bindings" == '<no value>' ]]; then
    pass 'PostgreSQL 5432 not published to host'
  else
    warn 'PostgreSQL 5432 published to host (inspect docker compose ps)'
  fi

  volume="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Type}}:{{.Name}}{{end}}{{end}}' "$db_cid" 2>/dev/null || true)"
  if [[ "$volume" == volume:* ]]; then
    pass "PostgreSQL uses a named volume ($volume)"
  else
    warn 'PostgreSQL data mount is not a named volume'
  fi
else
  warn 'Cannot check DB port/volume: db container not running'
fi

# The checks below run through the UI's ACTUAL connection, not the DB admin account.
# They use only SELECT and PostgreSQL's privilege introspection functions.
role_result="$("${compose[@]}" exec -T ui python - 2>/dev/null <<'PY' || true
import db

conn = db.get_conn(retries=1)
try:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT current_user,
                   r.rolsuper OR r.rolcreatedb OR r.rolcreaterole,
                   has_table_privilege(current_user, 'public.patients', 'SELECT'),
                   has_table_privilege(current_user, 'public.patients', 'INSERT'),
                   has_table_privilege(current_user, 'public.cases', 'SELECT'),
                   has_table_privilege(current_user, 'public.cases', 'INSERT'),
                   has_column_privilege(current_user, 'public.patients', 'medical_history', 'UPDATE'),
                   has_sequence_privilege(current_user, 'public.patients_id_seq', 'USAGE'),
                   has_sequence_privilege(current_user, 'public.cases_id_seq', 'USAGE'),
                   has_table_privilege(current_user, 'public.patients', 'DELETE'),
                   has_table_privilege(current_user, 'public.cases', 'DELETE'),
                   has_table_privilege(current_user, 'public.patients', 'TRUNCATE'),
                   has_table_privilege(current_user, 'public.cases', 'TRUNCATE'),
                   has_schema_privilege(current_user, 'public', 'CREATE')
            FROM pg_roles AS r WHERE r.rolname = current_user
        """)
        row = cur.fetchone()
        if row is None:
            raise RuntimeError('Could not determine UI database role')
        name, privileged, *permissions = row
        expected_allowed = all(permissions[:7])
        expected_denied = not any(permissions[7:])
        print('ROLE=' + name)
        print('NONADMIN=' + str(not privileged))
        print('ALLOWED=' + str(expected_allowed))
        print('DENIED=' + str(expected_denied))
finally:
    conn.close()
PY
)"

if [[ "$role_result" == *'ROLE=medtriage_app'* ]]; then
  pass 'UI connects to PostgreSQL as medtriage_app'
else
  warn 'UI could not authenticate as medtriage_app (or returned an unexpected role)'
fi
if [[ "$role_result" == *'NONADMIN=True'* ]]; then
  pass 'UI database role has no superuser/createdb/createrole powers'
else
  warn 'UI database role is privileged or privilege introspection failed'
fi
if [[ "$role_result" == *'ALLOWED=True'* ]]; then
  pass 'UI role can SELECT/INSERT needed tables, UPDATE medical_history and use sequences'
else
  warn 'UI role is missing a required least-privilege permission'
fi
if [[ "$role_result" == *'DENIED=True'* ]]; then
  pass 'UI role cannot DELETE/TRUNCATE tables or CREATE objects in public schema'
else
  warn 'UI role has unsafe privileges or permission introspection failed'
fi

# Output row counts, never patient codes, notes, secrets or image data.
if counts="$("${compose[@]}" exec -T db sh -c 'psql -X -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA -F, -c "SELECT (SELECT count(*) FROM public.patients), (SELECT count(*) FROM public.cases);"' 2>/dev/null | tr -d '\r\n ')"; then
  printf '[INFO] Row counts (patients, cases): %s\n' "${counts:-unavailable}"
else
  warn 'Could not query patient/case row counts'
fi

# UID of docker exec is only an indication; server process UID needs separate validation.
for service in ui vision llm db; do
  exec_uid="$("${compose[@]}" exec -T "$service" id -u 2>/dev/null | tr -d '\r\n ' || true)"
  if [[ -n "$exec_uid" ]]; then
    printf '[INFO] Default exec user for %s: UID %s (not necessarily main process UID)\n' "$service" "$exec_uid"
  fi
done

printf '\nAudit summary: %d PASS, %d WARN. Read-only checks completed.\n' "$passed" "$warned"
if (( warned > 0 )); then
  printf 'Warnings need review; no data or volume was modified.\n'
fi
