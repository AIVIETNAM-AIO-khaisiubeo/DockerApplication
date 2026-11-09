
import multiprocessing
import os
import time

from fastapi import FastAPI

from . import llm_service as svc
from .models import SoapRequest

LLM_MODE = os.getenv("LLM_MODE", "mock")   

app = FastAPI(title="MedTriage - LLM API")


@app.get("/health")
def health():
    return {"status": "ok", "mode": LLM_MODE}


@app.post("/soap")
def soap(req: SoapRequest):
    t0 = time.perf_counter()
    priority = svc.decide_priority(req.symptoms, req.findings)
    mode = LLM_MODE
    if LLM_MODE == "real":
        try:
            note = svc.soap_real(req.symptoms, req.findings, priority)
        except Exception as e:  
            print(f"[soap] LLM lỗi, dùng template: {type(e).__name__}: {e}")
            note, mode = svc.soap_mock(req.symptoms, req.findings, priority), "mock"
    else:
        note = svc.soap_mock(req.symptoms, req.findings, priority)
    return {"soap": note, "priority": priority, "mode": mode,
            "latency_ms": int((time.perf_counter() - t0) * 1000)}


# ---- Chỉ phục vụ Audit 3 - tuyệt đối không bật khi demo ----
if os.getenv("ENABLE_DEBUG") == "1":
    _hog: list = []

    @app.post("/debug/crash")
    def debug_crash():
        os._exit(1)                                 

    @app.post("/debug/allocate")
    def debug_allocate(mb: int = 100):
        _hog.append(bytearray(b"\x01") * (mb * 1024 * 1024))   
        return {"allocated_mb": sum(len(x) for x in _hog) // (1024 * 1024)}

    @app.post("/debug/cpu")
    def debug_cpu(seconds: float = 15, workers: int = 4):
        n, sec = min(workers, 16), min(seconds, 120)
        for _ in range(n):
            multiprocessing.get_context("spawn").Process(target=svc.spin, args=(sec,), daemon=True).start()
        return {"workers": n, "seconds": sec}

    @app.post("/debug/hang")
    async def debug_hang(seconds: float = 90):
        time.sleep(min(seconds, 300))                 
        return {"hung_s": seconds}
