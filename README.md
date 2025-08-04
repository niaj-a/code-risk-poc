# Code Risk POC

FastAPI + Celery service that takes a code change (GitHub webhook or manual diff),
redacts obvious secrets, runs an async risk pass (LangChain or a local mock), and
stores findings in Postgres. Devs can chat against a finished analysis.

## What it does

- GitHub `push` / `pull_request` webhooks (HMAC verified)
- Manual diff submit API
- Celery worker + Redis queue
- Regex redaction before LLM calls
- LangChain structured output (`AnalysisReport`) for OpenAI / Azure OpenAI
- Deterministic mock analyzer when you don't want to hit an API
- Chat grounded on the stored redacted diff + report
- Repo allowlist, diff length cap
- Compose stack: API, worker, Postgres, Redis

```mermaid
flowchart LR
  subgraph ingress [Ingress]
    GH[GitHub Webhook]
    Manual[Manual Diff API]
  end
  subgraph apiLayer [FastAPI]
    Routes[API Routes]
    Sec[HMAC plus Allowlist]
  end
  subgraph asyncProc [Async]
    Redis[(Redis)]
    Celery[Celery Worker]
  end
  subgraph analyze [Analysis]
    Redact[Redaction]
    LLM[LangChain OpenAI or Azure]
    Mock[Mock Analyzer]
  end
  PG[(PostgreSQL)]
  Routes --> Sec
  GH --> Routes
  Manual --> Routes
  Sec -->|queued Analysis| PG
  Sec -->|task| Redis
  Redis --> Celery
  Celery --> Redact
  Redact --> LLM
  Redact --> Mock
  Celery -->|completed or failed| PG
  Routes -->|GET and chat| PG
```

## Layout

```text
app/
  api/routes.py
  core/config.py, security.py
  db/models.py, session.py
  schemas/analysis.py
  services/github.py, llm.py, mock_analyzer.py, redaction.py
  workers/celery_app.py, tasks.py
  main.py
tests/
sample_payloads/
Dockerfile
docker-compose.yml
Makefile
requirements.txt
.env.example
```

