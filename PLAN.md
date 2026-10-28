# Kế hoạch 28/10 -> 05/11/2026 (9 ngày) - MedTriage AI

**Giả định (sửa nếu sai):** 05/11 là hạn nộp/demo bản đầu: (1) ứng dụng chạy 1 lệnh, (2) log đủ 4 audit, (3) bản nháp báo cáo LaTeX.
Mỗi người ~2-3 giờ/ngày. **Code freeze: tối 04/11.** 05/11 chỉ kiểm tra và sửa lỗi nhỏ.

## Nguyên tắc để nhóm không bị lạc hướng
1. **Mock trước, thật sau**: pipeline đã chạy được từ ngày 1; thay dần từng module sang bản thật mà không làm hỏng người khác.
2. **Hợp đồng API đóng băng** (`docs/CONTRACT.md`): làm việc song song không cần chờ nhau.
3. **Audit là điểm chấm**: Dockerfile phải có bản `Dockerfile.naive` (baseline) và bản tối ưu để đo so sánh.
4. **Họp nhanh 15 phút mỗi tối**: hôm nay xong gì / mai làm gì / đang kẹt gì. Kẹt quá 1 giờ thì hỏi ngay.

## Các mốc
| Ngày | Mốc | Tiêu chí đạt |
|---|---|---|
| T4 28/10 | **M0 Kick-off** | Cả 4 người chạy được scaffold (`docker compose up`, mở được UI, smoke test OK); nhận việc |
| T6 30/10 | **M1 Module v1** | Mỗi module có bản "thật" đầu tiên (hoặc mock cải tiến) chạy trong container riêng; có `Dockerfile.naive` |
| T2 02/11 | **M2 Tích hợp E2E** | Chạy end-to-end với 15-20 ca; ghi nhận xác suất, SOAP, nhãn ưu tiên, độ trễ |
| T3 03/11 | **M3 Audit** | Chạy `run_all.sh`, có log cả 4 audit |
| T4 04/11 | **M4 Báo cáo + freeze** | Bản nháp LaTeX đủ các mục; README hoàn chỉnh; đóng băng code tối nay |
| T5 05/11 | **M5 Giao nộp** | Clone repo sạch -> chạy 1 lệnh OK; tập dượt demo; nộp |

## Phân công theo người

### P1 - Module 01 (Giao diện) + Audit 1 (Tái lập & Dev) + ghép báo cáo
- **28/10 (T4):** chạy scaffold, ghi OS vào `audits/os_matrix.md`; cùng nhóm chốt cách dùng Git.
- **29-30/10:** hoàn thiện UI: upload ảnh + nhập triệu chứng, biểu đồ xác suất, SOAP, nhãn ưu tiên có màu, hiển thị độ trễ, trang Lịch sử; báo lỗi thân thiện khi một service sập. *(M1)*
- **31/10 - 01/11:** Audit 1: nhờ các bạn dùng OS khác nhau chạy `audit1_reproducibility.sh`, so `PROB_SHA256`; đo Bind Mount (Phần B trong script) so với build lại.
- **02/11:** viết `scripts/run_dataset.py` chạy toàn bộ 15-20 ca qua pipeline, xuất CSV kết quả. *(M2)*
- **03/11:** chạy Audit 1 chính thức, lưu log.
- **04/11:** viết mục 1 (Đặt vấn đề), mục 2 (Phương pháp) và mục Audit 1 trong `report/`; ghép báo cáo.
- **05/11:** biên dịch PDF cuối, kiểm tra hình/bảng.

