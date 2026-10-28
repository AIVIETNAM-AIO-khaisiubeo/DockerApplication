# Hợp đồng API giữa các module (đóng băng từ 28/10)

Mọi thay đổi **phải báo cả nhóm** vì sẽ ảnh hưởng người khác. Nếu cần thêm trường, chỉ **thêm**, không đổi tên/xóa trường cũ.

## Module 02 - Vision (`http://vision:8000`)
`POST /predict` - `multipart/form-data`, trường `file` (PNG/JPG; DICOM do P2 bổ sung)
```json
{
  "probabilities": {"Pneumonia": 0.41, "Pleural Effusion": 0.12, "Cardiomegaly": 0.05,
                    "Atelectasis": 0.20, "Pneumothorax": 0.02, "No Finding": 0.59},
  "metadata_removed": true,
  "mode": "mock | real",
  "latency_ms": 123
}
```
`GET /health` -> `{"status":"ok","mode":"...","model_load_ms":0}`

## Module 03 - LLM (`http://llm:8000`)
`POST /soap`
```json
// request
{"symptoms": "sốt 3 ngày, ho có đờm", "findings": {"Pneumonia": 0.41, "...": 0.0}}
// response
{"soap": {"S": "...", "O": "...", "A": "...", "P": "..."},
 "priority": "EMERGENT | URGENT | ROUTINE",
 "mode": "mock | real", "latency_ms": 456}
```
`GET /health` -> `{"status":"ok","mode":"..."}`
`POST /debug/crash`, `POST /debug/allocate?mb=N` - chỉ khi `ENABLE_DEBUG=1` (Audit 3).

## Module 04 - Database (`db:5432`, chỉ trong mạng `backend`)
Bảng `cases` - xem `services/04-db/init.sql`. UI ghi/đọc qua `services/01-ui/db.py`.
Không lưu tên/ID bệnh nhân.

## Mạng & volume
- `frontend`: chỉ `ui`, là service duy nhất publish cổng (8501).
- `backend`: `ui`, `vision`, `llm`, `db`. Không service nào ngoài `ui` publish cổng.
- Named Volumes: `vision_models` (/models của vision), `llm_models` (/models của llm), `db_data`.
> Lưu ý: sơ đồ trong bản đề cương trước vẽ vision/llm nằm cả ở frontend. Bản scaffold này chọn UI làm "cổng" duy nhất
> (UI ở cả hai mạng, vision/llm/db chỉ ở backend) vì cô lập tốt hơn; cập nhật sơ đồ báo cáo cho khớp.
