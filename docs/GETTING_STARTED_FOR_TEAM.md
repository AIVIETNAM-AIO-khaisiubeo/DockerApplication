# Hướng dẫn bắt đầu project DockerApplication

**Dành cho:** thành viên đã học Machine Learning/Deep Learning nhưng chưa có nhiều kinh nghiệm phát triển phần mềm, Docker hoặc MLOps.

Repository: https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication

## 1. Đọc hướng dẫn theo thứ tự

1. [README — tổng quan project](../README.md)
2. [Docker căn bản — học bằng chính project này](DOCKER_BASICS.md)
3. [Hướng dẫn thành viên: chạy, test, xử lý lỗi và Git](TEAM_GUIDE.md)
4. [Làm module độc lập rồi ghép sau](MODULE_INDEPENDENCE.md)
5. [Hợp đồng API — cách các module trao đổi dữ liệu](CONTRACT.md)
6. [Kế hoạch và phân công](../PLAN.md)

Không cần hiểu hết code trước khi bắt đầu. Hãy chạy được module được giao trước, sau đó đọc và sửa phần code liên quan.

## 2. Chuẩn bị máy

Cài Git và Docker Desktop (Windows/macOS), hoặc Docker Engine + Docker Compose v2 (Linux). Mở terminal và kiểm tra:

```bash
git --version
docker --version
docker compose version
```

Nếu Docker báo không kết nối được tới engine/server, hãy mở Docker Desktop hoặc khởi động Docker Engine rồi thử lại.

## 3. Lấy repository và tạo branch cá nhân

Chạy các lệnh sau trong terminal:

```bash
git clone https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication.git
cd DockerApplication
git fetch origin
git switch -c <ten-branch> origin/integration
```

Thay `<ten-branch>` bằng branch của mình:

- P1: `p1-ui`
- P2: `p2-vision`
- P3: `p3-llm`
- P4: `p4-db`

Nếu branch đó đã tồn tại trên máy, dùng `git switch <ten-branch>` thay vì tạo lại. Làm việc trên branch cá nhân, không commit trực tiếp vào `main` hoặc `integration`.

## 4. Chỉ chạy module được giao

Mở terminal **tại thư mục gốc `DockerApplication`**. Chỉ chạy một lệnh tương ứng với module của bạn; chưa cần khởi động toàn bộ project.

| Thành viên | Lệnh chạy | Kết quả để kiểm tra |
|---|---|---|
| **P1 — UI** | `docker compose -f docker-compose.p1.yml up --build` | Mở [http://localhost:8501](http://localhost:8501). UI dùng backend giả lập để thử giao diện, không gọi model/API thật và không ghi PostgreSQL. |
| **P2 — Vision API** | `docker compose -f docker-compose.p2.yml up --build` | Mở [http://localhost:8001/docs](http://localhost:8001/docs). Thử `GET /health` và `POST /predict`. |
| **P3 — LLM API** | `docker compose -f docker-compose.p3.yml up --build` | Mở [http://localhost:8002/docs](http://localhost:8002/docs). Thử `GET /health` và `POST /soap`. |
| **P4 — PostgreSQL** | `docker compose -f docker-compose.p4.yml up --build -d` | Kiểm tra trạng thái bằng `docker compose -f docker-compose.p4.yml ps`; xem bảng theo hướng dẫn trong `DOCKER_BASICS.md`. |

Lần chạy đầu tiên có thể mất thêm thời gian vì Docker cần tải môi trường nền và cài thư viện.

## 5. Code ở đâu?

| Thành viên | File nên mở đầu tiên | Mục tiêu |
|---|---|---|
| P1 | `services/01-ui/app.py` | Hoàn thiện giao diện, hiển thị kết quả, trạng thái và xử lý lỗi. |
| P2 | `services/02-vision/app/main.py` | Xử lý ảnh, endpoint `/predict`, model và kết quả Vision. |
| P3 | `services/03-llm/app/main.py` | Endpoint `/soap`, tạo SOAP, luật mức ưu tiên và xử lý lỗi LLM. |
| P4 | `services/04-db/init.sql` và `docker-compose.yml` | Cấu trúc bảng, dữ liệu lưu bền vững và hạ tầng Docker. Trao đổi với nhóm trước khi đổi Compose dùng chung. |

## 6. Sau mỗi lần sửa code

1. Lưu file và kiểm tra ứng dụng có cập nhật không.
2. Nếu cần, xem container và log bằng lệnh dưới đây (đổi tên file Compose cho đúng module):

```bash
docker compose -f docker-compose.p2.yml ps
docker compose -f docker-compose.p2.yml logs
```

3. Chạy lại bài test của module và ghi kết quả.
4. Nếu thay `requirements.txt` hoặc Dockerfile, build lại bằng lệnh `up --build` tương ứng.

Nếu gặp lỗi, gửi vào group: module đang làm, lệnh đã chạy, thông báo lỗi nguyên văn, log liên quan và kết quả mong đợi.

## 7. Git và Pull Request

Khi đã sửa xong một phần nhỏ:

```bash
git status
git diff
git add <duong-dan-file-cua-minh>
git commit -m "Describe your change"
git push -u origin <ten-branch>
```

Sau đó tạo Pull Request trên GitHub từ branch cá nhân vào **`integration`**. Trong mô tả PR, ghi:
- Đã thay đổi gì.
- Đã chạy lệnh test nào và kết quả ra sao.
- Phần nào còn TODO hoặc cần nhóm hỗ trợ.

Không commit `.env`, API keys, mật khẩu thật, dữ liệu bệnh nhân có thể định danh hoặc model weights lớn. Không tự ý đổi tên endpoint/trường JSON; nếu cần thay đổi, báo nhóm và cập nhật `docs/CONTRACT.md`.

## 8. Chỉ tích hợp ở cuối

Trong lúc phát triển, **mỗi người chỉ chạy module của mình**. Khi các module đã có thể chạy riêng và có kết quả test, leader review PR và ghép trên `integration`.

Khi cần kiểm tra toàn bộ hệ thống, leader chạy:

```bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
```

Mở [http://localhost:8501](http://localhost:8501) và thử luồng UI → Vision → LLM → PostgreSQL. Chỉ sau khi kiểm thử end-to-end và các audit cần thiết đạt yêu cầu, leader tạo PR từ `integration` vào `main`.

## 9. Những điều cần nhớ

- **Image** là gói môi trường; **container** là một lần chạy image.
- **Dockerfile** là công thức tạo image; **Compose** mô tả các container cần chạy và cách chúng kết nối.
- **Port** cho phép máy bạn truy cập ứng dụng; **volume** giúp giữ dữ liệu khi container bị tạo lại.
- **Mock** là dữ liệu giả dùng để kiểm tra phần mềm. Mock không phải kết quả model thật và không được dùng cho quyết định y khoa.
- `docker compose down` thường giữ Named Volume; `docker compose down -v` có thể xoá database/model cache. Không dùng `-v` nếu chưa chắc dữ liệu có thể xoá.
- Không cần tự biết hết DevOps ngay. Trước tiên hãy chạy module, hiểu bài test, đọc log và ghi lại kết quả.
