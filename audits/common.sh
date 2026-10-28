#!/usr/bin/env bash
# Hàm dùng chung cho các bài audit. Windows: chạy trong Git Bash hoặc WSL.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[ -f .env ] || cp .env.example .env
set -a; . ./.env; set +a
RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
OUT="$ROOT/audits/results/$RUN_ID"
mkdir -p "$OUT"
COMPOSE="docker compose -f $ROOT/docker-compose.yml"   # bản production: KHÔNG gộp override (không bind mount)
log()    { echo "[$(date +%T)] $*" | tee -a "$OUT/audit.log"; }
now_ms() { python3 -c 'import time; print(int(time.time()*1000))'; }   # tương thích macOS/Linux/Windows
