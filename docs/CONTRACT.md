# Quy ước giao tiếp giữa các module (API contract)

File này quy định các module **gửi dữ liệu gì và nhận lại dữ liệu gì**. Hãy coi đây là một thỏa thuận chung của nhóm: bạn có thể thay cách viết code bên trong module, nhưng phần dữ liệu gửi/nhận cần giữ đúng để module khác vẫn hoạt động.

Nếu muốn đổi tên đường dẫn API hoặc tên trường trong JSON, hãy báo nhóm trước và cập nhật file này cùng với thay đổi code. Không tự ý xoá hoặc đổi tên trường đang được dùng.

## Một số từ cần biết

- **API:** cách một chương trình yêu cầu một chương trình khác làm việc.
- **Endpoint:** địa chỉ của một chức năng trong API, ví dụ `/predict`.
- **Request:** dữ liệu được gửi tới API.
- **Response:** dữ liệu API trả về.
- **JSON:** cách viết dữ liệu có tên trường và giá trị; các module dùng định dạng này để trao đổi kết quả.
- **Mode mock:** kết quả giả để thử phần mềm khi model/dịch vụ thật chưa sẵn sàng. Kết quả mock không phải kết quả y khoa.

## Module 02 — Vision API (xử lý ảnh)

Khi chạy **stack tích hợp**, UI gọi Vision theo địa chỉ nội bộ `http://vision:8000`.

### Kiểm tra trạng thái: GET /health

Địa chỉ: `GET /health`

Nếu service đang chạy bình thường, nó trả JSON tương tự:

```json
{
  "status": "ok",
  "mode": "mock",
  "model_load_ms": 0
}
```

### Gửi ảnh để phân tích: POST /predict

Địa chỉ: `POST /predict`

- Request: gửi file ảnh qua `multipart/form-data`, tên trường phải là `file`.
- Định dạng hiện có: PNG/JPG. P2 chỉ bổ sung DICOM khi đã triển khai và kiểm tra phần xử lý đó.

Response có dạng:

```json
{
  "probabilities": {
    "Pneumonia": 0.41,
    "Pleural Effusion": 0.12,
    "Cardiomegaly": 0.05,
    "Atelectasis": 0.20,
    "Pneumothorax": 0.02,
    "No Finding": 0.59
  },
  "metadata_removed": true,
  "mode": "mock",
  "latency_ms": 123
}
```

Ý nghĩa các trường:
- `probabilities`: điểm/xác suất dự đoán cho từng nhãn, theo định dạng mà UI và LLM đang mong đợi.
- `metadata_removed`: cho biết bước loại metadata đã được thực hiện.
- `mode`: `mock` hoặc `real`, dùng để biết kết quả có đến từ phần giả lập hay model thật.
- `latency_ms`: thời gian xử lý, tính bằng mili giây.

Các số ở trên chỉ là ví dụ minh hoạ định dạng. Khi mode là mock, chúng không phải dự đoán từ model y khoa.

## Module 03 — LLM API (tạo ghi chú SOAP)

Trong stack tích hợp, UI gọi LLM theo địa chỉ nội bộ `http://llm:8000`.

### Kiểm tra trạng thái: GET /health

Địa chỉ: `GET /health`

Response thành công có trường `status` là `ok` và trường `mode` cho biết mode hiện tại.

### Tạo ghi chú: POST /soap

Địa chỉ: `POST /soap`

Request cần có hai trường:
- `symptoms`: chuỗi mô tả triệu chứng dùng cho ca thử nghiệm.
- `findings`: object chứa các nhãn và giá trị trả về từ Vision.

Ví dụ request:

```json
{
  "symptoms": "sốt và ho trong ca thử nghiệm",
  "findings": {
    "Pneumonia": 0.41,
    "Pleural Effusion": 0.12,
    "Cardiomegaly": 0.05,
    "Atelectasis": 0.20,
    "Pneumothorax": 0.02,
    "No Finding": 0.59
  }
}
```

Response cần giữ đúng cấu trúc:

```json
{
  "soap": {
    "S": "Subjective",
    "O": "Objective",
    "A": "Assessment",
    "P": "Plan"
  },
  "priority": "URGENT",
  "mode": "mock",
  "latency_ms": 456
}
```

Ý nghĩa:
- `soap`: bốn phần ghi chú S/O/A/P.
- `priority`: chỉ nhận một trong ba giá trị `EMERGENT`, `URGENT`, `ROUTINE`.
- `mode`: `mock` hoặc `real`.
- `latency_ms`: thời gian xử lý tính bằng mili giây.

Ví dụ response chỉ để giải thích định dạng. SOAP do mock tạo ra không phải hồ sơ y tế thực và không dùng để quyết định điều trị.

### Endpoint debug dành riêng cho bài kiểm tra

- `POST /debug/crash`
- `POST /debug/allocate?mb=N`

Các đường dẫn này chỉ được bật khi `ENABLE_DEBUG=1`, nhằm giả lập lỗi hoặc tiêu thụ bộ nhớ khi làm Audit 3. Chỉ dùng trong môi trường test có thể khởi động lại; không bật khi demo bình thường.

## Module 04 — Database (nơi lưu dữ liệu)

Database là PostgreSQL. Trong stack tích hợp, chỉ các container thuộc mạng nội bộ mới kết nối được tới `db:5432`; database không publish cổng ra máy bên ngoài.

Bảng `cases` được định nghĩa trong [`services/04-db/init.sql`](../services/04-db/init.sql). UI ghi và đọc dữ liệu qua [`services/01-ui/db.py`](../services/01-ui/db.py).

Bảng lưu thông tin ca thử nghiệm, kết quả và thời gian xử lý. **Không lưu tên, mã bệnh nhân hoặc thông tin có thể định danh cá nhân.** Nếu đổi tên cột hoặc kiểu dữ liệu, P4 cần trao đổi với P1 vì code UI đang dùng schema này.

## Mạng và địa chỉ: tại sao không dùng localhost?

Khi các container chạy cùng Compose tích hợp:
- UI gọi Vision bằng `http://vision:8000`.
- UI gọi LLM bằng `http://llm:8000`.
- UI kết nối PostgreSQL bằng hostname `db`, port `5432`.

Tên `vision`, `llm`, `db` là tên service được Compose dùng làm địa chỉ trong mạng Docker. Trong container UI, `localhost` có nghĩa là chính container UI, không phải container Vision hay máy của bạn.

Khi chạy các module độc lập, ta map cổng của container ra máy local để thử:
- P2: mở `http://localhost:8001/docs`.
- P3: mở `http://localhost:8002/docs`.
- P4: PostgreSQL được map vào `localhost:5433`.

## Named Volume (nơi giữ dữ liệu)

Stack tích hợp định nghĩa ba vùng lưu do Docker quản lý:
- `vision_models`: weights/cache của Vision, được gắn vào `/models`.
- `llm_models`: weights/cache của LLM, được gắn vào `/models`.
- `db_data`: dữ liệu PostgreSQL.

Không commit model weights lớn vào Git. Lệnh `docker compose down` thường giữ các volume này; `docker compose down -v` có thể xoá chúng. Chỉ dùng lệnh có `-v` khi chắc chắn dữ liệu có thể bị xoá.
