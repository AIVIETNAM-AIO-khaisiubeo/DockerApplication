# Hướng dẫn thành viên — làm từng bước

Tài liệu này dành cho các bạn đã học Machine Learning/Deep Learning nhưng chưa có nhiều kinh nghiệm viết ứng dụng hoặc dùng Docker. Bạn **không cần hiểu hết code của project**. Hãy đọc phần chung, sau đó chỉ làm phần module mình được giao.

Nếu chưa biết Docker image, container, port, volume hoặc log nghĩa là gì, đọc [Docker căn bản — thực hành từng bước](DOCKER_BASICS.md) trước.

## 1. Trước khi bắt đầu

Bạn cần:
- Git để lấy code và gửi thay đổi.
- Docker Desktop trên Windows/macOS, hoặc Docker Engine + Docker Compose v2 trên Linux.
- VS Code hoặc editor tương tự.
- Một terminal: PowerShell là đủ cho các lệnh cơ bản trên Windows; Git Bash/WSL tiện hơn với script audit.

Mở terminal và kiểm tra:

```bash
git --version
docker --version
docker compose version
```

Nếu `docker version` báo lỗi kết nối tới Docker Engine, hãy mở Docker Desktop (hoặc khởi động Docker Engine) rồi thử lại.

## 2. Tải project về máy

Chạy một lần:

```bash
git clone https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication.git
cd DockerApplication
```

**Quan trọng:** các lệnh Docker dưới đây phải được chạy từ thư mục gốc `DockerApplication`, nơi có các file `docker-compose.p1.yml`, `docker-compose.p2.yml`, v.v. Nếu terminal đang ở thư mục khác, dùng lệnh `cd` để đi vào đúng thư mục.

Bạn sẽ thấy các thư mục:
- `services/01-ui/`: giao diện.
- `services/02-vision/`: API nhận và xử lý ảnh.
- `services/03-llm/`: API tạo ghi chú SOAP.
- `services/04-db/`: định nghĩa bảng database.
- `docs/`: hướng dẫn và quy tắc giao tiếp giữa các module.
- `audits/`: script kiểm tra Docker và hệ thống ở giai đoạn tích hợp.

## 3. Chạy riêng module của bạn

Mỗi người có một file Compose riêng. **Chỉ chạy lệnh của module được giao; không cần chạy cả bốn module.** Lần chạy đầu có thể lâu hơn vì Docker cần tải image nền và cài thư viện.

### P1 — Giao diện người dùng

File code chính: `services/01-ui/app.py`

Chạy:

```bash
docker compose -f docker-compose.p1.yml up --build
```

Mở http://localhost:8501. Chọn ảnh tổng hợp `data/sample_cases/demo_synthetic.png`, nhập ghi chú thử nghiệm rồi bấm **Phân tích**.

Bạn sẽ thấy giao diện kết quả và lịch sử demo. Một cảnh báo trên trang cho biết **UI ISOLATION MODE**: Vision, LLM và lịch sử đang được mô phỏng trong UI. Chế độ này chỉ để bạn làm giao diện; nó không chạy model và không lưu vào PostgreSQL.

Thử sửa một dòng giao diện trong `services/01-ui/app.py`, lưu file và xem trình duyệt có cập nhật không. Nếu sửa code mà chưa thấy đổi, xem log và xác nhận container đang chạy bằng file Compose P1.

### P2 — API xử lý ảnh (Vision)

File code chính: `services/02-vision/app/main.py`

Chạy:

```bash
docker compose -f docker-compose.p2.yml up --build
```

Mở http://localhost:8001/docs. Đây là trang thử API được FastAPI tạo tự động.

1. Mở `GET /health`.
2. Bấm **Try it out**, sau đó **Execute**.
3. Mong đợi nhận phản hồi JSON có `status: ok` và `mode: mock`.
4. Thử `POST /predict`, chọn file PNG/JPG và nhấn Execute.
5. Mong đợi nhận JSON gồm `probabilities`, `metadata_removed`, `mode`, `latency_ms`.

Ở chế độ mock, các xác suất chỉ là số giả để kiểm tra định dạng phản hồi. Chúng không phải dự đoán từ model y khoa.

### P3 — API tạo SOAP (LLM)

File code chính: `services/03-llm/app/main.py`

Chạy:

```bash
docker compose -f docker-compose.p3.yml up --build
```

Mở http://localhost:8002/docs. Trước hết thử `GET /health`, rồi mở `POST /soap`.

Request mẫu cho endpoint `POST /soap`:

```json
{
  "symptoms": "sample test symptoms",
  "findings": {
    "Pneumonia": 0.8,
    "Pleural Effusion": 0.1,
    "Cardiomegaly": 0.1,
    "Atelectasis": 0.1,
    "Pneumothorax": 0.1,
    "No Finding": 0.2
  }
}
```

Mong đợi phản hồi có `soap` với đủ bốn phần `S`, `O`, `A`, `P`, cùng `priority`, `mode` và `latency_ms`. Mode mock không phải lời khuyên y tế và không chứng minh model thật đã được kết nối.

### P4 — Database (PostgreSQL)

File schema chính: `services/04-db/init.sql`

Chạy:

```bash
docker compose -f docker-compose.p4.yml up --build -d
docker compose -f docker-compose.p4.yml ps
docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c "\dt"
```

Lệnh cuối yêu cầu PostgreSQL liệt kê các bảng; bạn mong đợi thấy bảng `cases`. PostgreSQL không có trang web như P1/P2/P3, vì vậy bạn kiểm tra nó từ terminal hoặc database client. Stack P4 dùng cổng local `5433` và vùng lưu dữ liệu riêng, tách khỏi database tích hợp.

