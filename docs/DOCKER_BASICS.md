# Docker căn bản — các khái niệm cần dùng trong project

Tài liệu này giải thích Docker và những lệnh cơ bản. Để chạy module lần đầu, dùng [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md). Để kiểm tra từng API và xử lý lỗi, dùng [TEAM_GUIDE.md](TEAM_GUIDE.md).

## 1. Docker giúp ích gì?

Code có thể chạy trên laptop của bạn nhưng không chạy trên máy bạn khác vì khác phiên bản Python hoặc thiếu thư viện. Docker đóng gói ứng dụng với môi trường cần thiết để các thành viên chạy theo cách nhất quán hơn.

Trong project MedTriage AI:
- UI là trang web để nhập nội dung và xem kết quả.
- Vision là API nhận ảnh.
- LLM là API tạo ghi chú SOAP.
- DB là dịch vụ PostgreSQL lưu dữ liệu thử nghiệm.

Docker không tự tạo model ML và không làm model chính xác hơn. Nó giúp chuẩn bị môi trường, chạy và kết nối các thành phần phần mềm.

## 2. Sáu khái niệm quan trọng

| Khái niệm | Hiểu đơn giản | Ví dụ trong repo |
|---|---|---|
| **Dockerfile** | Công thức chuẩn bị môi trường chạy | services/02-vision/Dockerfile |
| **Image** | Gói được tạo từ Dockerfile, chứa runtime và thư viện cần thiết | Image của Vision API |
| **Container** | Một lần chạy của image | Container thuộc service vision |
| **Compose** | File mô tả các service, cổng, mạng và volume | docker-compose.yml |
| **Port** | Cổng để máy phát triển truy cập ứng dụng trong container | Host port 8001 chuyển tới port 8000 trong Vision |
| **Volume** | Nơi giữ dữ liệu ngoài vòng đời container | Volume của PostgreSQL hoặc model cache |

Có thể hình dung Dockerfile là công thức, image là gói được chuẩn bị từ công thức, còn container là một lần chạy gói đó.

## 3. Dockerfile hoạt động thế nào?

Ví dụ rút gọn:

~~~dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
~~~

- FROM chọn môi trường nền.
- WORKDIR đặt thư mục làm việc trong container.
- COPY đưa file từ project vào image.
- RUN thực hiện lệnh lúc build image, ví dụ cài thư viện.
- CMD là lệnh chính khi container khởi động.

Cài thư viện từ requirements.txt trước khi copy toàn bộ code có thể giúp Docker tái sử dụng build cache khi chỉ có code thay đổi. Cache giúp build nhanh hơn; nó không phải dữ liệu của ứng dụng.

EXPOSE trong Dockerfile chỉ ghi chú cổng mà ứng dụng sử dụng bên trong container. Muốn truy cập ứng dụng từ máy phát triển, cần cấu hình port trong Compose.

## 4. Các lệnh thường dùng

Chạy các lệnh tại thư mục gốc repository, trừ khi có hướng dẫn khác.

| Lệnh | Ý nghĩa |
|---|---|
| docker --version | Kiểm tra Docker CLI. |
| docker compose version | Kiểm tra Docker Compose v2. |
| docker compose -f docker-compose.p2.yml up --build | Build image nếu cần rồi chạy stack P2. |
| docker compose -f docker-compose.p2.yml ps | Xem trạng thái container thuộc stack P2. |
| docker compose -f docker-compose.p2.yml logs --tail=100 | Xem 100 dòng log gần nhất. |
| docker compose -f docker-compose.p2.yml down | Dừng và xoá container/network của stack P2. |
| docker compose exec -T vision sh | Mở shell trong container vision đang chạy; chỉ dùng khi cần kiểm tra sâu hơn. |

Tùy module, thay docker-compose.p2.yml và tên service vision bằng tên phù hợp. Các lệnh chạy và test cụ thể được liệt kê trong [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md) và [TEAM_GUIDE.md](TEAM_GUIDE.md).

## 5. Host port và container port

Một cấu hình Compose có dạng:

~~~yaml
ports:
  - "127.0.0.1:8001:8000"
~~~

Đọc từ phải sang trái:
- 8000 là cổng trong container, nơi API lắng nghe.
- 8001 là cổng trên máy phát triển.
- 127.0.0.1 giới hạn truy cập vào chính máy phát triển.

Vì vậy, khi P2 chạy riêng, bạn mở http://localhost:8001/docs. Trong stack tích hợp, UI gọi Vision qua hostname service nội bộ vision và cổng 8000; hai container giao tiếp qua mạng Docker. Trong container UI, localhost không phải container Vision hoặc máy phát triển.

## 6. Bind mount và Named Volume

### Bind mount — chia sẻ file từ máy vào container

Ví dụ:

~~~yaml
volumes:
  - ./services/02-vision/app:/app/app
~~~

Thư mục code ở máy phát triển được chia sẻ vào container. Khi sửa file, chương trình trong container có thể nhìn thấy thay đổi; việc reload còn phụ thuộc cách server được cấu hình.

### Named Volume — giữ dữ liệu

Ví dụ:

~~~yaml
volumes:
  - p2_vision_models:/models
~~~

Named Volume do Docker quản lý, phù hợp để giữ database hoặc model cache khi container được tạo lại. Code nguồn thường nằm trong repository; dữ liệu cần giữ qua nhiều lần chạy có thể đặt trong Named Volume.

**Cẩn thận:** docker compose down thường giữ Named Volume. docker compose down -v có thể xoá volume của stack đó và làm mất dữ liệu database hoặc cache. Chỉ dùng -v khi chắc chắn dữ liệu có thể bị xoá.

## 7. Vì sao repo có nhiều file Compose?

- docker-compose.p1.yml, docker-compose.p2.yml, docker-compose.p3.yml và docker-compose.p4.yml dùng để phát triển/test riêng từng module.
- docker-compose.yml dùng cho stack tích hợp có UI, Vision, LLM và PostgreSQL.

Compose riêng giúp một thành viên làm việc mà không cần chờ các module còn lại. Nó không thay thế kiểm thử tích hợp. Xem [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md) để hiểu quy trình ghép code.

## 8. Cần đọc gì tiếp?

- Cài công cụ, clone repository, chọn lệnh theo module: [GETTING_STARTED_FOR_TEAM.md](GETTING_STARTED_FOR_TEAM.md).
- Kiểm tra response, trạng thái và log: [TEAM_GUIDE.md](TEAM_GUIDE.md).
- Quy tắc API giữa UI, Vision, LLM và DB: [CONTRACT.md](CONTRACT.md).
