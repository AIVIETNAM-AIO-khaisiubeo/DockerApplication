# Kế hoạch và phân công — MedTriage AI
**Thời gian dự kiến: 28/10–05/11/2026**

Tài liệu này cho biết ai làm phần nào và nhóm cần đạt điều gì vào từng ngày. Không cần chờ các thành viên khác hoàn thành mới bắt đầu code: mỗi người chạy Compose riêng cho module mình, dùng mock khi model thật chưa sẵn sàng. Xem [Hướng dẫn Docker thực hành](docs/DOCKER_BASICS.md) nếu chưa quen với Docker.

## Từ ngữ dùng trong kế hoạch

- **Mock:** kết quả giả để thử code trước khi model/dịch vụ thật sẵn sàng.
- **Audit:** bài kiểm tra có các bước cụ thể nhằm đo một khía cạnh của hệ thống.
- **E2E (end-to-end):** kiểm tra toàn bộ đường đi, từ lúc người dùng gửi yêu cầu đến khi kết quả được lưu và hiển thị.
- **Weights:** file chứa các tham số đã học của model ML/DL.
- **Bind mount:** chia sẻ thư mục code trên laptop vào container để sửa code không cần tạo lại image mỗi lần.
- **Image:** gói môi trường được tạo từ Dockerfile; **container** là một lần chạy image.
- **Non-root:** chạy chương trình bằng tài khoản không có quyền quản trị cao nhất, để giảm rủi ro bảo mật.
- **OOM:** tình huống tiến trình dùng hết giới hạn bộ nhớ và bị hệ thống dừng. Chỉ thử trên stack audit riêng, không dùng dữ liệu cần giữ.

## Mốc chung của cả nhóm

- **28/10:** mỗi thành viên clone repo, chạy được Compose riêng của mình và hiểu cách xem log.
- **30/10:** mỗi module có bản đầu tiên có thể chạy riêng. Nếu chưa kịp tích hợp model thật thì giữ mock và ghi rõ phần còn thiếu.
- **02/11:** leader bắt đầu ghép module trên nhánh `integration` và thử toàn bộ luồng với dữ liệu tổng hợp.
- **03/11:** chạy các bài audit, lưu lại kết quả thật.
- **04/11:** hoàn thiện báo cáo và hướng dẫn; tránh thêm chức năng lớn mới.
- **05/11:** kiểm tra từ một bản clone mới, tập dượt demo và nộp.

Nhánh `main` nên giữ phiên bản ổn định. Mỗi thành viên tạo nhánh riêng từ `integration`, gửi Pull Request vào `integration`; leader chỉ gửi Pull Request từ `integration` sang `main` khi kiểm thử tích hợp đạt yêu cầu.

## P1 — Giao diện người dùng (UI) và Audit 1

**Code chính:** `services/01-ui/app.py`  
**Compose riêng:** `docker-compose.p1.yml`  
**Bài kiểm tra được giao:** `audits/audit1_reproducibility.sh`

- **28/10:** chạy giao diện độc lập bằng Compose P1. Ghi hệ điều hành và phiên bản Docker vào `audits/os_matrix.md` nếu nhóm sử dụng file này.
- **29–30/10:** hoàn thiện màn hình tải ảnh, nhập triệu chứng, biểu đồ kết quả, ghi chú SOAP, nhãn mức ưu tiên, thời gian xử lý và lịch sử. Thông báo rõ ràng khi có dịch vụ không hoạt động.
- **31/10–01/11:** cùng thành viên ở hệ điều hành khác chạy Audit 1. So sánh dòng `PROB_SHA256` và ghi nhận thời gian cập nhật code khi dùng bind mount so với việc build lại. Ghi cả hệ điều hành và cách đo để người khác hiểu kết quả.
- **02/11:** viết hoặc hoàn thiện script chạy 15–20 ca thử nghiệm qua toàn bộ hệ thống và xuất kết quả dạng CSV, nếu tiến độ cho phép.
- **03/11:** chạy Audit 1 và lưu log.
- **04/11:** viết phần giới thiệu, phương pháp và kết quả Audit 1 trong báo cáo.
- **05/11:** hỗ trợ kiểm tra bản báo cáo cuối.

**Điều kiện bàn giao:** UI chạy độc lập ở chế độ giả lập; thao tác chính hoạt động; các thành viên biết kết quả trên UI là dữ liệu mock; test và ảnh chụp màn hình được đính kèm PR.

## P2 — API xử lý ảnh (Vision) và Audit 2

**Code chính:** `services/02-vision/app/main.py`  
**Compose riêng:** `docker-compose.p2.yml`  
**Bài kiểm tra được giao:** `audits/audit2_image_cache.sh`

- **28–29/10:** chạy API độc lập và thử endpoint trước. Nếu chọn model thật, thử model với một vài ảnh trước khi đưa vào Docker. Chọn 15–20 ảnh thử nghiệm công khai hoặc dữ liệu tổng hợp; ghi nguồn và giấy phép. Không đưa ảnh bệnh nhân có thể định danh lên GitHub.
- **29/10:** sao chép Dockerfile ban đầu thành `Dockerfile.naive` để giữ bản dùng làm mốc so sánh trước khi tối ưu.
- **30/10:** triển khai `load_model()` và `predict_real()` cho mode thật nếu kịp. Nếu chưa hoàn tất, giữ mode mock và ghi rõ lý do. Có thể bổ sung DICOM sau khi hỗ trợ PNG/JPG chạy ổn định.
- **31/10–01/11:** cải thiện Dockerfile: cài dependencies trước khi copy code để Docker tái sử dụng các bước đã làm; dùng image gọn hơn nếu phù hợp; chạy bằng user ít quyền hơn. Đo kích thước image và thời gian build theo Audit 2.
- **02/11:** thử model thật qua pipeline tích hợp nếu model đã sẵn sàng; ghi thời gian xử lý và các giới hạn.
- **03/11:** chạy Audit 2 và lưu log.
- **04/11:** viết kết quả Audit 2, giải thích kích thước file model và lợi ích của việc giữ weights/cache trong volume.

