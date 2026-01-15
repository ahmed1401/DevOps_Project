# DevOps Demo API — Report (1–2 pages)

## Architecture & Design
- Stateless FastAPI service (≤150 LOC), in-memory store (no DB), endpoints: /health, /items (GET/POST), /metrics.
- Flow: Dev → GitHub (issues/PRs/reviews) → GitHub Actions (test, SAST, build/push, DAST baseline) → Docker Hub → Kubernetes Deployment/Service.
- Observability built-in: JSON logs with request_id, Prometheus counters/histograms, request_id returned to clients.

```
Dev → GitHub (Issues/PRs/Reviews)
		│
		▼
	GitHub Actions
		├─ pytest
		├─ Semgrep
		├─ build & push image
		└─ ZAP baseline
		│
		▼
	Docker Hub (registry)
		│
		▼
	Kubernetes
		├─ Deployment (devops-api, port 8000, probes)
		└─ Service (ClusterIP 80→8000)
Observability: JSON logs + Prometheus metrics (/metrics)
```

## Runtime view
```
Client → FastAPI (in-memory store)
		 ├→ JSON logs (stdout, includes request_id)
		 └→ /metrics scraped by Prometheus
```

## Tooling Justification
- Python 3.11 + FastAPI + Uvicorn: modern async stack, minimal boilerplate, OpenAPI auto-docs; fits small footprint.
- Prometheus client: standard metrics exposition for SRE-style monitoring.
- Docker + Docker Hub: immutable artifacts, registry distribution.
- GitHub Actions: integrated CI/CD, easy secrets and matrix; runs pytest, Semgrep, build/push, ZAP baseline.
- Semgrep (SAST): fast, good Python coverage; warning-mode to run without token.
- OWASP ZAP baseline (DAST): active scan hook; placeholder target to point at deployed URL.
- Kubernetes (minikube/kind): realistic deployment model with Deployment/Service, probes on /health.

## Observability Strategy
- Metrics: `http_requests_total` counter and `http_request_latency_seconds` histogram labeled by method/path/status; exposed at /metrics for Prometheus scraping.
- Logs: JSON to stdout including request_id, method, path, status, latency_ms; suitable for log aggregation.
- Tracing-lite: request_id middleware (header propagate or generate), echoed in responses and logs; can be extended to OpenTelemetry.

## Security Strategy
- SAST: Semgrep in CI; warning mode without token, configurable to fail builds on findings when tokened.
- DAST: ZAP baseline job ready; target should be updated to the deployed service URL; can export reports.
- Container: python:3.11-slim, non-root user, .dockerignore to reduce surface.

## Kubernetes Setup
- Deployment: 1 replica, image `docker.io/ahmedhajjej/devops-api:latest`, readiness/liveness on /health, port 8000.
- Service: ClusterIP on port 80 → 8000.
- Local access (minikube): `minikube service devops-api --url`.
- Suggested hardening: pin image to digest, add resource requests/limits, configure HPA when load testing.

## Security & DAST notes (ZAP baseline)
- Target (example): https://avon-folders-reaches-weeks.trycloudflare.com
- Findings (WARN only): cache-control re-examine, missing X-Content-Type-Options, missing HSTS, cacheable content, Spectre isolation header missing, Sec-Fetch-Dest missing (and 404s for robots/sitemap).
- Mitigations: set `X-Content-Type-Options: nosniff`, add HSTS when fronted by HTTPS, tighten cache headers on API responses.

## Lessons Learned / Future Work
- Tag immutably for k8s (`:sha` or digest) to avoid drift; promote via environments.
- Add resource requests/limits and HPA for resilience; add PodDisruptionBudget for availability.
- Integrate OpenTelemetry tracing and ship JSON logs to a collector.
- Expand DAST to full scan against deployed URL and archive reports.
- Add SBOM generation (e.g., syft) and signing (cosign) in CI for supply chain integrity.