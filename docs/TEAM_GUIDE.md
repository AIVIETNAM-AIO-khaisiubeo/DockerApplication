# Kiểm thử module và xử lý lỗi

Tài liệu này là phần tiếp theo của [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md). Tài liệu bắt đầu hướng dẫn bạn chạy module; file này giải thích **cần kiểm tra điều gì sau khi chạy**, cách đọc log và cách báo lỗi.

Không cần chạy cả bốn module. Chỉ kiểm tra phần mình phụ trách. Nếu chưa biết các khái niệm Docker, xem [DOCKER_BASICS.md](DOCKER_BASICS.md). Nếu đang tìm quy tắc branch và tích hợp, xem [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md).

## 1. Kiểm tra theo module

### P1 — Giao diện người dùng

Sau khi mở UI ở cổng 8501:

1. Xác nhận trang tải thành công và hiển thị cảnh báo UI ISOLATION MODE.
2. Dùng ảnh tổng hợp trong data/sample_cases/demo_synthetic.png và nhập nội dung thử nghiệm.
3. Bấm nút phân tích. Xác nhận UI hiển thị kết quả minh hoạ và lịch sử demo trong phiên hiện tại.
4. Thử tải lại trang hoặc sửa một dòng trong services/01-ui/app.py để kiểm tra vòng lặp phát triển.

Ở chế độ này, UI tự mô phỏng Vision, LLM và lịch sử. Nó **không chạy model thật, không gọi hai API kia và không ghi dữ liệu vào PostgreSQL**. Không diễn giải kết quả demo thành kết quả y khoa.

### P2 — Vision API

Mở trang tài liệu API tại cổng 8001, sau đó:

1. Gọi GET /health. Mong đợi phản hồi thành công với status là ok và mode là mock.
2. Gọi POST /predict bằng ảnh PNG/JPG với tên trường upload là file.
3. Kiểm tra response có các trường probabilities, metadata_removed, mode và latency_ms.
4. Nếu có lỗi, ghi lại HTTP status code cùng nội dung response và log của container.

Các con số trả về trong mode mock chỉ xác nhận API có thể nhận ảnh và trả đúng định dạng. Chúng không phải dự đoán từ model y khoa. Đặc tả đầy đủ nằm trong [CONTRACT.md](CONTRACT.md).

### P3 — LLM API

Mở trang tài liệu API tại cổng 8002, sau đó:

1. Gọi GET /health và xác nhận status là ok.
2. Gọi POST /soap với hai trường symptoms và findings.
3. Kiểm tra response có soap, priority, mode và latency_ms; soap cần có đủ bốn phần S, O, A, P.
4. priority phải thuộc một trong ba giá trị EMERGENT, URGENT hoặc ROUTINE.

Trong mode mock, SOAP là nội dung giả để thử luồng xử lý, không phải hồ sơ thực hoặc lời khuyên y khoa. Xem [CONTRACT.md](CONTRACT.md) để biết định dạng request/response.

### P4 — PostgreSQL

Sau khi stack P4 đã chạy, mở terminal tại thư mục gốc repository và kiểm tra trạng thái:

~~~bash
docker compose -f docker-compose.p4.yml ps
docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c "\dt"
~~~

Lệnh thứ hai yêu cầu PostgreSQL liệt kê bảng; môi trường hiện tại dự kiến có bảng cases. Nếu chưa thấy bảng, xem log database và kiểm tra services/04-db/init.sql. Script khởi tạo trong image PostgreSQL thường chỉ chạy khi thư mục dữ liệu được khởi tạo lần đầu.

## 2. Xem trạng thái và log

Thay tên file Compose bằng file của module bạn đang làm:

~~~bash
docker compose -f <file-compose-cua-module> ps
docker compose -f <file-compose-cua-module> logs --tail=100
~~~

- ps cho biết container đang chạy, đã dừng hay thoát do lỗi.
- logs hiển thị thông báo của ứng dụng. Đọc từ cuối log để xác định lỗi mới nhất; nếu có traceback, hãy giữ phần đầu tiên chỉ ra nguyên nhân.
- Sau khi đổi requirements.txt hoặc Dockerfile, cần build lại module bằng lệnh có --build trong [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md).

## 3. Một số lỗi thường gặp

| Vấn đề | Việc nên kiểm tra đầu tiên |
|---|---|
| Docker không kết nối được | Khởi động Docker Desktop/Engine rồi chạy docker version. |
| Cổng đã được sử dụng | Kiểm tra cổng module; xem hướng dẫn đổi port trong [DOCKER_BASICS.md](DOCKER_BASICS.md). |
| Trang web hoặc API không phản hồi | Xem ps, logs và xác nhận đang mở đúng địa chỉ trong tài liệu bắt đầu. |
| Build lỗi khi cài thư viện | Kiểm tra requirements.txt của module, tên package và log build. |
| Sửa code nhưng không thấy cập nhật | Kiểm tra đúng repository, đúng file Compose và log; xem code có được mount vào container hay không. |
| API trả lỗi 4xx/5xx | Đọc HTTP status và response body, rồi đối chiếu request với [CONTRACT.md](CONTRACT.md). |
| Database không có bảng | Xem log P4, file services/04-db/init.sql và xác định volume có phải dữ liệu đã được khởi tạo từ trước không. |

Không xoá volume hoặc chuyển sang mode real chỉ để né lỗi. Trước khi thay đổi cấu hình dùng chung, trao đổi với nhóm.

## 4. Cách gửi báo lỗi hữu ích

Khi cần nhờ nhóm hỗ trợ, hãy gửi đủ:

- Module đang làm (P1/P2/P3/P4).
- Lệnh chính xác đã chạy và thư mục đang đứng.
- Thông báo lỗi nguyên văn hoặc ảnh chụp màn hình có nội dung lỗi.
- Log liên quan và phản hồi API nếu có.
- Kết quả bạn mong đợi và những gì bạn đã thử.

Không gửi API key, mật khẩu, file .env hoặc dữ liệu bệnh nhân có thể định danh lên group hay GitHub. Quy trình commit và Pull Request được mô tả trong [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md).
