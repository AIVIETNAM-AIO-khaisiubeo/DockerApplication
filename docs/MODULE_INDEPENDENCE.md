# Làm riêng từng module, ghép lại ở cuối

## Ý tưởng chính

Trong nhóm có 4 người, không nên bắt mọi người chạy cả ứng dụng mỗi lần muốn sửa code. Thay vào đó:

1. Mỗi người chạy và kiểm tra phần mình bằng một file Compose riêng.
2. Mỗi người lưu thay đổi trên branch riêng và gửi Pull Request để leader review.
3. Leader ghép code vào branch `integration`.
4. Chỉ khi các phần đã ghép xong mới chạy toàn bộ ứng dụng và kiểm tra luồng từ đầu đến cuối.
5. Khi kiểm tra tích hợp đạt yêu cầu, leader gửi Pull Request từ `integration` vào `main`.

Bạn có thể hình dung đây là làm từng bộ phận riêng rồi mới lắp chúng thành một hệ thống.

## 1. Trước tiên: hiểu điểm giao tiếp chung

Các module không cần dùng chung code bên trong, nhưng phải đồng ý cách gửi và nhận dữ liệu. Quy tắc này nằm trong [CONTRACT.md](CONTRACT.md).

Ví dụ:
- Vision nhận một file ảnh tại đường dẫn API `/predict`, trả về một bộ xác suất theo định dạng JSON.
- LLM nhận triệu chứng và xác suất đó tại `/soap`, trả về ghi chú SOAP và mức ưu tiên.
- UI hiển thị các kết quả này.
- Database lưu lại các trường mà UI gửi vào.

Định dạng request/response là “lời hứa” giữa các module. Bạn có thể thay code bên trong, nhưng đừng tự ý đổi tên endpoint hoặc field JSON nếu chưa báo nhóm.

## 2. Chọn đúng lệnh của bạn

Chạy lệnh từ thư mục gốc `DockerApplication`. Cần có Docker đang hoạt động. Khi chạy lần đầu, Docker có thể mất thêm thời gian tải thư viện và tạo image.

### P1 — Chỉ làm giao diện

```bash
docker compose -f docker-compose.p1.yml up --build
```

Mở http://localhost:8501. Chế độ này mô phỏng kết quả Vision/LLM ngay trong UI, nên P1 có thể thiết kế giao diện và kiểm tra thao tác mà không cần chờ P2, P3 hoặc P4.

**Điều mode này không làm:** không chạy model thật, không gọi API thật và không lưu dữ liệu vào PostgreSQL. Kết quả trên UI là dữ liệu giả chỉ dùng cho kiểm thử giao diện.

### P2 — Chỉ làm Vision API

```bash
docker compose -f docker-compose.p2.yml up --build
```

Mở http://localhost:8001/docs.
1. Chọn `GET /health`, bấm **Try it out → Execute**.
2. Kiểm tra phản hồi có `status` và `mode`.
3. Chọn `POST /predict`, tải ảnh PNG/JPG và thử gửi.
4. Kiểm tra phản hồi có `probabilities`, `metadata_removed`, `mode`, `latency_ms`.

Các số ở chế độ mock chỉ giúp xác nhận API trả đúng định dạng. Chúng không phải kết quả của model thật.

### P3 — Chỉ làm LLM API

```bash
docker compose -f docker-compose.p3.yml up --build
```

Mở http://localhost:8002/docs. Thử `GET /health`, sau đó `POST /soap`. Gửi JSON có hai trường `symptoms` và `findings`. Xác nhận phản hồi có đủ phần `S`, `O`, `A`, `P`, cùng `priority`, `mode` và `latency_ms`.

### P4 — Chỉ làm database

```bash
docker compose -f docker-compose.p4.yml up --build -d
docker compose -f docker-compose.p4.yml ps
docker compose -f docker-compose.p4.yml exec db psql -U medtriage -d medtriage -c "\dt"
```

