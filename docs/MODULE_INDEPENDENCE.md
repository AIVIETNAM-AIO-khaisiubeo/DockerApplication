# Làm việc độc lập theo module

## Mục tiêu

Mỗi thành viên có thể phát triển và kiểm thử module của mình mà **không phải khởi động hay phụ thuộc code đang thay đổi của ba thành viên khác**. Khi từng module đạt tiêu chí hoàn thành, leader mới ghép chúng bằng Compose tích hợp và chạy kiểm thử end-to-end.

Nguyên tắc:
1. **Một người sở hữu một module** và làm trên branch riêng.
2. **Hợp đồng API trong [CONTRACT.md](CONTRACT.md) là điểm giao tiếp chung**; có thể dùng mock theo đúng contract trong lúc phát triển.
3. Dùng Compose riêng cho từng người. Các stack dev có port và volume riêng, không dùng chung database/model cache với stack tích hợp.
4. Chỉ tích hợp sau khi module đã có test, README/ghi chú cần thiết và Pull Request được review.

## 1. Lệnh khởi động độc lập

Chạy từ thư mục gốc repository. Các file dưới đây là Compose độc lập; chúng **không tự khởi động** các service trong stack tích hợp.

### P1 — UI, không cần Vision/LLM/DB thật

~~~~bash
docker compose -f docker-compose.p1.yml up --build
~~~~

Mở http://localhost:8501. UI chạy với chế độ giả lập backend: các xác suất, SOAP, mức ưu tiên và lịch sử chỉ là dữ liệu synthetic trong phiên Streamlit. Không gọi Vision/LLM thật hoặc PostgreSQL. Mọi thay đổi giao diện có thể xem trực tiếp nhờ bind mount/reload.

Dừng stack bằng Ctrl+C, sau đó nếu cần dọn container:

~~~~bash
docker compose -f docker-compose.p1.yml down
~~~~

### P2 — Vision API độc lập

~~~~bash
docker compose -f docker-compose.p2.yml up --build
~~~~

Mở http://localhost:8001/docs để thử API bằng Swagger hoặc kiểm tra http://localhost:8001/health. Mặc định mode là mock để không cần tải model. P2 có thể phát triển tiền xử lý và kiểm thử endpoint mà không cần UI, LLM hay database.

### P3 — LLM API độc lập

~~~~bash
docker compose -f docker-compose.p3.yml up --build
~~~~

Mở http://localhost:8002/docs để thử POST /soap và http://localhost:8002/health để kiểm tra trạng thái. Mặc định LLM_MODE là mock; API debug bị tắt. Không cần UI, Vision hay database để phát triển logic SOAP/priority.

### P4 — PostgreSQL/schema độc lập

~~~~bash
docker compose -f docker-compose.p4.yml up --build -d
docker compose -f docker-compose.p4.yml ps
docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c "\dt"
~~~~

Database dev được publish **chỉ trên localhost port 5433** và dùng volume riêng tên cho stack P4. Đây là cấu hình phát triển cục bộ, không phải cấu hình triển khai. Khi đổi init.sql, lưu ý PostgreSQL chỉ tự chạy script trong thư mục init khi khởi tạo data directory trống lần đầu.

Dừng stack:

~~~~bash
docker compose -f docker-compose.p4.yml down
~~~~

Lệnh trên giữ volume. Chỉ khi chắc chắn không cần dữ liệu thử nghiệm mới dùng lệnh có -v; lệnh đó xóa volume của stack P4.

## 2. Port và dữ liệu được tách riêng

| Stack dev | Chức năng | Host port mặc định | Phụ thuộc service của người khác? |
|---|---|---:|---|
| P1 | Streamlit với backend giả lập | 8501 | Không |
| P2 | Vision API mock | 8001 | Không |
| P3 | LLM API mock | 8002 | Không |
| P4 | PostgreSQL local | 5433 | Không |

Nếu một port đã được dùng, đổi biến tương ứng:
- P1: P1_UI_PORT
- P2: P2_VISION_PORT
- P3: P3_LLM_PORT
- P4: P4_DB_PORT

Ví dụ PowerShell có thể chạy lệnh sau trước khi khởi động P2:

~~~~powershell
$env:P2_VISION_PORT=8011
docker compose -f docker-compose.p2.yml up --build
~~~~