**Điều kiện bàn giao:** API độc lập trả đúng các trường trong [CONTRACT.md](docs/CONTRACT.md), test ảnh và lỗi đầu vào, có ghi rõ mode mock/real; nếu model thật chưa hoàn tất, không mô tả mock như kết quả model thật.

## P3 — API LLM tạo ghi chú SOAP và Audit 3

**Code chính:** `services/03-llm/app/main.py`  
**Compose riêng:** `docker-compose.p3.yml`  
**Bài kiểm tra được giao:** `audits/audit3_fault_tolerance.sh`

- **28–29/10:** thống nhất nhóm sẽ gọi dịch vụ LLM bên ngoài hay chạy model local. API bên ngoài thường dễ thử hơn; model local có thể cần nhiều RAM/dung lượng hơn. Ghi rõ lựa chọn trước khi mọi người phụ thuộc vào nó. Tạo bộ 15–20 ca thử nghiệm bằng dữ liệu tổng hợp, cùng nhãn ưu tiên dự kiến.
- **29/10:** sao chép Dockerfile hiện tại thành `Dockerfile.naive` trước khi tối ưu.
- **30/10:** triển khai `generate_soap_real()` nếu kịp; bảo đảm output có đúng bốn trường S/O/A/P, xử lý phản hồi không phải JSON và có cách báo lỗi khi LLM không phản hồi. Viết rõ quy tắc chọn mức ưu tiên để có thể giải thích trong báo cáo.
- **31/10–01/11:** cải thiện Dockerfile và kiểm tra giới hạn CPU/RAM. Hoàn thiện Audit 3: thử một tình huống service bị dừng và kiểm tra hệ thống khởi động lại thế nào; thử giới hạn tài nguyên chỉ trên stack audit.
- **02/11:** thử qua pipeline tích hợp và so mức ưu tiên với nhãn dự kiến của bộ test.
- **03/11:** chạy Audit 3 và lưu log.
- **04/11:** giải thích kết quả audit, cơ chế khởi động lại và các giới hạn còn tồn tại.

**Cảnh báo:** endpoint debug dùng để cố ý làm service lỗi hoặc dùng nhiều RAM. Chỉ bật khi chạy audit trong môi trường thử nghiệm có thể khởi động lại. Không bật trong demo bình thường.

**Điều kiện bàn giao:** API chạy độc lập; phản hồi có đủ S/O/A/P, priority, mode và latency; có test cho input sai hoặc LLM không phản hồi; secrets không nằm trong code hoặc Git.

## P4 — Database, Docker Compose và Audit 4

**Code chính:** `services/04-db/init.sql`, `docker-compose.yml`  
**Compose riêng:** `docker-compose.p4.yml`  
**Bài kiểm tra được giao:** `audits/audit4_security_persistence.sh`

- **28/10:** chạy database độc lập và giúp nhóm sửa lỗi Docker/Compose nếu có. Xác nhận mỗi thành viên hiểu cách dùng file Compose riêng; không bắt cả nhóm chạy mọi service trong lúc làm code.
- **29/10:** kiểm tra bảng trong `init.sql` khớp với các câu lệnh đọc/ghi trong `services/01-ui/db.py`. Tìm hiểu cách tạo user database có ít quyền nhất có thể.
- **30/10:** kiểm tra cấu hình Compose: các service có healthcheck để báo chúng sẵn sàng hay chưa, chính sách khởi động lại, database không mở cổng ra mạng ngoài, và secrets không được đóng gói vào image.
- **31/10–01/11:** hoàn thiện Audit 4 để thử dữ liệu còn tồn tại sau khi dừng/start container, kiểm tra các cổng và user chạy service. Chỉ dùng stack thử nghiệm.
- **02/11:** kiểm tra dữ liệu vẫn được lưu/đọc khi toàn bộ hệ thống đã ghép.
- **03/11:** chạy các audit trên máy thử nghiệm và lưu log tổng hợp.
- **04/11:** viết phần Audit 4, thảo luận các rủi ro và giải thích các cấu hình Docker đã dùng.
- **05/11:** thử quy trình từ clone mới đến chạy ứng dụng.

**Cảnh báo dữ liệu:** `docker compose down -v` có thể xóa Named Volume chứa database hoặc cache model. Trước khi chạy audit nào có lệnh này, hãy đọc script và bảo đảm không có dữ liệu cần giữ.

**Điều kiện bàn giao:** database độc lập khởi động được và có bảng mong đợi; dữ liệu thử nghiệm không mất khi dùng `down` thông thường; các thay đổi Compose được ghi rõ và có sự đồng thuận của nhóm.

## Báo cáo tiến độ hằng ngày

Mỗi người nên cập nhật ngắn gọn:
1. Hôm nay đã hoàn thành gì?
2. Đã chạy lệnh/test nào và kết quả ra sao?
3. Ngày mai sẽ làm gì?
4. Đang kẹt ở đâu và cần ai hỗ trợ?

Nếu mắc một lỗi hơn khoảng một giờ, hãy gửi nguyên văn lỗi, lệnh đã chạy và log liên quan. Đừng chỉ nhắn “Docker bị lỗi”.

