# Hướng dẫn bắt đầu cho thành viên — MedTriage AI

Tài liệu này dành cho thành viên mới với Git, Docker và ứng dụng nhiều service. Mục tiêu là để mỗi người biết mình phụ trách phần nào, viết code ở đâu, chạy thử ra sao và gửi Pull Request như thế nào.

## 1. Kiến trúc tổng quan

Dự án có bốn service:
- **P1 — UI (Streamlit):** giao diện tải ảnh, nhập triệu chứng, hiển thị kết quả và lịch sử ca.
- **P2 — Vision API (FastAPI):** nhận ảnh, tiền xử lý và trả kết quả dự đoán.
- **P3 — LLM API (FastAPI):** nhận triệu chứng/kết quả Vision, tạo SOAP và mức ưu tiên.
- **P4 — Database & hạ tầng:** PostgreSQL, schema, Docker Compose, volume, mạng và cấu hình bảo mật.

Luồng dữ liệu: Người dùng → UI → Vision API → LLM API → PostgreSQL → UI hiển thị kết quả.

**Quan trọng:** chế độ `mock` dùng để kiểm tra tích hợp phần mềm, không phải kết quả y khoa. Không commit dữ liệu bệnh nhân có thể định danh, API key, mật khẩu thật hoặc model weights lớn.

## 2. Cài đặt và khởi chạy lần đầu

Cài Git, Docker Desktop (Windows/macOS) hoặc Docker Engine + Docker Compose v2 (Linux), và VS Code hoặc editor tương đương.

Kiểm tra cài đặt:
```bash
git --version
docker --version
docker compose version
```

Clone repository:
```bash
git clone https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication.git
cd DockerApplication
git switch main
git pull --ff-only
```

Tạo file cấu hình local. PowerShell:
```powershell
Copy-Item .env.example .env
```
Git Bash/Linux/macOS:
```bash
cp .env.example .env
```

Không commit file `.env`. Giữ `MODEL_MODE=mock` và `LLM_MODE=mock` cho đến khi người phụ trách Vision/LLM triển khai và kiểm thử mode thật. Chỉ bật `ENABLE_DEBUG=1` trên stack audit thử nghiệm, không bật khi demo thông thường.

Khởi động:
```bash
docker compose up --build -d
docker compose ps
```

Mở http://localhost:8501 và thử ảnh tổng hợp `data/sample_cases/demo_synthetic.png`. Chạy smoke test:
```bash
docker compose exec -T ui python smoke_test.py
```

Xem log khi có lỗi:
```bash
docker compose logs --tail=100 ui
docker compose logs --tail=100 vision
docker compose logs --tail=100 llm
docker compose logs --tail=100 db
```
Theo dõi log liên tục: `docker compose logs -f ui vision llm db`; nhấn Ctrl+C chỉ dừng theo dõi log.

## 3. Phân công — code ở đâu, test thế nào?

### P1 — UI
**Thư mục:** `services/01-ui/`  
**File bắt đầu:** `services/01-ui/app.py`  
**Client DB:** `services/01-ui/db.py`

Nhiệm vụ: giao diện upload ảnh/nhập triệu chứng; hiển thị xác suất, SOAP, mức ưu tiên và thời gian xử lý; thông báo lỗi khi service không sẵn sàng; xem/ghi lịch sử ca. Giữ nguyên API endpoint và field JSON trong `docs/CONTRACT.md`, trừ khi nhóm đồng ý đổi contract.

Kiểm thử: mở http://localhost:8501, thực hiện một ca với dữ liệu tổng hợp, sau đó chạy `docker compose exec -T ui python smoke_test.py` và xem log UI.

### P2 — Vision API
**Thư mục:** `services/02-vision/`  
**File bắt đầu:** `services/02-vision/app/main.py`

Các endpoint chính là `GET /health` và `POST /predict`. Scaffold có chế độ mock; `load_model()` và `predict_real()` là điểm bắt đầu cho tích hợp model thật. Giữ response tương thích contract, xử lý ảnh lỗi và bảo đảm xác suất thuộc [0, 1]. Weights nên được mount tại `/models`, không commit vào Git.

