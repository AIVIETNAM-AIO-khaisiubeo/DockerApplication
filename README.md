# MedTriage AI

MedTriage AI là project học tập để thực hành cách đóng gói và kết nối một ứng dụng AI với Docker. Nhóm phát triển bốn module riêng, kiểm tra từng phần rồi mới ghép chúng thành một hệ thống.

> **Lưu ý:** các chế độ mock tạo dữ liệu giả để kiểm tra phần mềm. Chúng không đại diện cho dự đoán của model y khoa và không được dùng để đưa ra quyết định chẩn đoán hoặc điều trị. Không tải dữ liệu bệnh nhân có thông tin định danh lên GitHub.

## Bắt đầu ở đây

Mở **[GETTING_STARTED_FOR_TEAM.md](docs/GETTING_STARTED_FOR_TEAM.md)** để cài công cụ, clone repository và chạy đúng module được giao. Các tài liệu còn lại được chia theo mục đích để tránh lặp lại cùng một hướng dẫn:

- [DOCKER_BASICS.md](docs/DOCKER_BASICS.md) — khái niệm Docker, port, volume và các lệnh thường dùng.
- [TEAM_GUIDE.md](docs/TEAM_GUIDE.md) — kiểm thử module, kết quả mong đợi và xử lý lỗi.
- [MODULE_INDEPENDENCE.md](docs/MODULE_INDEPENDENCE.md) — branch, Pull Request và quy trình tích hợp.
- [CONTRACT.md](docs/CONTRACT.md) — endpoint và cấu trúc dữ liệu giữa các module.
- [PLAN.md](PLAN.md) — công việc và kế hoạch của project.

## Bốn module

| Module | Vai trò | Thư mục code chính | Compose chạy riêng |
|---|---|---|---|
| P1 — UI | Giao diện để nhập nội dung thử nghiệm và xem kết quả | services/01-ui/ | docker-compose.p1.yml |
| P2 — Vision | API nhận ảnh và trả kết quả theo định dạng đã thống nhất | services/02-vision/ | docker-compose.p2.yml |
| P3 — LLM | API tạo ghi chú SOAP và mức ưu tiên | services/03-llm/ | docker-compose.p3.yml |
| P4 — Database | PostgreSQL và schema lưu dữ liệu thử nghiệm | services/04-db/ | docker-compose.p4.yml |

Các Compose riêng dành cho phát triển và kiểm tra từng module. File docker-compose.yml dùng khi leader tích hợp và chạy toàn bộ stack.

## Quy tắc làm việc của nhóm

- Mỗi thành viên làm trên branch cá nhân và chỉ sửa phần việc được giao.
- Mở Pull Request vào integration; không commit trực tiếp vào main hoặc integration.
- Leader review và ghép code, sau đó kiểm thử toàn bộ luồng. Chỉ đưa thay đổi từ integration sang main khi các kiểm tra cần thiết đạt yêu cầu.
- Không tự ý đổi endpoint, tên trường JSON hoặc schema dùng chung. Trao đổi với nhóm và cập nhật docs/CONTRACT.md trước khi đổi code.
- Không commit file .env, API key, mật khẩu thật, dữ liệu bệnh nhân có thể định danh hoặc model weights lớn.

