# Phát triển độc lập và tích hợp các module

File này mô tả **cách nhóm phối hợp và ghép các module**. Nó không thay thế hướng dẫn chạy lần đầu ([GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md)) hay cách kiểm tra phản hồi và log ([TEAM_GUIDE.md](TEAM_GUIDE.md)).

## 1. Vì sao mỗi người chạy riêng?

Project có bốn phần:

| Module | Vai trò | Code chính |
|---|---|---|
| P1 — UI | Giao diện để nhập nội dung thử nghiệm và xem kết quả | services/01-ui/ |
| P2 — Vision | Nhận ảnh và trả điểm cho các nhãn | services/02-vision/ |
| P3 — LLM | Nhận triệu chứng và kết quả Vision, trả nội dung SOAP và mức ưu tiên | services/03-llm/ |
| P4 — Database | Lưu trữ dữ liệu ca thử nghiệm | services/04-db/ |

Trong quá trình phát triển, mỗi thành viên chỉ cần chạy và kiểm tra module được giao. Các file Compose riêng cho phép làm việc ngay cả khi module khác chưa hoàn thiện. P1 và các API hiện có chế độ mock để kiểm tra luồng phần mềm; mock không chứng minh model thật đã hoạt động.

## 2. Thỏa thuận giữa các module

Dù code được phát triển riêng, các module phải thống nhất về dữ liệu đầu vào/đầu ra. [CONTRACT.md](CONTRACT.md) là nguồn chuẩn cho endpoint, tên trường JSON và các giá trị được phép.

Trong Compose tích hợp, các địa chỉ nội bộ chính là:
- UI gọi Vision qua http://vision:8000.
- UI gọi LLM qua http://llm:8000.
- UI kết nối PostgreSQL bằng hostname db và port 5432.

Không thay các địa chỉ này thành localhost trong cấu hình chạy bên trong container. Trong container UI, localhost chỉ trỏ về chính container UI. Khi thử API từ trình duyệt của máy phát triển, dùng địa chỉ và cổng host được ghi trong [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md).

Nếu cần đổi endpoint, tên trường JSON, kiểu dữ liệu hoặc schema database, hãy thông báo cho thành viên liên quan và cập nhật CONTRACT.md cùng code trong cùng một thay đổi. Không tự sửa riêng một phía của giao tiếp.

## 3. Quy trình GitHub của thành viên

1. Tạo hoặc chuyển sang branch cá nhân dựa trên branch integration. Tên branch gợi ý: p1-ui, p2-vision, p3-llm, p4-db.
2. Chỉ sửa các file thuộc phần việc được giao, trừ khi nhóm thống nhất thay đổi dùng chung.
3. Chạy kiểm tra module riêng và ghi lại lệnh cùng kết quả.
4. Xem thay đổi trước khi commit:

~~~bash
git status
git diff
~~~

5. Commit các file liên quan, push branch và mở Pull Request từ branch cá nhân vào integration.
6. Trong mô tả PR, ghi rõ thay đổi, kiểm tra đã chạy và phần còn TODO.

Không commit trực tiếp vào main hoặc integration. Không đưa file .env, API key, mật khẩu thật, dữ liệu bệnh nhân có thể định danh hoặc model weights lớn vào Git.

## 4. Quy trình tích hợp của leader

Leader chỉ bắt đầu khi mỗi module đã có thể chạy độc lập, có kiểm tra cơ bản và các Pull Request cần thiết đã được review.

1. Review từng PR và xác nhận thay đổi phù hợp với CONTRACT.md.
2. Merge từng PR đã duyệt vào integration.
3. Tại thư mục gốc repository, khởi động stack tích hợp:

~~~bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
~~~

4. Mở http://localhost:8501 và kiểm tra luồng thử nghiệm UI → Vision → LLM → PostgreSQL.
5. Nếu có lỗi, dùng log để tìm service gặp vấn đề trước; yêu cầu người phụ trách sửa đúng module thay vì chỉnh đồng thời nhiều phần.
6. Chạy các audit được yêu cầu theo kế hoạch nhóm. Chỉ chạy audit có thể xoá dữ liệu trên stack thử nghiệm và volume có thể bỏ.
7. Khi kiểm tra tích hợp và audit liên quan đạt yêu cầu, mở Pull Request từ integration vào main.

## 5. Dừng và giữ dữ liệu

Lệnh docker compose down thường dừng và xoá container/network của stack, nhưng giữ Named Volume. Lệnh docker compose down -v có thể xoá volume chứa database hoặc model cache. Không thêm -v chỉ để dọn dẹp; trước hết xác nhận dữ liệu có thể bị xoá.

## 6. Tài liệu theo từng nhiệm vụ

- Lần đầu chuẩn bị máy và chạy module: [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md).
- Kiểm tra kết quả và xử lý lỗi: [TEAM_GUIDE.md](TEAM_GUIDE.md).
- Khái niệm/lệnh Docker: [DOCKER_BASICS.md](DOCKER_BASICS.md).
- Endpoint và schema trao đổi dữ liệu: [CONTRACT.md](CONTRACT.md).
- Nhiệm vụ và kế hoạch: [PLAN.md](../PLAN.md).
