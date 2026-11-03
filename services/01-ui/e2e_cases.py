"""15–20 synthetic-case API contract/E2E batch runner for P1.

Use --ui-mock for offline, zero-backend development. Without it, requires P2/P3.
Can --save to P4 only when running real API mode. This is NOT a medical evaluation.
"""
import argparse
import csv
import os
import pathlib
import sys
import time

import client


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", default="/data/sample_cases/p1_synthetic_cases.csv")
    p.add_argument("--output", default="/tmp/p1_e2e_results.csv")
    p.add_argument("--ui-mock", action="store_true")
    p.add_argument("--save", action="store_true", help="Save results to database; requires API mode")
    p.add_argument("--limit", type=int, default=20)
    args = p.parse_args()
    if args.save and args.ui_mock:
        p.error("--save and --ui-mock are mutually exclusive: isolated UI never writes DB")
    path = pathlib.Path(args.cases)
    if not path.exists():
        print(f"Input CSV not found: {path}", file=sys.stderr)
        return 2
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))[: max(1, args.limit)]
    if not rows:
        print("No cases found", file=sys.stderr)
        return 2
    results, failures = [], 0
    for case in rows:
        started = time.perf_counter()
        result = {"case_id": case.get("case_id", ""), "image_file": case.get("image_file", ""),
                  "status": "FAIL", "priority": "", "vision_mode": "", "llm_mode": "",
                  "vision_latency_ms": "", "llm_latency_ms": "", "elapsed_ms": "", "saved_case_id": "", "error": ""}
        try:
            image_path = path.parent / case["image_file"]
            with image_path.open("rb") as handle:
                image_bytes = handle.read()
            data = client.analyze(case["symptoms"], image_name=image_path.name,
                                  image_bytes=image_bytes, ui_mock=args.ui_mock,
                                  vision_url=os.getenv("VISION_URL", "http://vision:8000"),
                                  llm_url=os.getenv("LLM_URL", "http://llm:8000"))
            v, l = data["vision"], data["llm"]
            result.update(status="PASS", priority=l["priority"], vision_mode=v["mode"],
                          llm_mode=l["mode"], vision_latency_ms=v["latency_ms"],
                          llm_latency_ms=l["latency_ms"])
            if args.save:
                import db
                result["saved_case_id"] = db.save_case(case["symptoms"], v["probabilities"],
                                                       l["soap"], l["priority"],
                                                       v["latency_ms"], l["latency_ms"])
        except Exception as exc:
            failures += 1
            result["error"] = str(exc)[:160] if isinstance(exc, client.ServiceError) else type(exc).__name__
        result["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 1)
        results.append(result)
        print(f"{result['case_id']}: {result['status']} (vision={result['vision_mode']}, llm={result['llm_mode']})")
    out = pathlib.Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    print(f"RESULT={out} TOTAL={len(results)} PASS={len(results) - failures} FAIL={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
