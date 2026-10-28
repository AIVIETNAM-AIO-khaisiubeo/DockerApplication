<<<<<<< HEAD
# MedTriage AI - Prototype khung (scaffold)

Pipeline 4 container: **UI (Streamlit) -> Vision API -> LLM API -> PostgreSQL**.
Mọi thứ đã chạy được ở chế độ **mock**; mỗi người chỉ cần thay phần code trong thư mục module của mình.
Kế hoạch & phân công: xem [`PLAN.md`](PLAN.md). Hợp đồng API: [`docs/CONTRACT.md`](docs/CONTRACT.md).

## Chạy thử (cần Docker Desktop / Docker Engine + Compose v2)
```bash
cp .env.example .env
docker compose up --build        # mở http://localhost:8501
```
Kiểm tra nhanh không cần giao diện:
```bash
docker compose exec -T ui python smoke_test.py
```

## Mỗi người làm ở đâu?
| Người | Module | Thư mục | Audit |
|---|---|---|---|
| P1 | 01 UI | `services/01-ui/` | `audits/audit1_reproducibility.sh` |
| P2 | 02 Vision | `services/02-vision/` | `audits/audit2_image_cache.sh` |
| P3 | 03 LLM | `services/03-llm/` | `audits/audit3_fault_tolerance.sh` |
| P4 | 04 DB + hạ tầng | `services/04-db/`, `docker-compose.yml` | `audits/audit4_security_persistence.sh` |

Tìm `TODO(P1..P4)` trong code để thấy việc của mình: `grep -rn "TODO(P" .`

## Quy tắc làm việc
- **Dev (mặc định)** `docker compose up`: Compose tự gộp `docker-compose.override.yml` (bind mount + reload) - sửa code là thấy ngay.
- **Production/audit** `docker compose -f docker-compose.yml up --build`: không bind mount.
- Mỗi người một nhánh (`p1-ui`, `p2-vision`, `p3-llm`, `p4-db`), merge vào `main` qua Pull Request; **đừng sửa file của người khác**
  (riêng `docker-compose.yml`: báo P4). Không commit `.env`, weights mô hình, dữ liệu thật.
- Đổi API => cập nhật `docs/CONTRACT.md` và báo nhóm.
- Chế độ thật: đặt `MODEL_MODE=real` / `LLM_MODE=real` trong `.env` khi module của bạn sẵn sàng.

## Chạy audit
```bash
bash audits/run_all.sh            # hoặc từng file audits/auditN_*.sh ; kết quả ở audits/results/<thời gian>/
```
Windows: dùng Git Bash hoặc WSL. Cấu trúc compose/script chưa được chạy thử trên Docker thật trước khi giao nhóm;
nếu lỗi ở bước `docker compose up --build` hãy gửi log cho P4 xử lý ngay trong ngày 28/10.
=======
# DockerApplication
>>>>>>> 0bef199964252e67d57773dda1a6dc022f3b7dcb
