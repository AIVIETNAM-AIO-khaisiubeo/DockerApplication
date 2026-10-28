#!/usr/bin/env bash
# AUDIT 3 - Chịu lỗi & Quản lý tài nguyên   (owner: P3)
. "$(dirname "$0")/common.sh"
SVC="${1:-llm}"
log "=== AUDIT 3: fault tolerance ($SVC) ==="
$COMPOSE up -d --build --wait

# --- Kịch bản 1: kill container, đo thời gian tự phục hồi ---
cid=$($COMPOSE ps -q "$SVC")
rc0=$(docker inspect -f '{{.RestartCount}}' "$cid")
T0=$(now_ms); docker kill "$cid" >/dev/null
for _ in $(seq 1 120); do
  rc=$(docker inspect -f '{{.RestartCount}}' "$cid"); st=$(docker inspect -f '{{.State.Health.Status}}' "$cid")
  [ "$rc" -gt "$rc0" ] && [ "$st" = healthy ] && break; sleep 1
done
log "Kịch bản 1: restart_count $rc0 -> $rc, health=$st, thời gian phục hồi = $(( $(now_ms) - T0 )) ms"

# --- Kịch bản 2: ép OOM để kiểm tra giới hạn bộ nhớ (cần ENABLE_DEBUG=1 cho llm) ---
ENABLE_DEBUG=1 $COMPOSE up -d --wait llm
$COMPOSE exec -T ui python -c "import requests; print(requests.post('http://llm:8000/debug/allocate', params={'mb': 900}, timeout=60).status_code)" \
  >"$OUT/a3_oom_call.txt" 2>&1 || log "Gọi allocate lỗi/đứt kết nối (kỳ vọng khi container bị OOM-kill)"
sleep 3
cid=$($COMPOSE ps -q llm)
log "Kịch bản 2: OOMKilled=$(docker inspect -f '{{.State.OOMKilled}}' "$cid") restarts=$(docker inspect -f '{{.RestartCount}}' "$cid")"
docker stats --no-stream --format 'table {{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}' | tee "$OUT/a3_stats.txt"

# TODO(P3): (a) kiểm tra các service khác (ui, vision) vẫn sống trong lúc llm sập; (b) ghi nhận UI báo lỗi thế nào;
#           (c) so sánh có/không có `restart:` và có/không giới hạn tài nguyên; (d) thử CPU limit.
log "AUDIT 3 xong"
