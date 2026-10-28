#!/usr/bin/env bash
# Chạy cả 4 audit với cùng một RUN_ID. Kết quả: audits/results/<RUN_ID>/
export RUN_ID="${RUN_ID:-$(date +%Y%m%d-%H%M%S)}"
cd "$(dirname "$0")"
for a in audit1_reproducibility.sh audit2_image_cache.sh audit3_fault_tolerance.sh audit4_security_persistence.sh; do
  echo "################ $a ################"
  bash "./$a" || echo "!! $a thất bại (xem log), tiếp tục audit kế tiếp"
done
echo "Kết quả: audits/results/$RUN_ID/"
