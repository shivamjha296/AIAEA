# Regulatory Compliance Radar

**Real-time Indian banking regulatory intelligence — powered by live web data, AI extraction, and a professional web dashboard.**

Built for Indian Cooperative Banks to automatically monitor RBI, MeitY, CERT-In, SEBI and other regulators in real time.

---

## What This Does

The system watches Indian regulatory websites 24/7, extracts compliance requirements using AI, scores the risk to your bank, and presents everything in a live dashboard — with no hardcoded or fake regulatory data anywhere.

**The full pipeline, step by step:**

```
Live Web Search (SearchProvider Abstraction -> DDGSSearchProvider)
        ↓
Real Regulatory Sources (RBI, MeitY, CERT-In, SEBI, MCA)
        ↓
HTML / PDF Extraction
        ↓
Security Scan  ←── blocks prompt injection attacks
        ↓
Quarantined LLM  ←── extracts facts only, can't be manipulated
        ↓
Pydantic Validation  ←── strict schema, no hallucination
        ↓
Evidence Verification  ←── every claim tied to a verbatim quote
        ↓
Privileged LLM  ←── impact analysis on clean data
        ↓
Risk Scoring + Compliance Gaps
        ↓
Human Review Queue
        ↓
SQLite Audit Trail
        ↓
Next.js Web Dashboard
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web search | SearchProvider interface (DDGSSearchProvider default) — live, no API key |
| HTML extraction | BeautifulSoup4 |
| PDF extraction | PyMuPDF / pdfplumber |
| LLM inference | Ollama (local) — llama3.2:1b |
| Data validation | Pydantic v2 |
| Security | Custom IPI (Indirect Prompt Injection) scanner |
| API backend | FastAPI + Uvicorn |
| Database | SQLite |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS |
| Charts | Recharts |
| Tests | Pytest (74 tests, all passing) |

---

## Project Structure

```
AIAEA ACT-1/
│
├── main.py                  # Pipeline CLI entry point
├── models.py                # All Pydantic data schemas
├── config.py                # Organisation profile + search config
│
├── pipeline/                # 14 pipeline modules
│   ├── search.py            # DDGS live web search
│   ├── source_validator.py  # 4-tier source trust system
│   ├── retriever.py         # HTTP source retrieval
│   ├── extractor.py         # HTML + PDF text extraction
│   ├── security.py          # IPI prompt injection scanner
│   ├── quarantined_llm.py   # First LLM — extraction only
│   ├── evidence_verifier.py # Claim verification against source
│   ├── privileged_llm.py    # Second LLM — impact analysis
│   └── report_generator.py  # Final JSON report assembly
│
├── api/                     # FastAPI REST backend
│   ├── main.py              # All API endpoints
│   ├── database.py          # SQLite schema + queries
│   └── scanner.py           # Background scan runner + SSE
│
├── frontend/                # Next.js web dashboard
│   ├── app/
│   │   ├── page.tsx         # Overview / Command Centre
│   │   ├── regulations/     # Regulatory updates table + detail
│   │   ├── risk/            # Risk register + donut chart
│   │   ├── evidence/        # Evidence explorer (verbatim quotes)
│   │   ├── security/        # IPI monitor + architecture diagram
│   │   ├── review/          # Human approval workflow
│   │   └── audit/           # Full audit trail timeline
│   ├── components/          # Reusable UI components
│   └── lib/                 # API client + TypeScript types
│
├── reports/                 # Auto-saved JSON reports (pipeline output)
├── tests/                   # 57 unit tests
│
├── startallservices.ps1     # Launch everything (Windows PowerShell)
├── startallservices.bat     # Launch everything (Windows CMD)
├── startallservices.sh      # Launch everything (Linux / macOS)
│
├── requirements.txt         # Python dependencies
└── CONTEXT.md               # Full technical specification
```

---

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| Python 3.10+ | Backend pipeline | [python.org](https://python.org) |
| Ollama | Local LLM inference | [ollama.com](https://ollama.com/download) |
| Node.js 18+ | Frontend | [nodejs.org](https://nodejs.org) |
| Git | Version control | [git-scm.com](https://git-scm.com) |

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/shivamjha296/AIAEA.git
cd "AIAEA/AIAEA ACT-1"
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Ollama and pull a model

```bash
# Install Ollama (Windows)
winget install Ollama.Ollama

# Pull the configured model
ollama pull llama3.2:1b
```

Then update `config.py` line 22 if you pulled a different model:
```python
OLLAMA_MODEL = "llama3.2:1b"
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Running the Project

### Option A — Start everything at once (recommended)

**Windows (double-click or run in PowerShell):**
```powershell
powershell -ExecutionPolicy Bypass -File startallservices.ps1
```

