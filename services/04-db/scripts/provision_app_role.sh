#!/usr/bin/env bash
# P4 - Idempotent least-privilege role provisioning for an EXISTING database.
# Only manages the dedicated medtriage_app role and its grants.
# Does not set or print passwords; does not delete user data or volumes.
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd -- "$script_dir/../../.." && pwd)"
cd "$repo_root"

if [[ ! -f docker-compose.yml ]]; then
  printf '[ERROR] docker-compose.yml was not found at %s\n' "$repo_root" >&2
  exit 1
fi

case "${1:---integrated}" in
  --integrated)
    compose=(docker compose -f docker-compose.yml)
    if [[ -f docker-compose.override.yml ]]; then
      compose+=(-f docker-compose.override.yml)
    fi
    ;;
  --p4)
    compose=(docker compose -f docker-compose.p4.yml)
    ;;
  *)
    printf 'Usage: bash services/04-db/scripts/provision_app_role.sh [--integrated|--p4]\n' >&2
    exit 2
    ;;
esac

if [[ -z "$("${compose[@]}" ps -q db)" ]]; then
  printf '[ERROR] PostgreSQL container is not running for the selected Compose stack. Start it first.\n' >&2
  exit 1
fi

printf 'Provisioning least-privilege PostgreSQL app role on the selected DB...\n'
"${compose[@]}" exec -T db sh -c 'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
BEGIN;

-- The role is created once; subsequent runs refresh privileges only.
DO $provision$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'medtriage_app') THEN
        CREATE ROLE medtriage_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
    END IF;
END
$provision$;

ALTER ROLE medtriage_app WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;

-- Use the currently connected database name, including custom P4_DB settings.
DO $grant_connect$
BEGIN
    EXECUTE format('GRANT CONNECT ON DATABASE %I TO medtriage_app', current_database());
END
$grant_connect$;
GRANT USAGE ON SCHEMA public TO medtriage_app;

-- Reset only explicit permissions held by this dedicated app role.
REVOKE ALL PRIVILEGES ON TABLE public.patients, public.cases FROM medtriage_app;
GRANT SELECT, INSERT ON TABLE public.patients, public.cases TO medtriage_app;
GRANT UPDATE (medical_history) ON TABLE public.patients TO medtriage_app;

REVOKE ALL PRIVILEGES ON SEQUENCE public.patients_id_seq, public.cases_id_seq FROM medtriage_app;
GRANT USAGE ON SEQUENCE public.patients_id_seq, public.cases_id_seq TO medtriage_app;

COMMIT;

SELECT rolname, rolsuper, rolcreatedb, rolcreaterole
FROM pg_roles WHERE rolname = 'medtriage_app';
SQL

printf '\n[OK] Role and grants provisioned. Existing role password was NOT changed.\n'
printf 'For a fresh database, set the new role password interactively with:\n'
if [[ "${1:---integrated}" == '--p4' ]]; then
  printf '  docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c '\''\\password medtriage_app'\''\n'
else
  printf '  docker compose exec db psql -U medtriage -d medtriage -c '\''\\password medtriage_app'\''\n'
fi
printf 'Then set APP_POSTGRES_USER and APP_POSTGRES_PASSWORD in your local .env.\n'
printf 'Use your local Compose override to connect the UI as medtriage_app.\n'
