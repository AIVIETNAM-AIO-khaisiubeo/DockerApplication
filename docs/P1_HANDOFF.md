# P1 – UI handoff for MedTriage AI

This folder overlay is designed for `DockerApplication/main` (2026-11-03).
**It does not modify GitHub automatically.** Copy its files into the repository root, preserving their paths.

## Responsibility and scope

P1 owns `services/01-ui/` and UI-specific software tests. This implementation covers:

1. Streamlit interface for PNG/JPG upload and synthetic symptom text.
2. Live health indicators for Vision, LLM, PostgreSQL.
3. Vision `/predict` → LLM `/soap` contract validation, sensible connection/HTTP/timeout errors.
4. SOAP, triage label, response modes, latency metrics, prediction-score visualization, raw JSON.
5. PostgreSQL `save_case()` and `list_cases()` with no schema changes.
6. Standalone `UI_MOCK_BACKENDS=1` with session-only history and **zero** calls to P2/P3/P4.
7. Explicit manual score entry for integration development (no PostgreSQL write).
8. `smoke_test.py` compatibility with Audit 1 and 4 (`PROB_SHA256`, `SAVED_CASE_ID`).
9. 20 synthetic cases with optional CSV E2E test and unit tests.
10. Dockerfile with dependency-layer caching and non-root runtime user.

## Files

- `services/01-ui/app.py` – Streamlit page, state, visual output and history.
- `services/01-ui/client.py` – isolated HTTP client, contract checks, deterministic UI-only mocks.
- `services/01-ui/db.py` – PostgreSQL persistence.
- `services/01-ui/smoke_test.py` – existing audit CLI compatibility.
- `services/01-ui/e2e_cases.py` – 20-case CSV software pipeline test.
- `services/01-ui/tests/test_client.py` – offline unit tests.
- `services/01-ui/Dockerfile` – P1 runtime with non-root user.
- `services/01-ui/requirements.txt` – pinned Python dependencies.
- `data/sample_cases/p1_synthetic_cases.csv`, `p1_test_image.png` – pure synthetic fixtures.
- `audits/audit1_reproducibility.sh` – completed P1 reproducibility/build-cache script.

The `main` branch already has `docker-compose.p1.yml`, `docker-compose.yml`,
`docker-compose.override.yml`, `services/04-db/init.sql`, and `docs/CONTRACT.md`;
**do not replace them with the Demo3 root-level files**. These continue to be used unchanged.

## Setup on Windows / Docker Desktop

Open a terminal in the repository root (not the zip folder):

```powershell
git fetch origin
git switch main
git pull --ff-only origin main
git switch -c p1-ui-complete
```

Extract the ZIP into a staging folder, then copy the `services`, `data`, and `docs`
folders from the extracted overlay into the repository root. Overwrite **only**
matching P1 files. Do not run `git merge Demo3` and do not delete the original modules.

### A. P1 isolated mode – no P2/P3/P4 needed

```powershell
docker compose -f docker-compose.p1.yml up --build -d
docker compose -f docker-compose.p1.yml ps
docker compose -f docker-compose.p1.yml logs --tail=100 ui
```

Open http://localhost:8501. Expect the `UI ISOLATION MODE` banner.
Upload `data/sample_cases/p1_test_image.png`, write synthetic text, press Analyze,
check all SOAP fields, priority, bars, modes and session history. No PostgreSQL is used.

Stop only this stack:

```powershell
docker compose -f docker-compose.p1.yml down
```

### B. P1 unit tests (without Docker)

From repository root, after installing `services/01-ui/requirements.txt` in a Python 3.11 environment:

```powershell
python -m unittest discover -s services/01-ui/tests -v
```

### C. Integrated stack (needs P2/P3/P4)

After the leader has copied and adapted code from `demo2` into `services/02-vision`
and from `Demo3` into `services/03-llm`, and ensured the full-stack Compose builds:

```powershell
docker compose -f docker-compose.yml up --build -d
docker compose -f docker-compose.yml ps
docker compose -f docker-compose.yml exec -T ui python smoke_test.py
```

Open http://localhost:8501. Upload a **test-only** image, add synthetic symptoms and
check the P2/P3 mode displayed in the UI. If either mode is `mock`, it must **not** be
presented as a clinical inference. Verify the inserted case in the History tab.

If the LLM is running outside Docker on the host (Ollama), `Demo3` uses
`http://host.docker.internal:11434/v1`. The P3 owner must configure the LLM
container to access that host, test connection and document the resource limits.
The existing `docker-compose.yml` does **not** yet pass that configuration.

