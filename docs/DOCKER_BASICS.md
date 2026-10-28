# Docker căn bản — học bằng project MedTriage AI

Tài liệu này dành cho thành viên đã học Machine Learning/Deep Learning nhưng chưa quen phát triển phần mềm và MLOps. Bạn không cần học hết lý thuyết Docker trước. Hãy chạy các bước theo thứ tự, đọc kết quả và thử thay đổi nhỏ.

## 1. Docker dùng để làm gì?

Giả sử code của bạn chạy được trên laptop, nhưng máy thành viên khác lại thiếu phiên bản Python hoặc thiếu thư viện. Docker giúp đóng gói code cùng môi trường cần thiết để mọi người chạy gần như giống nhau.

Trong project này, mỗi phần chạy trong một môi trường riêng:
- UI: trang web để tải ảnh và xem kết quả.
- Vision: API nhận ảnh.
- LLM: API tạo ghi chú SOAP.
- DB: nơi lưu lịch sử ca thử nghiệm.

Docker **không tự tạo ra model ML** và cũng không làm model chính xác hơn. Nó giúp đóng gói, chạy, kết nối, kiểm soát tài nguyên và triển khai các phần mềm của dự án.

## 2. Sáu khái niệm cần nhớ

| Từ | Hiểu đơn giản | Ví dụ trong repo |
|---|---|---|
| **Image** (ảnh Docker) | Bản đóng gói để tạo ra môi trường chạy | Build từ \`services/02-vision/Dockerfile\` |
| **Container** | Một lần chạy của image, giống một tiến trình được cách ly | Container tên \`vision\` |
| **Dockerfile** | Công thức để tạo image | \`services/03-llm/Dockerfile\` |
| **Docker Compose** | File mô tả những container nào cần chạy và kết nối với nhau ra sao | \`docker-compose.yml\` |
| **Port** (cổng) | Địa chỉ để chương trình trên máy bạn truy cập ứng dụng đang chạy | P2 mở cổng máy bạn \`8001\`, bên trong container là \`8000\` |
| **Volume** (vùng lưu dữ liệu) | Nơi lưu file/dữ liệu để chúng không mất chỉ vì container bị tạo lại | \`db_data\`, \`p2_vision_models\` |

Ví dụ dễ nhớ: Dockerfile là công thức nấu ăn, image là món đã chuẩn bị sẵn theo công thức, container là lần bạn bày món đó ra sử dụng. Nếu container bị xoá rồi tạo lại, dữ liệu trong volume có thể vẫn còn.

## 3. Các lệnh Docker thường dùng

Chạy các lệnh từ thư mục gốc repository, trừ khi hướng dẫn ghi khác.

| Lệnh | Nó làm gì? |
|---|---|
| \`docker --version\` | Kiểm tra Docker đã cài chưa |
| \`docker compose version\` | Kiểm tra Docker Compose |
| \`docker compose -f docker-compose.p2.yml up --build\` | Tạo image nếu cần rồi chạy stack P2 |
| \`docker compose -f docker-compose.p2.yml ps\` | Xem container còn chạy không |
| \`docker compose -f docker-compose.p2.yml logs\` | Đọc log khi có lỗi |
| \`docker compose -f docker-compose.p2.yml down\` | Dừng và xoá container của stack P2 |
| \`docker compose exec -T vision sh\` | Mở shell bên trong container đang chạy (chỉ dùng khi cần tìm hiểu thêm) |

**Phân biệt hai lệnh cuối quan trọng:**
- \`down\` thường xoá container và network do Compose tạo, nhưng giữ Named Volume.
- \`down -v\` còn xoá cả Named Volume thuộc stack đó. Có thể mất database hoặc model cache. Đừng dùng lệnh này chỉ để “dọn dẹp” nếu chưa chắc dữ liệu có thể xoá.

## 4. Port: vì sao P2 dùng 8001 thay vì 8000?

Trong Compose độc lập của P2, cấu hình tương tự:

\`\`\`yaml
ports:
  - "127.0.0.1:8001:8000"
\`\`\`

Đọc từ phải sang trái:
- \`8000\`: cổng bên trong container, nơi FastAPI lắng nghe.
- \`8001\`: cổng trên máy của bạn.
- \`127.0.0.1\`: chỉ cho phép truy cập từ chính máy của bạn.

Vì vậy, mở \`http://localhost:8001/docs\` để thử API P2 từ trình duyệt. Bên trong hệ thống tích hợp, UI gọi tên service \`vision\` và cổng container \`8000\`; các container giao tiếp qua mạng Docker, không dùng cổng localhost của máy host.

## 5. Volume và Bind Mount: code khác dữ liệu

### Bind mount — chia sẻ thư mục code
Ví dụ:

\`\`\`yaml
volumes:
  - ./services/02-vision/app:/app/app
\`\`\`

Nghĩa là thư mục code trên laptop được chia sẻ vào container. Khi bạn sửa file Python, container nhìn thấy thay đổi và server có thể tự reload. Cách này tiện khi phát triển.

### Named Volume — giữ dữ liệu
Ví dụ:

\`\`\`yaml
volumes:
  - p2_vision_models:/models
\`\`\`

Named Volume là vùng dữ liệu Docker tự quản lý. Ta dùng nó để lưu weights hoặc cache model. Với PostgreSQL, volume giúp dữ liệu tồn tại qua việc dừng và tạo lại container.

**Mẹo:** code thường nằm trong thư mục repo và được bind mount; dữ liệu cần giữ lâu hơn vòng đời container thường nằm trong Named Volume.

## 6. Tại sao mỗi module có file Compose riêng?

Compose tích hợp \`docker-compose.yml\` chạy cả bốn service. Điều đó tốt khi kiểm thử toàn hệ thống, nhưng chậm và dễ gây rối khi bạn chỉ đang sửa một phần.

Các file riêng giúp:
- P1: chạy giao diện với backend giả lập.
- P2: chạy riêng Vision API.
- P3: chạy riêng LLM API.
- P4: chạy riêng PostgreSQL với dữ liệu thử nghiệm.

Các file này là công cụ **phát triển độc lập**, không thay thế Compose tích hợp khi cần kiểm tra cả luồng. Mọi kết quả mock chỉ để test phần mềm, không phải kết quả y khoa.

## 7. Thực hành theo module

### P1 — UI

Chạy:

\`\`\`bash
docker compose -f docker-compose.p1.yml up --build
\`\`\`

Mở \`http://localhost:8501\`, chọn ảnh tổng hợp \`data/sample_cases/demo_synthetic.png\` và nhập ghi chú thử nghiệm. Bạn sẽ thấy giao diện kết quả, nhưng banner báo **UI ISOLATION MODE** cho biết backend đang được giả lập. Không có model thật chạy và không ghi vào PostgreSQL.

Thử sửa tiêu đề trong \`services/01-ui/app.py\`, lưu file rồi quan sát trình duyệt. Dừng bằng Ctrl+C; nếu cần xoá container, mở terminal thứ hai và chạy \`docker compose -f docker-compose.p1.yml down\`.

### P2 — Vision API

Chạy:

\`\`\`bash
docker compose -f docker-compose.p2.yml up --build
\`\`\`

Mở \`http://localhost:8001/docs\`. Đây là trang Swagger tự tạo từ FastAPI, cho phép thử endpoint thủ công. Mở \`GET /health\` rồi bấm **Try it out → Execute**. Mong đợi phản hồi JSON có \`status: ok\` và \`mode: mock\`.

Sau đó thử \`POST /predict\`: chọn ảnh PNG/JPG và bấm Execute. Mong đợi JSON có \`probabilities\`, \`metadata_removed\`, \`mode\`, \`latency_ms\`. Các số trong mode mock chỉ là kết quả giả lập để kiểm tra định dạng, không phải dự đoán bệnh thật.

### P3 — LLM API

Chạy:

\`\`\`bash
docker compose -f docker-compose.p3.yml up --build
\`\`\`

Mở \`http://localhost:8002/docs\`, thử \`GET /health\`, sau đó \`POST /soap\`. Request cần có \`symptoms\` và \`findings\`. Mong đợi response có \`soap\` với bốn mục \`S\`, \`O\`, \`A\`, \`P\`, cùng \`priority\`, \`mode\`, \`latency_ms\`.

### P4 — Database

Chạy:

\`\`\`bash
docker compose -f docker-compose.p4.yml up --build -d
docker compose -f docker-compose.p4.yml ps
docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c "\\dt"
\`\`\`

Mong đợi thấy bảng \`cases\`. P4 dùng host port \`5433\`, và volume riêng cho database phát triển. Không cần mở trang web trong trình duyệt; PostgreSQL là dịch vụ database, không phải giao diện web.

## 8. Phát triển độc lập và tích hợp khác nhau thế nào?

**Khi đang code:** chỉ chạy Compose riêng của bạn. Bạn không cần chờ model của thành viên khác, cũng không cần chạy toàn hệ thống.

**Khi muốn tích hợp:** sau khi từng module có thể chạy độc lập và có test, thành viên mở Pull Request vào nhánh \`integration\`. Leader review và ghép các phần, rồi mới chạy:

\`\`\`bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
\`\`\`

Mở \`http://localhost:8501\` và kiểm tra luồng UI → Vision → LLM → DB. Khi tích hợp, các module dùng tên service nội bộ như \`vision:8000\`, \`llm:8000\`, \`db:5432\`; đừng thay các địa chỉ này bằng \`localhost\` trong cấu hình container.

Khi toàn bộ luồng và các audit được yêu cầu đã kiểm tra đạt, leader tạo Pull Request từ \`integration\` sang \`main\`.

## 9. Nếu gặp lỗi, kiểm tra theo thứ tự

1. **Docker có đang chạy?** Chạy \`docker version\`. Nếu phần Server báo lỗi, mở Docker Desktop hoặc khởi động Docker Engine.
2. **Container đã chạy chưa?** Dùng file Compose đúng module, thêm \`ps\`. Nếu chưa chạy, đọc log.
3. **Build hay chạy bị lỗi?** Dùng \`docker compose -f <file-compose-cua-ban> logs\` và đọc dòng lỗi đầu tiên.
4. **Port đã bị sử dụng?** Đổi biến port dành cho module trong lệnh/môi trường rồi chạy lại.
5. **Bạn có đang dùng đúng Compose file?** P2 chạy bằng \`docker-compose.p2.yml\`, còn Compose gốc là dành cho cả hệ thống.
6. **Bạn vừa đổi requirements.txt hoặc Dockerfile?** Cần build lại service. Chỉ sửa Python thường có thể được reload tự động ở stack dev.

Đừng vội xoá volume hoặc chuyển sang mode real để né lỗi. Hãy copy thông báo lỗi và gửi nhóm cùng lệnh đã chạy, kết quả mong đợi, và bước bạn đã thử.

## 10. Từ điển từ thường gặp

- **API:** cách một chương trình yêu cầu chương trình khác làm việc, theo địa chỉ và định dạng đã thống nhất.
- **Endpoint:** một đường dẫn của API, ví dụ \`/predict\` hoặc \`/health\`.
- **JSON:** định dạng dữ liệu có cấu trúc dùng để gửi/nhận kết quả.
- **Mock:** kết quả giả được tạo ra để thử phần mềm khi model/dịch vụ thật chưa sẵn sàng.
- **Health check:** kiểm tra nhanh một service còn phản hồi và sẵn sàng không.
- **Log:** bản ghi thông báo, cảnh báo và lỗi khi chương trình chạy.
- **Build:** tạo hoặc cập nhật image từ Dockerfile.
- **MLOps:** các cách tổ chức việc đưa model ML vào ứng dụng có thể chạy, kiểm thử, theo dõi và cập nhật được.

**Nếu chỉ nhớ ba điều:** mỗi module có thể chạy riêng; đọc log khi có lỗi; và chỉ tích hợp sau khi module đã kiểm thử độc lập.