Lệnh cuối liệt kê các bảng. Mong đợi nhìn thấy `cases`. P4 dùng cổng máy local 5433 và vùng lưu dữ liệu riêng để không làm lẫn dữ liệu thử nghiệm với database tích hợp.

Để dừng P4:

```bash
docker compose -f docker-compose.p4.yml down
```

Lệnh `down` giữ dữ liệu trong Named Volume. Không dùng `down -v` nếu còn cần dữ liệu thử nghiệm.

## 3. Nếu port trên máy bạn đã bị dùng

Các cổng mặc định:
- P1: http://localhost:8501
- P2: http://localhost:8001/docs
- P3: http://localhost:8002/docs
- P4: PostgreSQL ở localhost:5433

Nếu cổng trùng với chương trình khác, hãy đổi biến port cho đúng Compose file:
- P1 dùng `P1_UI_PORT`
- P2 dùng `P2_VISION_PORT`
- P3 dùng `P3_LLM_PORT`
- P4 dùng `P4_DB_PORT`

Ví dụ PowerShell để chạy P2 trên cổng 8011:

```powershell
$env:P2_VISION_PORT=8011
docker compose -f docker-compose.p2.yml up --build
```

## 4. Khi nào nên chạy toàn bộ ứng dụng?

Chỉ chạy khi các module đã có thể chạy riêng và các thành viên đã gửi Pull Request:

```bash
docker compose up --build -d
docker compose ps
docker compose exec -T ui python smoke_test.py
```

Mở http://localhost:8501 để kiểm tra. Nếu thành công, luồng thử nghiệm sẽ đi qua UI → Vision API → LLM API → PostgreSQL. Nếu thất bại, đừng sửa tất cả file cùng lúc; đọc log để xác định service gặp lỗi trước.

Xem log từng service:

```bash
docker compose logs --tail=100 ui
docker compose logs --tail=100 vision
docker compose logs --tail=100 llm
docker compose logs --tail=100 db
```

## 5. Quy trình GitHub cho nhóm

### Thành viên

Tạo branch từ `integration` (ví dụ P2):

```bash
git fetch origin
git switch -c p2-vision origin/integration
```

Nếu branch đó đã tồn tại, chuyển sang branch hiện có bằng `git switch p2-vision`. Sửa code trong thư mục P2, chạy test độc lập và ghi lại kết quả. Sau đó commit/push và tạo Pull Request từ `p2-vision` vào `integration`.

Trong PR nên ghi:
- Bạn đã thay đổi gì.
- Bạn chạy lệnh nào để test và kết quả là gì.
- Phần nào chưa hoàn thành hoặc cần nhóm quyết định.

### Leader / người ghép hệ thống

1. Review các PR; kiểm tra mỗi module có lệnh chạy độc lập và kết quả test.
2. Merge từng PR đã duyệt vào `integration`.
3. Chạy toàn bộ ứng dụng bằng Compose gốc và thực hiện smoke test.
4. Điều tra lỗi tích hợp, yêu cầu người sở hữu module sửa đúng phần đó.
5. Chạy các audit trên stack thử nghiệm và đọc log kết quả.
6. Khi các kiểm tra cần thiết đã đạt, mở PR từ `integration` vào `main`.

Nhánh `main` là phiên bản ổn định đã qua kiểm tra. Đừng merge thẳng code chưa kiểm thử vào `main`.

## 6. Những điều nên nhớ

- **Không cần chạy toàn bộ project khi đang sửa một module.**
- Dùng mock để kiểm tra giao diện/API khi model thật chưa sẵn sàng.
- Mock không chứng minh model thật hoạt động hoặc có độ chính xác tốt.
- Không tự ý đổi API contract; các module khác có thể đang dựa vào nó.
- Không commit file bí mật, dữ liệu bệnh nhân hoặc model weights lớn.
- Đọc [DOCKER_BASICS.md](DOCKER_BASICS.md) nếu chưa rõ image, container, port, volume, bind mount hoặc log.
- Audit 4 có lệnh có thể xóa Named Volume. Chỉ chạy trên stack thử nghiệm và dữ liệu có thể bỏ.
