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

## 7) Docker
```bash
docker build -t docker.io/ahmedhajjej/devops-api:local .
docker run -p 8000:8000 docker.io/ahmedhajjej/devops-api:local
```

## 8) CI/CD (GitHub Actions)
- Triggers on push (main/feat) and PR to main.
- Jobs: pytest; Semgrep (warning mode); build/push image (only on main pushes) to `docker.io/ahmedhajjej/devops-api:{latest,sha}`; ZAP baseline placeholder.
- Secrets needed: `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`.

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

## 13) Future Improvements
- Pin k8s image to digests/tags per release.
- Add resource requests/limits in Deployment.
- Add structured tracing (OpenTelemetry) and log shipping.
- Extend DAST to target deployed URL and export reports.