### D. Run 20-case batch test

**UI-only / no backend:** run on your PC if Python dependencies are installed:

```powershell
python services/01-ui/e2e_cases.py --ui-mock --cases data/sample_cases/p1_synthetic_cases.csv --output p1_e2e_results.csv
```

**Integrated APIs:** inside the running UI container:

```powershell
docker compose -f docker-compose.yml exec -T ui python e2e_cases.py
docker compose -f docker-compose.yml cp ui:/tmp/p1_e2e_results.csv ./p1_e2e_results.csv
```

For a test database used only for this exercise, optionally use `--save` to verify
persistence. Do not use real patient data. The CSV measures **software/contract pass**,
not clinical diagnostic accuracy. These 20 cases intentionally reuse a purely synthetic
image; they provide no radiology evidence or clinical ground truth.

### E. Audit 1: reproducibility, bind mounts and evidence

On Windows Git Bash/WSL, macOS and Linux, after full-stack P2/P3/P4 integration:

```bash
bash audits/audit1_reproducibility.sh
```

The supplied `audits/audit1_reproducibility.sh` replaces the earlier Audit 1
scaffold. It records OS/Docker versions, smoke-test `PROB_SHA256`, bind-mount file
propagation time and Docker source-change rebuild time in `audits/results/<run_id>/`.
The benchmark writes a temporary probe and builds from a disposable code copy;
it does **not** modify your checked-in `app.py` or delete Docker volumes.
Save per-OS: OS/version, Docker/Compose versions, command, timestamp, exit code,
`PROB_SHA256`, mount/rebuild timings, and the audit log.
A matching hash only demonstrates stable output for the *same input and configuration*,
not real medical reproducibility. **Real model** scores can vary across hardware,
software versions and accelerator settings; document those differences rather than
claiming exact hashes are guaranteed in real mode.

The **browser-visible reload** still requires a separate manual observation:
start `docker compose up -d` with override (development mode), edit one harmless
UI title/string locally, and measure until an open browser shows the change.
Repeat without the override using `docker compose -f docker-compose.yml up --build -d`
and record the time to see the new UI. Run three trials per mode, report medians,
laptop specs and file watcher configuration. The automated mount-propagation
metric is intentionally not mislabeled as Streamlit browser reload latency.

### F. Audit 4 compatibility

The default `smoke_test.py` sample is `/data/sample_cases/p1_test_image.png`
(128×128 purely synthetic grayscale fixture), so it is large enough for P2's
32-pixel minimum side constraint. `smoke_test.py --save` retains the exact `SAVED_CASE_ID=...` log needed by
`audits/audit4_security_persistence.sh`. New P1 Dockerfile runs non-root, which
addresses **only the P1** non-root check; P2/P3/P4 owners must handle their services.

The audit 4 script contains `docker compose down -v`. Run it **only on a disposable
stack**; this destroys the named volumes used by its Compose project.

## P1 acceptance checklist

- [ ] P1-only stack starts and displays `UI ISOLATION MODE`.
- [ ] Upload and analysis produce all four SOAP fields; no P2/P3/DB is contacted.
- [ ] 14 offline tests pass; 20 synthetic UI mock cases pass.
- [ ] Real API mode calls `/predict` then `/soap` and respects `CONTRACT.md`.
- [ ] P2/P3 timeouts, HTTP errors and malformed JSON show comprehensible errors.
- [ ] PostgreSQL history works and a DB outage does not erase the visible result.
- [ ] Manual score testing is labeled and is never persisted to DB.
- [ ] Dockerfile builds and UI runs as non-root.
- [ ] Smoke test outputs `PROB_SHA256`; `--save` outputs `SAVED_CASE_ID`.
- [ ] Audit 1 results are recorded from at least the intended OS environments.
- [ ] Code review PR targets up-to-date `integration`, then full integration is validated before main.

## Known external blockers (not caused by P1)

- `demo2` is in its own root-level project layout with a separate Git history;
  its requirements and Docker runtime need separate validation before integration.
- `Demo3` uses root-level Python files but its Dockerfile refers to `app/` and
  `app.main:app` and therefore must be corrected by P3/integration.
- `integration` was behind `main` by 42 commits at the time of review; update it
  before opening the P1 PR to avoid mixing unrelated documentation changes.
- No actual container E2E run or DB persistence was performed during packaging.