### Dừng module sau khi thử

Đối với P2, ví dụ:

```bash
docker compose -f docker-compose.p2.yml down
```

Thay tên file bằng file Compose của mình. Với P1/P2/P3 đang chạy ở foreground, Ctrl+C sẽ dừng việc chạy ở terminal; dùng lệnh `down` khi muốn dọn các container do Compose tạo.

**Không thêm `-v` vào lệnh down nếu chưa chắc chắn muốn xóa dữ liệu.** Tùy stack, `down -v` có thể xóa cả database thử nghiệm hoặc model cache.

## 4. Docker đang làm gì? (giải thích ngắn)

- **Dockerfile:** công thức để chuẩn bị môi trường chạy module.
- **Image:** gói được tạo từ Dockerfile, gồm runtime và thư viện cần thiết.
- **Container:** một lần chạy của image.
- **Compose file:** danh sách các container cần chạy, cổng, thư mục chia sẻ và kết nối giữa chúng.
- **Port:** đường để máy bạn truy cập chương trình đang chạy trong container.
- **Bind mount:** chia sẻ thư mục code trên laptop vào container để sửa code thuận tiện.
- **Named Volume:** vùng lưu dữ liệu do Docker quản lý, ví dụ database hoặc model cache.
- **Log:** thông báo chương trình in ra khi chạy; thường là nơi đầu tiên cần xem khi có lỗi.

Các ví dụ cụ thể có trong [DOCKER_BASICS.md](DOCKER_BASICS.md).

## 5. Nếu có lỗi, kiểm tra theo thứ tự

### A. Xem container có chạy không

Thay tên file bằng Compose của module bạn:

```bash
docker compose -f docker-compose.p2.yml ps
```

Nếu container không chạy hoặc thoát ngay, xem log:

```bash
docker compose -f docker-compose.p2.yml logs
```

### B. Các lỗi thường gặp

- **Docker không hoạt động:** mở Docker Desktop/Engine và thử lại `docker version`.
- **Cổng đã được dùng:** P1 dùng 8501, P2 dùng 8001, P3 dùng 8002, P4 dùng 5433. Nếu port bị chiếm, hãy báo nhóm hoặc đổi biến port theo [DOCKER_BASICS.md](DOCKER_BASICS.md).
- **Không mở được trang:** kiểm tra container còn chạy không và đọc log. Đảm bảo bạn mở đúng URL nêu trong phần module.
- **Build lỗi sau khi thêm thư viện:** kiểm tra `requirements.txt` của module và build lại bằng `up --build`.
- **Không thấy thay đổi code:** kiểm tra mình đang chạy đúng file Compose, đúng thư mục và log không báo lỗi.
- **API trả lỗi:** đọc nội dung phản hồi và log; đừng đổi sang mode real chỉ để thử sửa lỗi.
- **Database không có bảng:** xem log của P4 và nội dung `services/04-db/init.sql`. File khởi tạo bảng có thể chỉ được chạy khi database được tạo lần đầu.

Khi nhờ giúp đỡ, gửi đủ: module đang làm, lệnh đã chạy, thông báo lỗi nguyên văn, điều bạn mong đợi và cách đã thử.

## 6. Cách gửi thay đổi qua GitHub

Mỗi người làm trên một branch riêng. Branch `integration` là nơi nhóm ghép các module; `main` dành cho phiên bản đã qua kiểm tra tích hợp.

Lần đầu tạo branch cá nhân (thay `p1-ui` bằng `p2-vision`, `p3-llm` hoặc `p4-db` tùy module):

```bash
git fetch origin
git switch -c p1-ui origin/integration
```

Nếu branch cá nhân đã có rồi, dùng:

```bash
git switch p1-ui
git pull --ff-only
```

Sau khi sửa code, kiểm tra những gì đã đổi:

```bash
git status
git diff
```

Commit những file liên quan đến công việc của bạn. Ví dụ P1:

```bash
git add services/01-ui/app.py
git commit -m "Improve UI analysis result display"
git push -u origin p1-ui
```

Sau đó mở GitHub và tạo **Pull Request (PR)** từ branch cá nhân vào `integration`. PR là đề nghị cho nhóm xem và ghép thay đổi; nó chưa có nghĩa là thay đổi đã được chấp nhận. Trong mô tả PR, ghi:
- Bạn đã làm gì.
- Lệnh test nào đã chạy và kết quả.
- Việc gì còn chưa làm được.

Không commit file `.env`, API key, mật khẩu thật, dữ liệu bệnh nhân hoặc model weights lớn. Nếu cần đổi cách gửi/nhận dữ liệu giữa các module, trước tiên báo nhóm và đọc [CONTRACT.md](CONTRACT.md).

## 7. Khi nào chạy toàn bộ ứng dụng?

Chỉ integration owner/leader cần làm phần này khi các module đã sẵn sàng được ghép:

```bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
```

Mở http://localhost:8501 và thử luồng UI → Vision → LLM → database. Nếu không thành công, đọc log từng service. Hãy dùng [MODULE_INDEPENDENCE.md](MODULE_INDEPENDENCE.md) để theo dõi thứ tự tích hợp.

## 8. Những việc chưa cần làm ngay

Bạn chưa cần:
- chạy cả bốn module mỗi khi sửa một dòng code;
- tải model thật ngay trong lần chạy đầu tiên;
- chỉnh file `docker-compose.yml` dùng chung nếu không phải P4;
- chạy audit toàn hệ thống trong lúc chỉ đang code module;
- tự đổi API contract mà không báo nhóm.

Trước tiên hãy làm cho module riêng chạy được, hiểu output của bài test và ghi lại kết quả. Đó là bước đầu tiên để làm việc với Docker/MLOps.
