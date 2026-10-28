#!/usr/bin/env bash
# AUDIT 4 - Bảo mật & Bền vững dữ liệu   (owner: P4)
. "$(dirname "$0")/common.sh"
log "=== AUDIT 4: security & persistence ==="
count() { $COMPOSE exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc 'SELECT count(*) FROM cases' | tr -d '[:space:]'; }
$COMPOSE up -d --build --wait

# --- 1. Bền vững dữ liệu ---
$COMPOSE exec -T ui python smoke_test.py --save | grep SAVED_CASE_ID | tee -a "$OUT/audit.log"
before=$(count);  log "Số ca trước khi down: $before"
$COMPOSE down;    $COMPOSE up -d --wait
after=$(count);   log "Sau down/up (giữ volume): $after  -> $([ "$before" = "$after" ] && echo PASS || echo FAIL)"
$COMPOSE down -v; $COMPOSE up -d --wait             # đối chứng: xóa volume => mất dữ liệu (kỳ vọng 0)
log "Đối chứng sau down -v: $(count) (kỳ vọng 0)"

# --- 2. Cô lập mạng: cổng DB không được publish ra host ---
if (echo > /dev/tcp/127.0.0.1/5432) 2>/dev/null; then log "Cô lập mạng: FAIL (5432 truy cập được từ host)"; else log "Cô lập mạng: PASS (5432 không truy cập được từ host)"; fi

# --- 3. Non-root: mỗi service phải chạy với uid != 0 ---
for s in ui vision llm db; do
  uid=$($COMPOSE exec -T "$s" id -u | tr -d '[:space:]')
  log "Non-root [$s]: uid=$uid -> $([ "$uid" != 0 ] && echo PASS || echo 'FAIL (đang chạy root)')"
done
# TODO(P4): thêm kiểm tra: tài khoản DB quyền tối thiểu, `docker compose config` không lộ secret, internal network.
log "AUDIT 4 xong"
