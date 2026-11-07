# Branch progress and next steps — MedTriage AI

> **Snapshot:** 07/11/2026 · Repository: [DockerApplication](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication) · Nhánh chuẩn: `main`  
> **Cách đánh giá:** Đã đọc source code, cấu trúc file, tài liệu bàn giao, so sánh commit và trạng thái PR trên GitHub. **Không chạy Docker, model thật hoặc hệ thống E2E trong lần rà soát này.** «Đã triển khai» chỉ xác nhận code đã có; **không đồng nghĩa đã chạy/đạt nghiệm thu**.

Tài liệu này ghi nhận trạng thái **những branch thực sự tồn tại** và các công việc nên ưu tiên để hợp nhất bốn module P1–P4. Các nhiệm vụ gốc được mô tả trong [PLAN.md](../PLAN.md); dữ liệu API phải tuân theo [CONTRACT.md](CONTRACT.md).

## 1. Tổng quan các branch

| Branch | Mức độ so với `main` (07/11) | Code đã có / mục đích | Việc còn thiếu | Đánh giá |
|---|---|---|---|---|
| [`main`](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/tree/main) | Baseline | Scaffold Docker Compose cho P1–P4, API mock P2/P3, UI + DB, audit scripts, tài liệu | Thay mock bằng các module đã kiểm thử; chạy tích hợp và audit có log | Nền tảng, **chưa được xác nhận production-ready** |
| [`integration`](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/tree/integration) | **0 ahead / 42 behind** | Branch tích hợp trước đây; PR [#1](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/pull/1) đã merge vào main | Cập nhật với `main` trước khi tiếp nhận PR mới | **Lỗi thời**, chưa phù hợp làm base nếu chưa đồng bộ |
| [`p1-ui-complete`](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/tree/p1-ui-complete) | **1 ahead / 0 behind** | P1 UI nâng cấp, HTTP client + kiểm tra contract, offline tests, synthetic fixtures, handoff, Audit 1 script | Docker runtime, E2E live với P2/P3/P4, persistence và audit đa hệ điều hành | **Code sẵn sàng review**, chưa nghiệm thu tích hợp |
| [`demo2`](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/tree/demo2) | **Không có common ancestor** với `main` (GitHub compare trả 404) | P2 Vision FastAPI standalone, DenseNet qua `torchxrayvision`, tiền xử lý PNG/JPG, Dockerfile CPU | Xác minh dependencies/model weights, test thực tế, đưa code vào `services/02-vision/` và kiểm tra contract | **Ứng viên P2**, chưa tích hợp |
| [`Demo3`](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/tree/Demo3) | **18 ahead / 0 behind** | P3 FastAPI, phân loại priority, SOAP mock/real gọi endpoint chat-completions tương thích OpenAI, fallback và demo UI | Sửa Dockerfile/layout, đưa P3 vào `services/03-llm/`, test LLM/Compose/Audit 3 | **Ứng viên P3**, chưa tích hợp |

**Lưu ý:** `Demo3` và `demo2` hiện có cấu trúc project ở **root**, khác layout `services/XX-*` của main. **Không merge toàn bộ branch này trực tiếp vào main/integration.** Đặc biệt `Demo3` sẽ làm mất rất nhiều file gốc theo diff GitHub (README, docs, Compose, services, audits); hãy chuyển **các file cần thiết** vào module đích qua PR có review. `demo2` không có lịch sử chung với main, vì vậy cần import/cherry-pick chọn lọc thay vì merge Git history trực tiếp.

## 2. Công việc đã triển khai và TODO theo branch

### `main` — Nền tảng chung

**Đã có trong source**
- `services/01-ui/`: Streamlit UI, DB adapter, smoke test cơ bản.
- `services/02-vision/`: `GET /health`, `POST /predict`, kết quả mock xác định từ pixel ảnh, tái tạo ảnh grayscale bỏ metadata kiểu EXIF đối với ảnh đọc được bằng Pillow.
- `services/03-llm/`: `GET /health`, `POST /soap`, mẫu SOAP mock và quy tắc gán priority; endpoint debug chỉ xuất hiện nếu `ENABLE_DEBUG=1`.
- `services/04-db/init.sql`, `docker-compose.yml`, Compose độc lập `docker-compose.p1.yml` … `docker-compose.p4.yml`, network/volume/healthcheck và scripts `audits/`.
- `docs/CONTRACT.md`, hướng dẫn team và kế hoạch trong `PLAN.md`.

**Chưa hoàn tất / cần xác minh**
- `load_model()` và `predict_real()` của P2 **chưa được triển khai** trên main; chế độ real không chạy như model y khoa hoàn chỉnh.
- `generate_soap_real()` của P3 **chưa được triển khai** trên main.
- DICOM **chưa được hỗ trợ** trong scaffold P2. Cờ `metadata_removed=true` không thay cho kiểm thử loại toàn bộ thông tin định danh ở mọi định dạng.
- Chưa có bằng chứng trong lần rà soát này cho bản chạy E2E live và kết quả thực đo của bốn audit. Không được báo cáo là đã PASS nếu chưa lưu log.

### `p1-ui-complete` — P1 UI + Audit 1

**Đã triển khai trong code**
- Streamlit UI upload PNG/JPG, triệu chứng tổng hợp, bảng điểm, SOAP S/O/A/P, priority, mode mock/real/manual, thời gian xử lý, history và trạng thái health của backend/DB.
- `services/01-ui/client.py` tách HTTP client, kiểm tra JSON contract, giới hạn kích thước file, timeout và báo lỗi.
- `UI_MOCK_BACKENDS=1`: chạy UI độc lập, dùng lịch sử theo session, **không gọi P2/P3/PostgreSQL**. Chế độ nhập score thủ công để thử integration không ghi DB.
- `db.py` và `smoke_test.py` cập nhật, `e2e_cases.py` với 20 tình huống tổng hợp, `tests/test_client.py`, dữ liệu thử trong `data/sample_cases/`.
- Dockerfile P1 chạy non-root, tận dụng dependency-layer cache; Audit 1 script và [P1_HANDOFF.md](P1_HANDOFF.md).

**Bằng chứng hiện có (do báo cáo trong branch ghi nhận, chưa được kiểm tra lại độc lập):**
- [P1_VALIDATION_REPORT.md](https://github.com/AIVIETNAM-AIO-khaisiubeo/DockerApplication/blob/p1-ui-complete/P1_VALIDATION_REPORT.md): **14/14** unit tests và **20/20** synthetic UI-mock cases PASS; `compileall` và `bash -n` PASS.
- Báo cáo **ghi rõ chưa chạy** Docker image build, live Vision, live LLM, ghi PostgreSQL, Audit 1 nhiều OS. Câu «NOT PUSHED» trong báo cáo là ghi chú lúc đóng gói, **không còn mô tả đúng trạng thái branch hiện đã tồn tại trên GitHub**.

**Việc tiếp theo**
1. Đưa PR từ branch này vào `integration` sau khi đồng bộ base; review cả contract và các file Audit 1.
2. Chạy `docker compose -f docker-compose.p1.yml up --build -d`; xác nhận banner `UI ISOLATION MODE`, nhập synthetic image và xem lịch sử.
3. Chạy lại unit tests: `python -m unittest discover -s services/01-ui/tests -v`.
4. Khi P2/P3/P4 sẵn sàng: test `/predict` → `/soap` → database, kiểm tra outage/timeout/JSON sai; chạy 20 cases trong chế độ integrated (không nhầm với 20 mock cases).
5. Chạy Audit 1 trên các hệ điều hành dự kiến; lưu OS, Docker/Compose versions, hash, đo đạc, exit code và log.

**Điều kiện hoàn thành:** UI mock độc lập chạy qua Docker; các API integration đúng contract; DB lưu/đọc thử nghiệm; Audit 1 có số đo và log tái lập. Không dùng 14/14 và 20/20 mock làm bằng chứng hiệu quả y khoa.

### `demo2` — P2 Vision API

**Đã triển khai trong code**
- `app/main.py`: FastAPI `/health` và `/predict`, giới hạn upload, xử lý lỗi input, đo model-load time / latency; response bao gồm `probabilities`, `metadata_removed`, `mode`.
- `app/model.py`: định nghĩa model DenseNet X-quang `densenet121-res224-all` dùng `torchxrayvision`, gọi inference bằng PyTorch, ánh xạ các nhãn sang contract.
- `app/preprocess.py`: decode ảnh, grayscale, kích thước tối thiểu, normalize, center crop và resize 224.
- `app/schemas.py`: Pydantic response schemas; Dockerfile multi-stage, non-root, healthcheck, CPU intention.

**Việc tiếp theo**
1. **Xác minh khả năng build:** kiểm tra version/package resolution trong `requirements.txt`, tên API load model, đường dẫn cache và weights; chạy Docker build thật với CPU.
2. Đưa code vào `services/02-vision/app/`, điều chỉnh Dockerfile, requirements, import và tên thư mục cho `docker-compose.p2.yml`/stack tổng; không xóa scaffold của các phần khác.
3. Giữ `POST /predict` upload field `file` và đủ 6 nhãn, `metadata_removed`, `mode`, `latency_ms` theo `docs/CONTRACT.md`. Xác minh nhãn `Effusion` ↔ `Pleural Effusion` và ý nghĩa/thang giá trị score model; **không mặc nhiên gọi các score là xác suất đã hiệu chuẩn**.
4. Kiểm tra dữ liệu hỏng/rỗng/quá lớn/ảnh quá nhỏ, PNG/JPG có EXIF, cache model khi restart. **DICOM và stripping các tag định danh DICOM còn là TODO** nếu có yêu cầu hỗ trợ.
5. Test API real qua `docker compose -f docker-compose.p2.yml up --build`; có log thời gian tải weights, inference và evidence Audit 2 (image size, cache, build timings).

**Điều kiện hoàn thành:** build + health + inference real hoạt động ổn trên test data được phép sử dụng, API contract đúng, metadata của định dạng hỗ trợ được loại an toàn, có tests/logs và baseline hiệu năng. Chưa có bằng chứng để tuyên bố đã đạt.

### `Demo3` — P3 LLM API / thử nghiệm UI

**Đã triển khai trong code**
- `main.py`: FastAPI `/health`, `/soap`, mock/real modes, fallback về mock nếu lời gọi real lỗi; `/debug/crash`, `/debug/allocate`, `/debug/cpu`, `/debug/hang` khi bật debug.
- `llm_service.py`: quy tắc triage dựa trên symptom keyword (có chuẩn hóa dấu tiếng Việt) + finding threshold, tạo SOAP mock, gọi API `/chat/completions` định dạng OpenAI-compatible với JSON output.
- `models.py`: ràng buộc `symptoms` và `findings` qua Pydantic; `UI.py`: Streamlit prototype kết nối Vision và LLM/nhập score bằng tay.
- Dockerfile multi-stage và non-root **đã được viết**.

**Việc tiếp theo**
1. **Blocker build rõ ràng:** Dockerfile `COPY app ./app` và chạy `uvicorn app.main:app` trong khi tree của branch chỉ có `main.py`, `llm_service.py`, `models.py` ở root, **không có thư mục `app/`**. Sửa layout và Dockerfile trước khi chạy.
2. Chuyển P3 vào `services/03-llm/` theo layout main; chỉ dùng `UI.py` làm reference, **không thay thế P1** vừa phát triển.
3. Thiết lập rõ `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` qua môi trường (không hardcode secrets); kiểm tra việc container truy cập LLM host/Ollama qua `host.docker.internal` trên môi trường của nhóm và giới hạn CPU/RAM phù hợp.
4. Test JSON S/O/A/P đúng, invalid input, timeout, JSON hỏng, lỗi backend, lựa chọn priority; fallback phải **hiển thị mode=mock** (đã có logic, cần test), tránh làm người dùng hiểu sai là LLM real thành công.
5. Xem lại quy tắc gán mức ưu tiên và độ an toàn ở góc độ prototype: các ngưỡng heuristic chưa được hiệu chuẩn/kiểm định lâm sàng. Chạy Audit 3 ở stack thử nghiệm, chỉ bật debug khi cần và lưu log recovery.
6. Kiểm tra API fields theo contract trong `docs/CONTRACT.md`; nếu thay đổi cần PR cập nhật contract đồng thời.

**Điều kiện hoàn thành:** Dockerfile build được, `/health` và `/soap` chạy được trong Compose độc lập/tích hợp, mock/real/fallback có tests, logs Audit 3 và không có secret lộ ra ngoài.

### P4 Database — chưa có branch riêng

Trong snapshot này **không có branch `p4-db`**. P4 hiện có scaffold trong `main`: `services/04-db/init.sql`, `docker-compose.p4.yml`, PostgreSQL và volume `db_data`. **Chưa đủ bằng chứng để kết luận P4 đã nghiệm thu**.

**Cần làm:** đối chiếu `init.sql` với `services/01-ui/db.py` sau khi merge P1; thử ghi/đọc/lưu qua container restart; healthcheck, phân quyền tối thiểu, port DB, secret và chính sách lưu/loại bỏ dữ liệu; thực thi Audit 4 **trên stack/volume có thể xóa** và nộp log. Không dùng dữ liệu bệnh nhân có định danh.

## 3. Thứ tự công việc đề xuất (ưu tiên)

| Thứ tự | Công việc | Phụ trách | Bằng chứng để đóng |
|---|---|---|---|
| **P0 / 1** | Đồng bộ `integration` với `main` (hiện fast-forward theo graph: 0 ahead / 42 behind); giữ quy trình PR/review của nhóm | Leader | Branch base cập nhật; không mất docs/Compose |
| **P0 / 2** | Review PR P1 → `integration`; chạy unit tests và UI-only Docker | P1 + Leader | PR reviewed, test command + output, screenshot |
| **P0 / 3** | Port `demo2` chọn lọc → `services/02-vision/`, sửa build/deps, validate real inference | P2 | Build + `/health`/`/predict`, test input, logs |
| **P0 / 4** | Port `Demo3` chọn lọc → `services/03-llm/`, sửa Dockerfile/layout, test LLM real/fallback | P3 | Build + `/health`/`/soap`, logs, no secrets |
| **P1 / 5** | Xác minh DB/schema, persistence và security | P4 | Test insert/read/restart + Audit 4 |
| **P1 / 6** | Chạy full stack P1–P4, smoke test và 20 synthetic E2E cases; kiểm tra mode từng bước | Leader + team | Kết quả chạy thật, CSV/log, không chỉ mock-only |
| **P1 / 7** | Thực hiện Audit 1–4, ghi số đo thực tế, tái lập thử nghiệm và cập nhật report | Team | Audit results có OS/config/time/log/exit code |
| **P2 / 8** | Quyết định scope DICOM, đánh giá data privacy, đo accuracy/calibration bằng dữ liệu được cấp phép nếu muốn báo cáo hiệu năng model | P2 + Team | Thiết kế được thống nhất và bằng chứng phù hợp |

**Lưu ý phân kỳ:** P0/P1/P2 trong bảng là **mức ưu tiên**, không phải tên module hay tuyên bố tiến độ.

## 4. Quy trình kiểm chứng trước khi merge

1. **Base:** xác nhận `integration` đã cập nhật. Không merge trực tiếp toàn bộ `Demo3`/`demo2` vì layout khác/thiếu common ancestor.
2. **PR:** mỗi PR ghi (a) file đổi, (b) mapping API contract, (c) test đã chạy + log, (d) TODO/blockers, (e) ảnh demo nếu liên quan.
3. **Module test:** build Compose riêng, `GET /health`, endpoint chức năng, lỗi đầu vào, mock vs real.
4. **Integration test:** trên branch `integration` đã ghép P1–P4, tại repo root:

   ```bash
   docker compose -f docker-compose.yml up --build -d
   docker compose -f docker-compose.yml ps
   docker compose -f docker-compose.yml exec -T ui python smoke_test.py
   ```

5. **Bằng chứng tối thiểu:** thời gian và thiết bị test, branch/commit SHA, lệnh đã chạy, exit code, log, ảnh chụp (nếu UI), CSV 20 ca và kết quả audit. Nếu chưa test, ghi **NOT RUN**, không ghi PASS.
6. **Release:** sau review và nghiệm thu E2E/audits, leader mở PR `integration` → `main`.

## 5. Vấn đề cần tránh

- **Mock ≠ model thật:** điểm ảnh, priority và SOAP mock chỉ thử logic phần mềm; không đo chất lượng lâm sàng.
- **Dữ liệu nhạy cảm:** metadata có thể chứa định danh bệnh nhân. P2 cần loại metadata trước khi dùng/persist; **ảnh X-ray và triệu chứng cũng có thể chứa thông tin nhạy cảm**, không mặc nhiên an toàn chỉ vì đã bỏ EXIF/DICOM tags. Chỉ dùng dữ liệu tổng hợp/được cho phép.
- **Cấu hình runtime:** hostname nội bộ là `vision:8000`, `llm:8000` và `db:5432`; không dùng `localhost` để giao tiếp giữa container.
- **Audit gây gián đoạn:** debug crash/memory/CPU/hang chỉ bật trên môi trường có thể khôi phục. `docker compose down -v` sẽ xóa named volumes, chỉ thử trên dữ liệu có thể bỏ.
- **Kế hoạch cũ:** [PLAN.md](../PLAN.md) có mốc 28/10–05/11/2026 đã qua; file này là **snapshot tiến độ và thứ tự ưu tiên tại 07/11/2026**, không phải chứng nhận các milestone cũ đã hoàn tất.

## 6. Cách cập nhật file này

Khi có PR merged hoặc branch mới, thành viên/leader cập nhật bảng ở `1`, chuyển TODO sang «đã kiểm thử» **chỉ khi có log thực tế**, nêu commit/PR và ngày kiểm chứng. Xóa/đổi tên branch chỉ khi nhóm đã thống nhất. Ưu tiên bổ sung link artefact audit và kết quả chạy thay vì phần trăm hoàn thành ước lượng.
