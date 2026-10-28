# Bắt đầu làm việc với MedTriage AI

Đây là **điểm bắt đầu duy nhất** cho thành viên mới. Project được chia thành bốn module để mỗi người có thể phát triển và kiểm tra riêng trước khi ghép hệ thống.

> **Lưu ý an toàn:** project hiện có các chế độ mock dùng để kiểm tra phần mềm. Kết quả mock là dữ liệu giả, không phải dự đoán y khoa và không được dùng cho quyết định chẩn đoán hoặc điều trị.

## 1. Chọn đúng tài liệu

Mỗi file có một nhiệm vụ riêng; không cần đọc tất cả ngay từ đầu.

| Tài liệu | Dùng khi nào? |
|---|---|
| [README](../README.md) | Muốn xem nhanh project gồm những phần nào. |
| **Tài liệu này** | Cài công cụ, lấy code và chạy module được giao lần đầu. |
| [DOCKER_BASICS.md](DOCKER_BASICS.md) | Chưa rõ image, container, port, volume hoặc các lệnh Docker. |
| [TEAM_GUIDE.md](TEAM_GUIDE.md) | Đã chạy module và cần kiểm tra kết quả, đọc log hoặc xử lý lỗi. |
| [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md) | Cần hiểu quy trình branch, Pull Request và cách leader ghép các module. |
| [CONTRACT.md](CONTRACT.md) | Cần biết chính xác API nhận và trả dữ liệu gì, hoặc muốn đổi cấu trúc dữ liệu. |
| [PLAN.md](../PLAN.md) | Cần xem nhiệm vụ và kế hoạch chung. |

Hướng dẫn được quản lý tập trung trong thư mục docs/; các thư mục trong services/ hiện không có file hướng dẫn Markdown riêng.

## 2. Chuẩn bị máy

Cài Git và Docker:
- Windows/macOS: Docker Desktop.
- Linux: Docker Engine và Docker Compose v2.

Mở terminal và kiểm tra:

~~~bash
git --version
docker --version
docker compose version
~~~

Nếu docker version báo không kết nối được tới Docker Engine, hãy mở Docker Desktop hoặc khởi động Docker Engine trước khi tiếp tục.

## 3. Tải repository và tạo branch

Chạy trong terminal:

~~~bash
git clone https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication.git
cd DockerApplication
git fetch origin
git switch -c <ten-branch> origin/integration
~~~

Thay <ten-branch> theo module được giao:

| Module | Branch gợi ý | Thư mục code chính |
|---|---|---|
| P1 — UI | p1-ui | services/01-ui/ |
| P2 — Vision API | p2-vision | services/02-vision/ |
| P3 — LLM API | p3-llm | services/03-llm/ |
| P4 — Database | p4-db | services/04-db/ |

Nếu branch của bạn đã tồn tại trên máy, chuyển sang branch đó bằng lệnh git switch kèm tên branch tương ứng. Làm việc trên branch cá nhân; không commit trực tiếp vào main hoặc integration.

## 4. Chạy riêng module được giao

**Chạy các lệnh từ thư mục gốc DockerApplication và chỉ chọn một lệnh** theo phần việc của bạn. Chưa cần chạy toàn bộ project.

| Module | Lệnh chạy | Mở hoặc kiểm tra |
|---|---|---|
| **P1 — UI** | docker compose -f docker-compose.p1.yml up --build | Mở [http://localhost:8501](http://localhost:8501). Banner UI ISOLATION MODE xác nhận backend đang được mô phỏng ngay trong UI. |
| **P2 — Vision API** | docker compose -f docker-compose.p2.yml up --build | Mở [http://localhost:8001/docs](http://localhost:8001/docs), thử GET /health và POST /predict. |
| **P3 — LLM API** | docker compose -f docker-compose.p3.yml up --build | Mở [http://localhost:8002/docs](http://localhost:8002/docs), thử GET /health và POST /soap. |
| **P4 — PostgreSQL** | docker compose -f docker-compose.p4.yml up --build -d | Kiểm tra container bằng docker compose -f docker-compose.p4.yml ps; cách liệt kê bảng nằm trong [TEAM_GUIDE.md](TEAM_GUIDE.md). |

Lần build đầu có thể mất thêm thời gian vì Docker cần tải môi trường và cài thư viện. Kết quả mong đợi, ví dụ request và cách kiểm tra từng module được mô tả trong [TEAM_GUIDE.md](TEAM_GUIDE.md).

## 5. Quy tắc quan trọng trước khi sửa code

- Chỉ tập trung vào module được giao; không cần khởi động cả bốn module khi đang phát triển riêng.
- Không tự ý đổi endpoint hoặc tên trường JSON vì các module khác có thể đang dùng chúng. Trao đổi với nhóm và cập nhật [CONTRACT.md](CONTRACT.md) trước khi thay đổi.
- Không commit file .env, API key, mật khẩu thật, dữ liệu bệnh nhân có thể định danh hoặc model weights lớn.
- Không dùng kết quả mock làm kết luận y khoa.
- docker compose down -v có thể xoá Named Volume, bao gồm dữ liệu database hoặc model cache. Không dùng lệnh này nếu chưa chắc dữ liệu có thể xoá.

## 6. Sau khi chạy được module

Hãy làm theo [TEAM_GUIDE.md](TEAM_GUIDE.md) để kiểm tra phản hồi, xem log và xử lý lỗi. Trước khi gửi code, đọc [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md) để làm đúng quy trình Pull Request vào integration.

Chỉ leader/người phụ trách tích hợp mới cần chạy toàn bộ stack và kiểm tra luồng end-to-end; quy trình này được mô tả trong [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md).