Kiểm tra health từ container UI:
```bash
docker compose exec -T ui python -c "import requests; r=requests.get('http://vision:8000/health',timeout=10); print(r.status_code,r.text)"
```

Test ảnh mẫu:
```bash
docker compose exec -T ui python -c "import requests; f=open('/data/sample_cases/demo_synthetic.png','rb'); r=requests.post('http://vision:8000/predict',files={'file':('demo_synthetic.png',f,'image/png')},timeout=120); print(r.status_code,r.text)"
```
Vision là service nội bộ Compose; không mặc định truy cập bằng `localhost:8000` từ máy host.

### P3 — LLM API
**Thư mục:** `services/03-llm/`  
**File bắt đầu:** `services/03-llm/app/main.py`

Endpoint chính: `GET /health`, `POST /soap`. Scaffold có mock cho SOAP và priority; `generate_soap_real()` là điểm bắt đầu tích hợp model/API thật. Kiểm tra output có đủ `S`, `O`, `A`, `P`, xử lý timeout và phản hồi không hợp lệ, đồng thời không để API key trong source code.

Kiểm tra health:
```bash
docker compose exec -T ui python -c "import requests; r=requests.get('http://llm:8000/health',timeout=10); print(r.status_code,r.text)"
```

Test SOAP mock:
```bash
docker compose exec -T ui python -c "import requests; p={'symptoms':'test symptoms','findings':{'Pneumonia':0.8,'Pleural Effusion':0.1,'Cardiomegaly':0.1,'Atelectasis':0.1,'Pneumothorax':0.1,'No Finding':0.2}}; r=requests.post('http://llm:8000/soap',json=p,timeout=30); print(r.status_code,r.text)"
```

Các endpoint debug nếu có chỉ được dùng trong audit trên stack có thể khởi động lại.

### P4 — Database & Docker Infrastructure
**File bắt đầu:** `services/04-db/init.sql`, `docker-compose.yml`, `docker-compose.override.yml`

Nhiệm vụ: đảm bảo schema khớp với code DB của UI; kiểm tra healthcheck/restart policy; giữ dữ liệu bằng Named Volume; chỉ publish UI port ra host; DB/Vision/LLM chỉ dùng trong mạng Compose; không nhúng secret vào image. Các thành viên khác cần trao đổi với P4 trước khi sửa Compose dùng chung.

Kiểm tra PostgreSQL với cấu hình mặc định:
```bash
docker compose exec -T db psql -U medtriage -d medtriage -c "SELECT count(*) FROM cases;"
```
Nếu đổi DB/user trong `.env`, điều chỉnh lệnh cho khớp. PostgreSQL init scripts thường chỉ chạy khi data directory được tạo lần đầu.

**Cảnh báo:** `docker compose down` thường giữ Named Volume. `docker compose down -v` xóa Named Volume của stack, có thể xóa database và model cache. Không chạy `-v` nếu cần giữ dữ liệu.

## 4. Hiểu chế độ Docker

Mặc định:
```bash
docker compose up --build -d
```
Docker Compose tự gộp `docker-compose.override.yml` nếu file này tồn tại; override thường dùng bind mount/reload để phát triển nhanh. Sửa Python thường không cần build lại, nhưng thay `requirements.txt` hoặc Dockerfile thì cần build lại service, ví dụ:
```bash
docker compose build vision
docker compose up -d vision
docker compose ps
``

Để chạy chỉ với Compose file gốc, không có override:
```bash
docker compose -f docker-compose.yml up --build -d
``
Ghi rõ chế độ Compose khi chạy audit để kết quả có thể so sánh.

## 5. Git workflow cho beginner

Mỗi thành viên làm trên nhánh riêng. Ví dụ P1:
```bash
git switch main
git pull --ff-only
git switch -c p1-ui
``
Tên nhánh đề xuất: `p1-ui`, `p2-vision`, `p3-llm`, `p4-db`. Nếu nhánh đã tồn tại, dùng `git switch <ten-nhanh>` thay vì tạo lại.

Kiểm tra thay đổi:
```bash
git status
git diff
``

