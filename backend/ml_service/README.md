# ML Sub-Service — Trust Model & Deployment Guide

## Overview

The ML Sub-Service is a **lightweight, stateless FastAPI application** that runs
on port `8001` and handles ML inference for the Interview module.

---

## Trust Model

> **This service is intended for internal Docker network use only.**

| Concern | Details |
|---|---|
| **Authentication** | Handled entirely by the core API (port 8000). The ML service receives no JWT tokens and performs no auth checks. |
| **Caller trust** | The ML service trusts all HTTP callers — it assumes they are the core API on the same Docker network. |
| **Public exposure** | The ML service must **NOT** be publicly exposed. It should not appear in any external load-balancer or reverse-proxy config. |
| **Network isolation** | In docker-compose, `ml_service` has no published ports in production configs. Port `8001` is mapped only for local development. |

### Why no auth on the ML service?

Authentication at the ML service boundary would be redundant:

- The core API authenticates every student request with JWT before calling the ML service.
- Any caller that can reach the internal Docker network is already inside the trusted perimeter.
- Adding auth here would double key management complexity for zero security gain in this threat model.

If the threat model changes (e.g., the ML service is exposed externally), add
an internal shared-secret header check at that point.

---

## Running the Service

### Local development

```powershell
# From backend/
uvicorn ml_service.main:app --reload --port 8001
```

### docker-compose

```powershell
docker-compose up --build
```

The `ml_service` container is defined in `docker-compose.yml` and is reachable
from the core API container at `http://ml_service:8001`.

Set `ML_SERVICE_URL=http://ml_service:8001` in the core API's environment when
running under docker-compose.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/predict/questions` | Generate interview questions |
| POST | `/predict/performance` | Predict next-semester GPA |
| GET | `/predict/health` | Health probe |

---

## Future: Real ML Model

When a trained model is ready, replace the rule-based bodies in
`routers/predict.py` with model-loading and inference code. The HTTP contract
(request/response schemas) stays the same — the core API's `InterviewService`
does not need to change.
