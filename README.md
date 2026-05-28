# 🚨 On-Call AI Incident Responder

> AI-driven autonomous agent built with FastAPI and Google Gemini to automate incident triage, root cause analysis and mitigation playbooks during 24/7 on-call shifts.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?style=flat&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-API-8E75B2?style=flat&logo=googlegemini&logoColor=white)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector%20DB-DC244C?style=flat&logo=qdrant&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)
[![Tests](https://github.com/AbelRodriguez97/on-call-ai-responder/actions/workflows/tests.yml/badge.svg)](https://github.com/AbelRodriguez97/on-call-ai-responder/actions/workflows/tests.yml)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 🎯 Motivation

On-call engineers face a critical challenge during incidents: under extreme pressure, they must rapidly triage alerts, identify root causes and execute mitigation steps — often at 3 AM with limited context.

This project automates that first-response workflow using an AI agent that:
- Receives production alerts via HTTP webhook
- Retrieves the most relevant playbook context via semantic search (RAG)
- Generates a structured incident report with severity, root cause and mitigation steps
- Automatically notifies the team on Slack when escalation is required

---

## 🧩 What it does

- 🔔 **Receives** production alerts as JSON webhooks from Datadog, Grafana or any HTTP-capable monitoring tool
- 📚 **Retrieves** relevant playbook context from Qdrant vector store via semantic similarity search (RAG)
- 🤖 **Analyzes** incidents using Google Gemini with strict Pydantic structured output
- 📋 **Generates** actionable incident reports: severity, root cause, prioritized mitigation steps, escalation flag
- 🔴 **Notifies** the on-call team on Slack automatically when escalation is required
- 🐳 **Runs** in Docker with a single `docker-compose up` command

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐
│  Monitoring Tool                │
│  (Datadog / Grafana / custom)   │
└──────────────┬──────────────────┘
               │ POST /api/v1/alerts
               ▼
┌─────────────────────────────────┐
│  FastAPI Endpoint               │
│  (async, Swagger UI included)   │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│  NativeIncidentAgent            │
│                                 │
│  1. Semantic search → Qdrant    │
│  2. Build prompt with context   │
│  3. Call Gemini (structured)    │
│  4. Validate via Pydantic       │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌──────────────┐  ┌──────────────────┐
│ IncidentReport│  │ SlackNotifier    │
│ (JSON response│  │ (if escalation   │
│  to caller)   │  │  required)       │
└──────────────┘  └──────────────────┘
```

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API | FastAPI + uvicorn | Async HTTP server with auto Swagger UI |
| AI | Google Gemini 2.5 Flash | Incident analysis with structured JSON output |
| RAG | Qdrant (in-memory) | Semantic search over playbook documentation |
| Validation | Pydantic V2 | Strict schema enforcement on all AI responses |
| Notifications | Slack Incoming Webhooks | Escalation alerts via Block Kit messages |
| Containerization | Docker + docker-compose | Reproducible deployment |
| Testing | pytest + httpx + pytest-asyncio | 24 tests, fully mocked external services |
| CI | GitHub Actions | Runs test suite on every push and PR |

---

## 📦 Project structure

```
on-call-ai-responder/
├── .github/
│   └── workflows/
│       └── tests.yml          # CI: runs pytest on every push/PR
├── app/
│   ├── agents/
│   │   └── incident_agent.py  # NativeIncidentAgent + IncidentReport schema
│   ├── core/
│   │   └── config.py          # Settings loaded from .env
│   ├── database/
│   │   └── vector_store.py    # Qdrant in-memory store + playbook indexer
│   ├── notifications/
│   │   └── slack.py           # SlackNotifier with Block Kit formatting
│   └── main.py                # FastAPI app + lifespan + alert endpoint
├── data/
│   └── playbooks/             # Markdown playbooks indexed at startup
├── tests/
│   ├── conftest.py            # Shared fixtures (mocked agent, ASGI client)
│   ├── test_alert_endpoint.py # 7 tests for POST /api/v1/alerts
│   ├── test_health.py         # 2 tests for health check
│   ├── test_slack_notifier.py # 8 tests for SlackNotifier
│   └── test_vector_store.py   # 6 tests for Qdrant store
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🚀 Quick start

### Option A: Local

```bash
git clone https://github.com/AbelRodriguez97/on-call-ai-responder.git
cd on-call-ai-responder

python -m venv .venv
source .venv/bin/activate          # Linux/macOS
# .\.venv\Scripts\Activate.ps1    # Windows PowerShell

pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your GEMINI_API_KEY (and optionally SLACK_WEBHOOK_URL)

uvicorn app.main:app --reload
```

### Option B: Docker

```bash
cp .env.example .env
# Edit .env with your keys

docker-compose up --build
```

Both options expose the API at **http://localhost:8000**.
Interactive docs available at **http://localhost:8000/docs**.

---

## 🧪 Running tests

```bash
pytest tests/ -v
```

Expected output: **24 passed, 0 failed, 0 warnings**.

Tests use mocked external services (Gemini API, Slack webhooks) — no real API keys needed to run the test suite.

---

## 📡 API Usage

### Health check

```bash
GET /
→ {"status": "online", "service": "On-Call AI Incident Responder", "version": "1.0.0"}
```

### Process an alert

```bash
POST /api/v1/alerts
Content-Type: application/json

{
  "alert_id": "ALR-2026-001",
  "source_service": "Keycloak-Identity-Provider",
  "raw_message": "CRITICAL: AUTH_TIMEOUT_500. Database pool exhausted.",
  "environment": "production"
}
```

Response:

```json
{
  "incident_severity": "CRITICAL",
  "root_cause_analysis": "Database connection pool exhausted...",
  "mitigation_steps": [
    "Check Keycloak logs for connection errors",
    "Restart connection pool via db_flush_connections.sh",
    "Monitor pool metrics in Datadog"
  ],
  "requires_escalation": true,
  "slack_summary": "CRITICAL: Keycloak AUTH_TIMEOUT_500 — DB pool exhausted. Escalation required."
}
```

If `requires_escalation` is `true` and `SLACK_WEBHOOK_URL` is configured, a Block Kit alert is automatically sent to the Slack channel.

---

## ⚙️ Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | Google AI Studio API key |
| `SLACK_WEBHOOK_URL` | ⚠️ Optional | Slack Incoming Webhook URL for escalation alerts |

Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).
Set up a Slack webhook at [api.slack.com/apps](https://api.slack.com/apps).

---

## 🗺️ Roadmap

- [x] FastAPI async endpoint for alert ingestion
- [x] RAG pipeline with Qdrant vector store
- [x] Gemini-powered incident analysis with Pydantic structured output
- [x] Dockerization with Dockerfile and docker-compose
- [x] pytest suite with 24 tests (endpoint, vector store, Slack notifier)
- [x] GitHub Actions CI workflow
- [x] Slack notifications via Block Kit for escalation-required incidents
- [ ] Microsoft Teams integration
- [ ] Alert deduplication (avoid duplicate Slack messages per incident)
- [ ] Persistent Qdrant storage (replace in-memory with on-disk)
- [ ] Multi-playbook support (one collection per service)

---

## 📄 License

MIT — see [LICENSE](LICENSE).

---

## 👤 Author

**Abel Rodriguez** — Software Engineer @ Accenture, building AI tools for security operations and incident response.

📫 [LinkedIn](https://www.linkedin.com/in/abel-rodriguez-gomez-20a446132/) · 📧 abelrodr42malaga@gmail.com · [threat-intel-agent](https://github.com/AbelRodriguez97/threat-intel-agent)