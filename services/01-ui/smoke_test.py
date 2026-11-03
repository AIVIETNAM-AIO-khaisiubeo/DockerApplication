"""Compatible with audits/audit1_reproducibility.sh and audit4_security_persistence.sh.

Run inside UI container: python smoke_test.py [--save] [path/to/image]
"""
import argparse
import hashlib
import json
import os
import sys

import client


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", default="/data/sample_cases/p1_test_image.png")
    parser.add_argument("--save", action="store_true", help="Save the synthetic run to PostgreSQL")
    args = parser.parse_args()
    try:
        with open(args.image, "rb") as handle:
            data = handle.read()
        vision = client.predict_image(os.getenv("VISION_URL", "http://vision:8000"),
                                     os.path.basename(args.image), data, "image/png")
        symptoms = "[SYNTHETIC TEST] ho, sốt, khó thở (smoke test; không phải dữ liệu bệnh nhân)"
        llm = client.request_soap(os.getenv("LLM_URL", "http://llm:8000"),
                                  symptoms, vision["probabilities"])
        print(json.dumps({"vision": vision, "llm": llm}, ensure_ascii=False, indent=2))
        # Keep original SHA256 format for Audit 1 across operating systems.
        digest = hashlib.sha256(json.dumps(vision["probabilities"], sort_keys=True).encode()).hexdigest()
        print("PROB_SHA256=" + digest)
        if args.save:
            import db
            case_id = db.save_case(symptoms, vision["probabilities"], llm["soap"],
                                   llm["priority"], vision["latency_ms"], llm["latency_ms"])
            print(f"SAVED_CASE_ID={case_id}")
        return 0
    except (client.ServiceError, OSError) as exc:
        print(f"SMOKE_TEST_FAILED: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"SMOKE_TEST_FAILED: {type(exc).__name__}; see logs", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
