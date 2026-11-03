# P1 local validation – 03 Nov 2026

- `python -m unittest discover -s services/01-ui/tests -v`: 14/14 PASS.
- `python services/01-ui/e2e_cases.py --ui-mock --cases data/sample_cases/p1_synthetic_cases.csv`: 20/20 PASS.
- `python -m compileall`: PASS for all Python source files.
- `bash -n audits/audit1_reproducibility.sh`: PASS (static Bash syntax validation).
- The 20-case CSV fixture is entirely synthetic; it tests the UI boundary and response contracts, **not clinical accuracy**.
- Unit tests use mocked HTTP requests to exercise P2/P3 contract integration without contacting live APIs.
- **NOT RUN:** Docker image build, live P2 model inference, live P3 LLM endpoint,
  PostgreSQL writes, Audit 1 on multiple OSes. Those require the team integration environment.
- **NOT PUSHED:** No GitHub repository or branch was changed.