### P2 - Module 02 (Vision) + Audit 2 (Image & Cache) + chọn ảnh dữ liệu
- **28-29/10:** thử mô hình thị giác ngoài Docker trên 1-2 ảnh (gợi ý: `torchxrayvision`); chọn **15-20 ảnh** từ bộ dữ liệu công khai (ghi nguồn + giấy phép) vào `data/sample_cases/`.
- **29/10:** `cp Dockerfile Dockerfile.naive` (giữ baseline).
- **30/10:** `predict_real()` + `load_model()` từ `/models`; `strip_metadata()` hỗ trợ DICOM (pydicom). *(M1)*
- **31/10 - 01/11:** viết `Dockerfile` tối ưu: multi-stage, base slim, cache layer, USER non-root. Chạy thử `audit2_image_cache.sh`; đo model load lần đầu và sau khi có Named Volume.
- **02/11:** chạy E2E với model thật, ghi độ trễ suy luận. *(M2)*
- **03/11:** chạy Audit 2 chính thức. **04/11:** viết mục Audit 2 + phần thảo luận về trọng số nặng/cache.

### P3 - Module 03 (LLM) + Audit 3 (Chịu lỗi & Tài nguyên) + ghi chú triệu chứng
- **28-29/10:** **chốt hướng LLM** (API ngoài hay model local nhỏ - API nhanh hơn để kịp hạn; model local làm Audit 3 "đáng giá" hơn nhưng nặng) và nói với nhóm trước tối 29/10. Soạn ghi chú triệu chứng (tổng hợp) + `expected_priority` cho 15-20 ca -> `data/sample_cases/cases.csv`.
- **29/10:** `cp Dockerfile Dockerfile.naive`.
- **30/10:** `generate_soap_real()` với prompt SOAP, ép JSON, có fallback; chốt luật `decide_priority()`. *(M1)*
- **31/10 - 01/11:** tối ưu Dockerfile (non-root, cache); chỉnh `deploy.resources.limits`; hoàn thiện `audit3_fault_tolerance.sh` (kill, OOM, các service khác vẫn sống, UI báo lỗi ra sao).
- **02/11:** E2E; so nhãn hệ thống với `expected_priority`. *(M2)*
- **03/11:** chạy Audit 3 chính thức. **04/11:** viết mục Audit 3 + thảo luận self-healing/giới hạn tài nguyên.

### P4 - Module 04 (Database) + Audit 4 (Bảo mật & Bền vững) + hạ tầng/repo
- **28/10:** chạy scaffold đầu tiên, **sửa mọi lỗi build/compose** để cả nhóm chạy được; thiết lập repo Git + nhánh + quy tắc PR.
- **29/10:** hoàn thiện `init.sql` (kiểm tra schema khớp `db.py`); thử `user: postgres` (non-root) cho DB; tài khoản DB quyền tối thiểu.
- **30/10:** rà `docker-compose.yml` (healthcheck, `depends_on`, restart, không publish 5432); soạn **checklist hardening** cho cả nhóm (USER non-root, không secret trong image). *(M1)*
- **31/10 - 01/11:** hoàn thiện `audit4_security_persistence.sh` (bền vững, cô lập mạng, non-root); thử `internal: true` cho `backend`.
- **02/11:** kiểm tra bền vững dữ liệu trên stack tích hợp. *(M2)*
- **03/11:** chạy `run_all.sh` (Audit tổng) trên máy sạch. *(M3)*
- **04/11:** viết mục Audit 4 + **chương Thảo luận tổng hợp** (rủi ro <-> cơ chế Docker) + README cuối.
- **05/11:** kiểm thử "clone mới -> 1 lệnh" trên máy sạch.

## Rủi ro và phương án B
| Rủi ro | Phương án |
|---|---|
| Model thị giác/LLM quá nặng, tải lâu | Giữ `mock` cho phần chưa kịp, nói rõ trong báo cáo; chọn model nhỏ hơn |
| Bind Mount chậm/không reload trên Windows/macOS | Đây chính là phát hiện của Audit 1 - ghi lại số đo và nêu giải pháp (`fileWatcherType=poll`) |
| Máy yếu không chạy nổi LLM local | P3 dùng API ngoài; vẫn làm Audit 3 trên container API wrapper |
| Trễ tiến độ | Cắt theo thứ tự: bỏ DICOM -> bỏ trang Lịch sử đẹp -> giảm số ca xuống 15; **không** cắt 4 audit |
| Lỗi nền tảng (`docker compose up` hỏng) | P4 xử lý ngay ngày 28/10 - đây là việc ưu tiên số 1 |
