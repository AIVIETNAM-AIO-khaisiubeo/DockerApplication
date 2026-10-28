#!/usr/bin/env bash
# AUDIT 1 - Tái lập & Môi trường Dev   (owner: P1)
# Chạy trên từng hệ điều hành (Linux/Windows/macOS), rồi so sánh PROB_SHA256 giữa các máy.
. "$(dirname "$0")/common.sh"
log "=== AUDIT 1: reproducibility ==="
{ uname -a; docker version --format 'engine {{.Server.Version}} {{.Server.Os}}/{{.Server.Arch}}'; docker compose version; } | tee "$OUT/a1_env.txt"

T0=$(now_ms)
$COMPOSE up -d --build --wait
log "Thời gian build+khởi động toàn hệ thống: $(( $(now_ms) - T0 )) ms"

$COMPOSE exec -T ui python smoke_test.py | tee "$OUT/a1_smoke.txt"
log "$(grep PROB_SHA256 "$OUT/a1_smoke.txt")  <- phải GIỐNG NHAU trên mọi hệ điều hành"

# TODO(P1) Phần B - tốc độ cập nhật code với Bind Mount (chạy bằng compose DEV có override):
#   1. docker compose up -d   (có override)
#   2. sửa 1 dòng trong services/01-ui/app.py, ghi mốc thời gian
#   3. đo đến khi UI hiển thị thay đổi; so với quy trình "sửa -> docker compose build -> up"
#   Lưu kết quả vào $OUT/a1_bindmount.txt (nhớ ghi hệ điều hành; Windows/macOS thường chậm hơn Linux).
log "AUDIT 1 xong (Phần B bind mount: làm thủ công/TODO)"