**Windows CMD:**
```cmd
startallservices.bat
```

**Linux / macOS:**
```bash
bash startallservices.sh
```

This opens **4 separate terminal windows:**

| Window | What it runs | URL |
|---|---|---|
| 1 | Ollama LLM Server | `http://localhost:11434` |
| 2 | FastAPI REST API | `http://localhost:8000` |
| 3 | Next.js Dashboard | `http://localhost:3000` |
| 4 | Pipeline CLI | ready for manual scans |

Wait ~15 seconds, then open **http://localhost:3000** in your browser.

---

### Option B — Start services manually

**Terminal 1 — Ollama:**
```bash
ollama serve
```

**Terminal 2 — FastAPI backend:**
```bash
cd "AIAEA ACT-1"
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 3 — Next.js frontend:**
```bash
cd "AIAEA ACT-1/frontend"
npm run dev
```

**Terminal 4 — Run a pipeline scan (optional):**
```bash
cd "AIAEA ACT-1"
python main.py
python main.py --queries 2 --max-sources 3
```

---

## Dashboard Pages

| Page | What you see |
|---|---|
| **Overview** | KPI tiles, activity chart, recent regulations, risk distribution |
| **Regulatory Updates** | Searchable/filterable table of all discovered regulations |
| **Regulation Detail** | Full extraction: title, requirements, evidence quotes, actions |
| **Risk Register** | Interactive risk levels, donut chart, filterable register |
| **Evidence Explorer** | Split-panel: source list + verbatim quote evidence per source |
| **Security Monitor** | IPI architecture diagram, security event feed, threat details |
| **Human Review** | Approve/reject HIGH and CRITICAL findings with reason + name |
| **Audit Trail** | Chronological timeline of every pipeline event per scan |

---

## API Reference

The FastAPI backend runs at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System status (DB, LLM, search) |
| `GET` | `/api/dashboard/metrics` | KPI summary |
| `GET` | `/api/regulations` | Paginated regulations list |
| `GET` | `/api/regulations/{id}` | Full regulation detail |
| `GET` | `/api/risk` | Risk register + distribution |
| `GET` | `/api/security/events` | Security event feed |
| `GET` | `/api/security/metrics` | Security summary |
| `GET` | `/api/reviews/pending` | Pending human reviews |
| `POST` | `/api/reviews/{id}/approve` | Approve a regulation |
| `POST` | `/api/reviews/{id}/reject` | Reject a regulation |
| `POST` | `/api/scans` | Start a live pipeline scan |
| `GET` | `/api/scans/{id}/events` | Real-time SSE scan progress |
| `GET` | `/api/audit` | Audit trail |

---

## Security Architecture — IPI Defence

The system defends against **Indirect Prompt Injection (IPI)** — where a malicious website embeds instructions designed to hijack the AI.

**How we stop it:**

1. Raw web content hits the **IPI Scanner** first (20+ regex patterns)
2. Suspicious/malicious sources are **quarantined** — never sent to any LLM
3. Clean content goes to the **Quarantined LLM** — its only job is to extract facts into a Pydantic schema. Any injected text becomes a harmless string value.
4. The validated, sanitised JSON (not the raw text) goes to the **Privileged LLM** for impact analysis
5. The Privileged LLM **never sees raw web content** — injection is structurally impossible to propagate

```
Web Content → IPI Scanner → [BLOCKED] or → Quarantined LLM → Pydantic JSON → Privileged LLM
                                                               (sterile data only)
```

---

## Running Tests

```bash
cd "AIAEA ACT-1"
pytest tests/ -v
```

74 tests covering all pipeline modules.

---

## Configuration

Edit `config.py` to change:

| Setting | What it controls |
|---|---|
| `OLLAMA_MODEL` | Which local LLM model to use |
| `DDGS_TIMELIMIT` | How recent the search results are (`"m"` = last month) |
| `DDGS_MAX_RESULTS` | Results per search query |
| `OrganizationProfile` | Bank name, type, jurisdiction, regulatory domains |
| `REGULATORY_SEARCH_QUERIES` | Search query templates |

---

## Important Notes

- **No fake data** — every regulation on the dashboard came from a real web source
- **No hardcoded regulations** — the system discovers them live each time you scan
- **Public information only** — the LLM never accesses internal bank systems or policies
- Fields marked `UNKNOWN` or `REQUIRES INTERNAL BANK REVIEW` are explicit fail-safes, not errors
- This system does **not** constitute legal advice

---

## Acknowledgements

Built as a demonstration of autonomous AI agent design patterns:
- Dual-LLM architecture (Quarantined + Privileged)
- Indirect Prompt Injection defence
- Pydantic-enforced structured extraction
- Evidence-bound regulatory intelligence
- Human-in-the-loop approval workflow
