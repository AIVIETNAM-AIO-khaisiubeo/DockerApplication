#!/usr/bin/env bash
# AUDIT 2 - Tối ưu Image & Cache   (owner: P2, P3 phối hợp cho service llm)
# Yêu cầu: mỗi service có Dockerfile.naive (baseline) và Dockerfile (đã tối ưu).
. "$(dirname "$0")/common.sh"
log "=== AUDIT 2: image & cache ==="
CSV="$OUT/a2_results.csv"
echo "service,variant,size_bytes,cold_build_ms,rebuild_after_code_ms,rebuild_after_deps_ms" > "$CSV"

build_ms() {  # $1=dockerfile $2=tag $3=context [$4=--no-cache]
  local t0; t0=$(now_ms)
  docker build ${4:-} -q -f "$1" -t "$2" "$3" >/dev/null
  echo $(( $(now_ms) - t0 ))
}

for svc in 02-vision 03-llm; do
  for variant in naive opt; do
    if [ "$variant" = naive ]; then df=Dockerfile.naive; else df=Dockerfile; fi
    src="$ROOT/services/$svc"
    [ -f "$src/$df" ] || { log "BỎ QUA $svc/$df (chưa có)"; continue; }
    tag="medtriage-audit/$svc:$variant"
    tmp="$(mktemp -d)"; cp -R "$src/." "$tmp/"          # làm việc trên bản sao, không đụng mã nguồn
    cold=$(build_ms "$tmp/$df" "$tag" "$tmp" --no-cache)
    size=$(docker image inspect -f '{{.Size}}' "$tag")
    echo "# touch" >> "$tmp/app/main.py";           code=$(build_ms "$tmp/$df" "$tag" "$tmp")
    echo "# touch" >> "$tmp/requirements.txt";      deps=$(build_ms "$tmp/$df" "$tag" "$tmp")
    echo "$svc,$variant,$size,$cold,$code,$deps" | tee -a "$CSV"
    rm -rf "$tmp"
  done
done

# TODO(P2) Đo tốc độ nạp model qua Named Volume (cần predict_real thật):
#   a) `docker compose down -v` -> `up -d --wait vision` -> đọc model_load_ms ở GET /health (lần đầu, tải weights)
#   b) `docker compose down`    -> `up -d --wait vision` -> đọc lại model_load_ms (volume còn weights)
#   Lưu vào $OUT/a2_model_load.txt
log "AUDIT 2 xong -> $CSV"