Commit file thuộc phạm vi của mình (ví dụ P1):
```bash
git add services/01-ui/app.py
git commit -m "feat(ui): improve analysis result display"
git push -u origin p1-ui
``

Sau đó tạo Pull Request từ nhánh cá nhân vào `main`. Trong mô tả PR, ghi mục tiêu, file đã sửa, lệnh test và kết quả, giới hạn/TODO còn lại, ảnh chụp màn hình hoặc log nếu hữu ích. Nhờ thành viên khác review; không merge khi smoke test lỗi.

## 6. Checklist trước khi gửi Pull Request

- [ ] Service chạy đúng: kiểm tra `docker compose ps`.
- [ ] Health endpoint của module trả kết quả thành công.
- [ ] Đã test endpoint hoặc giao diện bằng dữ liệu tổng hợp.
- [ ] Đã chạy `docker compose exec -T ui python smoke_test.py`.
- [ ] Đã đọc log và xử lý traceback/lỗi lặp.
- [ ] `git diff` không có secret, dữ liệu nhạy cảm, weights lớn hoặc file tạm.
- [ ] PR mô tả chính xác test đã chạy và TODO còn lại.

## 7. Audit

Các script trong `audits/` là Bash script. Trên Windows, dùng Git Bash hoặc WSL:
```bash
bash audits/audit1_reproducibility.sh
bash audits/audit2_image_cache.sh
bash audits/audit3_fault_tolerance.sh
bash audits/audit4_security_persistence.sh
```
Hoặc `bash audits/run_all.sh`.

Đọc log trong `audits/results/<RUN_ID>/` và xác nhận từng tiêu chí; không coi audit là PASS chỉ vì script đã chạy hết. Audit 1 tập trung reproducibility; Audit 2 image/build cache; Audit 3 fault tolerance; Audit 4 security và persistence. **Kiểm tra nội dung audit4 trước khi chạy:** nếu script gọi `docker compose down -v`, nó sẽ xóa volume của stack. Chỉ dùng dữ liệu tổng hợp và môi trường thử nghiệm.

## 8. Lỗi thường gặp

- **Docker không kết nối được:** mở Docker Desktop/Engine rồi kiểm tra `docker version`.
- **Port 8501 đang bận:** đổi `UI_PORT` trong `.env`, tạo lại container UI và mở port mới.
- **UI mở nhưng phân tích lỗi:** chạy smoke test, xem log UI/Vision/LLM và gọi health từng service.
- **Vision/LLM không mở trên localhost:** đó là service nội bộ; gọi bằng DNS `vision`/`llm` từ mạng Compose.
- **Sửa code nhưng không thấy thay đổi:** xác nhận đang dùng override cho development; build lại nếu thay dependencies/Dockerfile.
- **Thiếu bảng `cases`:** kiểm tra log DB, `.env` và `init.sql`; init script có thể không chạy lại trên volume đã tồn tại.
- **Smoke test lỗi:** tìm lỗi đầu tiên trong log và kiểm tra từng service; không đổi sang mode real để né lỗi.

Nếu bị kẹt, gửi nhóm: module đang làm, lệnh đã chạy, log/lỗi nguyên văn, kết quả mong đợi và những cách đã thử.

## 9. Definition of Done

Một module sẵn sàng tích hợp khi chức năng đã làm hoặc TODO được ghi rõ; API vẫn khớp `docs/CONTRACT.md`; test tái hiện được; pipeline mock vẫn chạy; không commit secret/dữ liệu nhạy cảm; và kết quả audit dùng số đo thật.

## Tài liệu liên quan

- [README](../README.md) — tổng quan dự án.
- [PLAN.md](../PLAN.md) — phân công và mốc tiến độ.
- [API contract](CONTRACT.md) — hợp đồng giữa các module.
- [Audit scripts](../audits/) — các bài kiểm tra hệ thống.
