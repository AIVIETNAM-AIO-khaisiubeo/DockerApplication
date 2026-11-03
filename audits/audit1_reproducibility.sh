#!/usr/bin/env bash
# AUDIT 1 – P1 reproducibility + bind-mount development cycle.
# Requires integrated P2/P3/P4 for Part A; no data volume is deleted.
set -euo pipefail
. "$(dirname "$0")/common.sh"

log '=== AUDIT 1: reproducibility and developer workflow ==='
{ uname -a; docker version --format 'engine {{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}'; docker compose version; } \
  | tee "$OUT/a1_env.txt"

T0=$(now_ms)
$COMPOSE up -d --build --wait
log "Full-stack build+startup: $(( $(now_ms) - T0 )) ms"
$COMPOSE exec -T ui python smoke_test.py | tee "$OUT/a1_smoke.txt"
log "$(grep '^PROB_SHA256=' "$OUT/a1_smoke.txt")"

# Two-file development stack explicitly enables bind mounts (not used by Part A).
DEV_COMPOSE="docker compose -f $ROOT/docker-compose.yml -f $ROOT/docker-compose.override.yml"
$DEV_COMPOSE up -d --wait ui

PROBE=$(mktemp "$ROOT/services/01-ui/.p1_mount_probe.XXXXXX")
TMP_DIR=$(mktemp -d)
cleanup() { rm -f "$PROBE"; rm -rf "$TMP_DIR"; }
trap cleanup EXIT
FILENAME=$(basename "$PROBE")
TOKEN="p1_${RUN_ID}_$$"
T0=$(now_ms)
printf '%s' "$TOKEN" > "$PROBE"
SEEN=0
for i in $(seq 1 100); do
  if $DEV_COMPOSE exec -T ui python -c \
    'from pathlib import Path; import sys; p=Path(sys.argv[1]); sys.exit(0 if p.is_file() and p.read_text()==sys.argv[2] else 1)' \
    "/app/$FILENAME" "$TOKEN" >/dev/null 2>&1; then
    SEEN=1
    break
  fi
  sleep 0.1
done
MOUNT_MS=$(( $(now_ms) - T0 ))
if [[ "$SEEN" -eq 0 ]]; then
  log 'Bind mount propagation: FAIL (probe not visible to container)'
  exit 1
fi
log "Bind mount file propagation (host -> container): $MOUNT_MS ms"

# Independent, disposable build context; does not touch the working-tree app.py.
cp -R "$ROOT/services/01-ui/." "$TMP_DIR/"
docker build -q -t medtriage-p1-audit1:bench "$TMP_DIR" >/dev/null
printf '\n# Audit 1 cache rebuild probe\n' >> "$TMP_DIR/app.py"
T1=$(now_ms)
docker build -q -t medtriage-p1-audit1:bench "$TMP_DIR" >/dev/null
REBUILD_MS=$(( $(now_ms) - T1 ))
log "Docker image rebuild after source-code edit (cached dependencies): $REBUILD_MS ms"
{
  echo "run_id=$RUN_ID"
  echo "bind_mount_file_propagation_ms=$MOUNT_MS"
  echo "image_rebuild_after_code_edit_ms=$REBUILD_MS"
  echo 'browser_visible_reload_ms=MANUAL_MEASUREMENT_REQUIRED'
  echo 'NOTE: File propagation is NOT a measurement of Streamlit browser reload.'
  echo 'NOTE: Rebuild benchmark uses a disposable copy of services/01-ui.'
} | tee "$OUT/a1_bindmount.txt"
log 'Audit 1 completed (cross-OS comparison and browser reload still require manual evidence)'