Trên Bash:

~~~~bash
P2_VISION_PORT=8011 docker compose -f docker-compose.p2.yml up --build
~~~~

Đừng để hai stack cùng chiếm một host port. Các stack P2/P3 dùng Named Volume riêng để weights/cache sau này không bị nhầm với volume của stack tích hợp. P4 dùng một volume dev khác với database tích hợp.

## 3. Điều mỗi thành viên phải kiểm tra

### P1
- UI mở được và các thành phần hiển thị đúng.
- Upload ảnh tổng hợp, nhập triệu chứng, nhấn Phân tích.
- Xác nhận trang lịch sử hiển thị các ca demo trong phiên hiện tại.
- Nêu rõ chế độ isolated UI chỉ kiểm thử bố cục/luồng giao diện, không chứng minh API thật hoạt động.

### P2
- GET /health trả status thành công.
- POST /predict nhận PNG/JPG và trả các trường định nghĩa trong contract.
- Có test cho file không hợp lệ, trường hợp lỗi và định dạng trả về.
- Nếu chọn model thật, ghi rõ model/version, license, kích thước weights, cách tải và thời gian load; không đưa weights lớn vào Git.

### P3
- GET /health trả status thành công.
- POST /soap trả soap có đủ S/O/A/P, priority thuộc EMERGENT/URGENT/ROUTINE, mode và latency_ms.
- Test input thiếu/sai, timeout và lỗi của nhà cung cấp model/API.
- Không commit API keys; giữ endpoint debug tắt ngoài audit.

### P4
- Schema trong init.sql phù hợp với các truy vấn của services/01-ui/db.py.
- Kiểm thử tạo bảng/index và các constraint trong database dev riêng.
- Ghi lại cách tạo mới schema, migration và các quyền cần thiết.
- Không chỉnh schema theo cách làm mất tương thích mà chưa báo nhóm.

## 4. Quy trình chỉ tích hợp ở cuối

### Giai đoạn A — Phát triển độc lập
Mỗi người chỉ chạy Compose riêng của mình, viết code/test trong thư mục được giao và commit trên branch riêng. Không cần khởi chạy toàn bộ ứng dụng mỗi lần sửa code.

### Giai đoạn B — Báo sẵn sàng tích hợp
Mỗi thành viên gửi Pull Request với base branch là `integration` và ghi:
- Phạm vi và file đã thay đổi.
- Lệnh chạy độc lập và kết quả test thực tế.
- Những biến môi trường, weights, API keys hoặc điều kiện ngoài cần thiết (không gửi giá trị secret).
- Những thay đổi API/schema và TODO còn lại.

### Giai đoạn C — Integration owner ghép các module
Sau khi review các module:
1. Merge các PR thành viên vào nhánh `integration` (đã có trong repository), không ghép thủ công bằng cách copy file.
2. Chạy stack tích hợp: docker compose up --build -d.
3. Chạy docker compose ps, kiểm tra health từng service và smoke test: docker compose exec -T ui python smoke_test.py.
4. Thử luồng UI → Vision → LLM → DB; kiểm tra log, lỗi timeout và lịch sử lưu/đọc.
5. Chạy các audit phù hợp trên stack thử nghiệm. Cảnh giác với audit4 vì có thể gọi docker compose down -v và xóa volume.
6. Khi E2E và audit đạt yêu cầu, tạo PR từ nhánh tích hợp vào main.

Nhánh `main` giữ phiên bản ổn định. Thành viên không mở PR module trực tiếp vào `main`; chỉ mở PR từ `integration` sang `main` sau khi stack đầy đủ vượt qua kiểm thử E2E và các audit bắt buộc.

## 5. Những điều không nên làm

- Không gọi API của thành viên khác trong lúc phát triển nếu chưa cần: dùng mock đúng contract.
- Không thay tên endpoint/JSON field một cách âm thầm; cập nhật CONTRACT.md và báo nhóm.
- Không dùng chung volume database/model giữa test độc lập và tích hợp.
- Không coi mock response là kết quả y khoa hoặc kết quả từ model thật.
- Không dùng docker compose down -v để dọn dẹp nếu còn dữ liệu cần giữ.
- Không tuyên bố audit PASS nếu chưa chạy và lưu log kết quả.

