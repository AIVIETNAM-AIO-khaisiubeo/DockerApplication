# MedTriage AI

Pipeline 4 container: **UI (Streamlit) -> Vision API -> LLM API -> PostgreSQL**.
Mọi thứ hiện chạy ở chế độ **mock** để kiểm thử tích hợp; từng thành viên triển khai phần được giao trong thư mục module tương ứng.

**Thành viên mới? Đọc [Hướng dẫn làm việc cho nhóm](docs/TEAM_GUIDE.md)** trước khi bắt đầu. Tài liệu bao gồm setup, vị trí code theo module, lệnh chạy/test, Git branch/PR, audit và xử lý lỗi.

**Muốn làm độc lập và chỉ ghép ở cuối?** Xem [Quy trình phát triển module độc lập](docs/MODULE_INDEPENDENCE.md). Mỗi thành viên có Compose riêng để chạy module của mình mà không phải khởi động toàn bộ hệ thống.

- Kế hoạch & phân công: [PLAN.md](PLAN.md)
- Hợp đồng API giữa các module: [docs/CONTRACT.md](docs/CONTRACT.md)

## Chạy thử

Cần Docker Desktop hoặc Docker Engine cùng Docker Compose v2.

Bash / Git Bash / Linux / macOS:
```bash
cp .env.example .env
docker compose up --build -d
```

PowerShell:
```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Mở http://localhost:8501, sau đó chạy smoke test:
```bash
docker compose exec -T ui python smoke_test.py
```

## Phân công module

| Thành viên | Module | Thư mục | Audit chính |
|---|---|---|---|
| P1 | UI | `services/01-ui/` | `audits/audit1_reproducibility.sh` |
| P2 | Vision API | `services/02-vision/` | `audits/audit2_image_cache.sh` |
| P3 | LLM API | `services/03-llm/` | `audits/audit3_fault_tolerance.sh` |
| P4 | Database + hạ tầng | `services/04-db/`, `docker-compose.yml` | `audits/audit4_security_persistence.sh` |

## Chạy riêng từng module

Chạy từ thư mục gốc repository; chi tiết test và tiêu chí hoàn thành nằm trong [docs/MODULE_INDEPENDENCE.md](docs/MODULE_INDEPENDENCE.md).

| Thành viên | Lệnh |
|---|---|
| P1 — UI demo độc lập | `docker compose -f docker-compose.p1.yml up --build` |
| P2 — Vision API | `docker compose -f docker-compose.p2.yml up --build` |
| P3 — LLM API | `docker compose -f docker-compose.p3.yml up --build` |
| P4 — PostgreSQL/schema | `docker compose -f docker-compose.p4.yml up --build -d` |

Các stack độc lập dùng port/volume riêng. UI của P1 dùng backend giả lập, không gọi model/database thật. Chỉ chạy stack tích hợp sau khi các module sẵn sàng: `docker compose up --build -d`.

## Quy tắc làm việc

- Mỗi thành viên làm trên nhánh riêng và gửi Pull Request vào `main`.
- Không commit `.env`, API keys, dữ liệu bệnh nhân hoặc model weights lớn.
- Trao đổi với P4 trước khi sửa `docker-compose.yml`.
- Nếu đổi API, cập nhật `docs/CONTRACT.md` và thông báo các thành viên liên quan.
- Giữ `MODEL_MODE=mock` và `LLM_MODE=mock` cho đến khi mode thật đã được triển khai và kiểm thử.
- Mặc định, `docker compose up` tự gộp `docker-compose.override.yml` nếu file này tồn tại. Xem hướng dẫn nhóm để phân biệt chế độ development và audit.

Tìm TODO được gắn theo người phụ trách:
```bash
grep -rn "TODO(P" services audits
```
Trên PowerShell:
```powershell
Get-ChildItem services,audits -Recurse -File | Select-String "TODO(P[1-4])"
```
