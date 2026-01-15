# DevOps Demo API (FastAPI)

Minimal FastAPI service (health, items, metrics) to demonstrate an end-to-end DevOps pipeline: GitHub workflow (issues/PRs/reviews), CI/CD, SAST/DAST, Docker, Kubernetes, and observability. Application code is under 150 lines.

## 1) Project Overview
- Stateless Python FastAPI API with in-memory items and health/metrics endpoints.
- Shows modern DevOps practices: CI/CD, security scans, containerization, k8s deploy, logs/metrics/tracing-lite.

## 2) Architecture
- Dev → GitHub (issues, branches, PRs, reviews) → GitHub Actions (pytest, Semgrep, build/push, ZAP baseline) → Docker Hub → Kubernetes (Deployment + Service). Observability via JSON logs + Prometheus metrics.

```
Developer
	│ push/PR
	▼
GitHub (Issues/PRs/Reviews)
	│ triggers
	▼
GitHub Actions
	├─ pytest
	├─ Semgrep (SAST)
	├─ build & push image
	└─ ZAP baseline (DAST hook)
	│
	▼
Docker Hub (image)
	│ pull
	▼
Kubernetes
	├─ Deployment (devops-api)
	└─ Service (ClusterIP 80→8000)
Observability: JSON logs + Prometheus /metrics
```

## 3) Tech Stack
- Python 3.11, FastAPI, Uvicorn, Prometheus client
- GitHub Actions, Docker, Docker Hub
- Semgrep (SAST), OWASP ZAP baseline (DAST)
- Kubernetes (minikube/kind friendly)

## 4) API
- `GET /health` – liveness
- `GET /items` – list items
- `POST /items` – create item
- `GET /metrics` – Prometheus exposition

## 5) Local Setup
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## 6) Tests
```bash
pytest
```

## 6.1) Smoke Test (minikube tunnel)
Keep `minikube service devops-api --url` running in a separate terminal to expose the ClusterIP service. Use these from PowerShell:
```powershell
curl.exe "http://127.0.0.1:57227/health"
curl.exe -X POST "http://127.0.0.1:57227/items" -H "Content-Type: application/json" --data-raw "{\"name\":\"test\"}"
curl.exe "http://127.0.0.1:57227/items"
curl.exe "http://127.0.0.1:57227/metrics" | Select-String http_requests_total -Context 0,2
```
Replace the URL/port with the value printed by `minikube service devops-api --url`.

## 7) Docker
```bash
docker build -t docker.io/ahmedhajjej/devops-api:local .
docker run -p 8000:8000 docker.io/ahmedhajjej/devops-api:local
```

## 8) CI/CD (GitHub Actions)
- Triggers on push (main/feat) and PR to main.
- Jobs: pytest; Semgrep (warning mode); build/push image (only on main pushes) to `docker.io/ahmedhajjej/devops-api:{latest,sha}`; ZAP baseline placeholder.
- Secrets needed: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.
- Re-run CI: open GitHub → Actions → select latest run → "Re-run all jobs" after updating secrets.
- ZAP baseline: set repo variable `ZAP_TARGET` to the live URL (e.g., your trycloudflare link), keep tunnel running, then push to `main`.
- ZAP artifacts: open the workflow run → Artifacts → `zap_scan` to download HTML/MD/JSON reports.

### Public tunnel quick start (for ZAP)
1) Run the service locally or in minikube and expose it (e.g., `minikube service devops-api --url`).
2) Start a quick tunnel (Windows example):
	```powershell
	& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://127.0.0.1:PORT_FROM_STEP1
	```
3) Copy the issued `https://<something>.trycloudflare.com` URL to the repo variable `ZAP_TARGET`.
4) Push to `main` to trigger ZAP; keep the tunnel terminal open until the run finishes.

## 9) Observability
- Logs: JSON to stdout with request_id, method, path, status, latency_ms.
- Metrics: `/metrics` exposes `http_requests_total` and `http_request_latency_seconds` histogram.
- Tracing-lite: request_id middleware; echoed in responses.

## 10) Security
- SAST: Semgrep in CI (fails on error/warning). No token required (warning mode).
- DAST: OWASP ZAP baseline job (adjust target URL when deployed).

## 11) Kubernetes
- Apply: `kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml`
- Check: `kubectl rollout status deploy/devops-api`
- Access (minikube): `minikube service devops-api --url`

## 12) Troubleshooting
- CI push failure: ensure Docker Hub secrets exist and branch is `main` for push stage.
- Import errors locally: activate venv and run from repo root.
- Probes failing: increase `initialDelaySeconds` in deployment.
- ZAP "Resource not accessible by integration": we disabled issue creation; ensure `ZAP_TARGET` is set as a repo variable (not a secret) and tunnel stays up during the run.

## 13) Future Improvements
- Pin k8s image to digests/tags per release.
- Add resource requests/limits in Deployment.
- Add structured tracing (OpenTelemetry) and log shipping.
- Extend DAST to target deployed URL and export reports.