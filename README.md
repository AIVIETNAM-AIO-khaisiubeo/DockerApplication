# MedTriage AI — Hướng dẫn bắt đầu

Đây là project thực hành Docker với một ứng dụng AI hỗ trợ nghiên cứu ảnh X-quang. Project được chia thành 4 phần để các thành viên có thể làm riêng, sau đó mới kết nối lại.

> **Lưu ý:** Kết quả `mock` là dữ liệu giả dùng để thử chương trình. Không dùng để đưa ra quyết định y khoa. Không tải dữ liệu bệnh nhân có thông tin định danh lên GitHub.

## Bạn nên đọc gì trước?

1. **[Hướng dẫn bắt đầu](docs/TEAM_ONBOARDING.md)**: chuẩn bị máy, clone repo, chạy module được giao, kiểm thử và gửi Pull Request.
2. **[Docker căn bản — thực hành từng bước](docs/DOCKER_BASICS.md)**: Docker image/container là gì, chạy lệnh nào, xem kết quả ở đâu.
3. **[Hướng dẫn thành viên](docs/TEAM_GUIDE.md)**: cách bắt đầu, làm việc theo module, kiểm thử và gửi thay đổi.
4. **[Làm module độc lập rồi ghép sau](docs/MODULE_INDEPENDENCE.md)**: hướng dẫn cho cả nhóm và leader.
5. **[PLAN.md](PLAN.md)**: các công việc và mốc thời gian.
6. **[Hợp đồng API](docs/CONTRACT.md)**: cách các module gửi dữ liệu cho nhau.

## Project được chia thành 4 phần

| Thành viên | Phần phụ trách | Thư mục code chính | Chạy thử riêng |
|---|---|---|---|
| P1 | Giao diện người dùng (UI) | `services/01-ui/` | `docker-compose.p1.yml` |
| P2 | API xử lý ảnh (Vision) | `services/02-vision/` | `docker-compose.p2.yml` |
| P3 | API tạo ghi chú SOAP (LLM) | `services/03-llm/` | `docker-compose.p3.yml` |
| P4 | Cơ sở dữ liệu và cấu hình Docker | `services/04-db/` | `docker-compose.p4.yml` |

## Chạy module của riêng bạn

Trước tiên hãy clone repo và mở terminal **ở thư mục DockerApplication**. Cần cài Git và Docker Desktop (Windows/macOS) hoặc Docker Engine + Compose v2 (Linux).

```bash
git clone https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication.git
cd DockerApplication
```

Chọn đúng một lệnh theo module được giao:

```bash
docker compose -f docker-compose.p1.yml up --build     # P1 — giao diện giả lập
docker compose -f docker-compose.p2.yml up --build     # P2 — Vision API
docker compose -f docker-compose.p3.yml up --build     # P3 — LLM API
docker compose -f docker-compose.p4.yml up --build -d  # P4 — PostgreSQL thử nghiệm
```

Không cần chạy cả bốn lệnh. Chỉ chạy lệnh của module bạn phụ trách. Hướng dẫn chi tiết, địa chỉ để mở trong trình duyệt và cách kiểm tra kết quả có trong [TEAM_ONBOARDING.md](docs/TEAM_ONBOARDING.md) và [DOCKER_BASICS.md](docs/DOCKER_BASICS.md).

## Khi nào chạy toàn bộ ứng dụng?

Chỉ khi các module đã sẵn sàng tích hợp, leader mới chạy Compose chính:

```bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
```

Mở http://localhost:8501 để thử luồng từ giao diện đến các API và database. Lệnh smoke test chỉ dùng khi stack tích hợp đang chạy.

## Cách nhóm làm việc với GitHub

- Mỗi thành viên làm trên branch riêng và chỉ sửa phần được giao.
- Tạo Pull Request vào branch `integration`, không merge trực tiếp vào `main`.
- Leader review, ghép các module và kiểm thử toàn bộ hệ thống; khi ổn mới tạo Pull Request từ `integration` vào `main`.
- Không commit file `.env`, mật khẩu thật, API key, dữ liệu bệnh nhân hoặc model weights lớn.
- Nếu muốn đổi cách các module giao tiếp, báo nhóm và cập nhật `docs/CONTRACT.md` trước khi đổi code.

