"""Chạy trong container ui:  docker compose exec -T ui python smoke_test.py [--save] [đường_dẫn_ảnh]
In ra kết quả pipeline + SHA256 của xác suất (dùng so sánh giữa các hệ điều hành ở Audit 1)."""
import argparse
import hashlib
import json
import os

import requests

p = argparse.ArgumentParser()
p.add_argument("image", nargs="?", default="/data/sample_cases/demo_synthetic.png")
p.add_argument("--save", action="store_true", help="lưu ca vào DB (dùng cho Audit 4)")
a = p.parse_args()

V, L = os.getenv("VISION_URL", "http://vision:8000"), os.getenv("LLM_URL", "http://llm:8000")
symptoms = "sốt, ho, khó thở nhẹ (ca thử nghiệm smoke test)"
with open(a.image, "rb") as f:
    vision = requests.post(f"{V}/predict", files={"file": (os.path.basename(a.image), f.read(), "image/png")}, timeout=120).json()
llm = requests.post(f"{L}/soap", json={"symptoms": symptoms, "findings": vision["probabilities"]}, timeout=300).json()
print(json.dumps({"vision": vision, "llm": llm}, ensure_ascii=False, indent=2))
print("PROB_SHA256=" + hashlib.sha256(json.dumps(vision["probabilities"], sort_keys=True).encode()).hexdigest())
if a.save:
    import db
    print("SAVED_CASE_ID=%d" % db.save_case(symptoms, vision["probabilities"], llm["soap"], llm["priority"], vision["latency_ms"], llm["latency_ms"]))
