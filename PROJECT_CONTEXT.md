# PROJECT_CONTEXT

## 1. PROJECT OVERVIEW
**Project name:** Regulatory Compliance Radar
**Domain:** Indian Banking

**Core purpose:** 
To provide an autonomous compliance monitoring system that continuously scans live sources for regulatory changes, assesses their impact on banking operations, and routes critical findings for human review.

**Real-world problem being solved:** 
Bank compliance teams manually monitor scattered regulatory sites (RBI, MeitY, CERT-In, SEBI). This process is slow, error-prone, and struggles to quickly map dense legal text to specific internal banking processes.

**Demonstration Use Case:** 
The DPDP Act (Digital Personal Data Protection) and associated rules are used as the primary demonstration use case. DPDP itself is not banking-specific, but it is used to demonstrate how the radar monitors cross-sectoral regulatory updates and determines their compliance impact specifically on a bank.

## 2. MAIN OBJECTIVE
Automatically discover current regulatory changes from the live web, securely analyze them using an LLM, validate the extracted information, verify evidence against source text, determine potential banking impact and risk, recommend actions, and send important decisions through human review.

## 3. COMPLETE PIPELINE

LIVE WEB
→ **SEARCH PROVIDER:** `SearchProvider` abstraction (defaults to `DDGSSearchProvider` using DuckDuckGo Search) executes dynamic live queries based on organization profile.
→ **SOURCE VALIDATION:** Filters raw HTML/PDF URLs and validates trust tiers.
→ **HTML/PDF EXTRACTION:** Uses BeautifulSoup and PyMuPDF to extract text from webpages and documents.
→ **PROMPT-INJECTION SECURITY:** A regex-based scanner (`security.py`) checks for prompt injections, obfuscation, or manipulation. Suspicious sources are quarantined.
→ **LLM EXTRACTION (Quarantined):** An LLM safely extracts factual regulatory claims and verbatim quotes from the untrusted text.
→ **PYDANTIC VALIDATION:** Enforces strict typing and JSON schema compliance on the extracted output.
→ **EVIDENCE VERIFICATION:** Ensures the LLM's claims are explicitly supported by exact source quotes present in the original text.
→ **PRIVILEGED IMPACT ANALYSIS (LLM):** A second, secure LLM uses the validated extraction and organization profile to determine banking impact and risk.
→ **RISK ENGINE:** Assigns priority (LOW, MEDIUM, HIGH, CRITICAL).
→ **RECOMMENDATIONS:** Generates actionable compliance tasks for specific banking departments.
→ **HUMAN REVIEW:** High/Critical risk items are routed to a dashboard queue for a human compliance officer to approve or reject.
→ **SQLITE:** Stores all scans, events, regulations, security threats, and reviews in an on-disk relational database.
→ **NEXT.JS DASHBOARD:** Presents live metrics, scan progress, and the human review queue.

## 4. TECHNOLOGY STACK

| Component | Technology | Purpose |
| --- | --- | --- |
| Backend API | FastAPI | REST API and Server-Sent Events (SSE) streaming |
| Web Search | SearchProvider (DDGS default) | Discovering live regulatory updates |
| LLM Inference | Ollama | Local execution of extraction and analysis LLMs (Model: llama3.2:1b) |
| Data Validation | Pydantic V2 | Enforcing strict JSON schemas for LLM outputs |
| Database | SQLite | Relational storage for regulations, scans, and audit logs |
| HTML Parsing | BeautifulSoup4 / lxml | Extracting text from raw web pages |
| PDF Parsing | PyMuPDF | Extracting text from regulatory PDF documents |
| Frontend Framework | Next.js (React) | App Router based web dashboard |
| Styling | Tailwind CSS | Utility-first UI styling |
| Charts | Recharts | Data visualization (Risk, Regulators, Activity) |
| Real-time Updates | SSE (Server-Sent Events) | Streaming live scan progress to the frontend |
| Testing | pytest | Unit and integration testing |

## 5. LLM ARCHITECTURE
The system employs a strict Dual-LLM architecture:
- **Extraction LLM (Quarantined):** Receives the raw, untrusted web text. Its ONLY job is to extract factual data into JSON. It operates with a highly restrictive system prompt.
- **Privileged Analysis LLM:** NEVER sees the raw web text. It only receives the structurally and factually validated JSON output from the Extraction LLM, combined with the organization's internal profile.

**Why separate stages?**
To prevent indirect prompt injection. Untrusted web content must not be allowed to manipulate the risk assessment or compliance recommendations.

**Validation Principle:**
LLM PROPOSES → PYDANTIC VALIDATES → APPLICATION ACCEPTS/REJECTS. The LLM does not write to the database directly; it returns structured data that the application validates.

## 6. PROMPT INJECTION SECURITY
External web content is treated as **UNTRUSTED DATA**, not instructions. The system guards against indirect prompt injection where malicious text on a webpage attempts to hijack the LLM.

Implemented mechanisms:
- **Pattern Detection:** `security.py` scans for jailbreaks, data exfiltration attempts, and role hijacking using regex.
- **Quarantine:** Sources exceeding the suspicion threshold are blocked before reaching the LLM.
- **Separation of LLM stages:** (As described in LLM Architecture).
- **Evidence Verification:** Prevents the LLM from hallucinating claims inserted by attackers.

*Note: Regex does not completely prevent prompt injection, but serves as an early filter alongside the structural quarantine.*

## 7. PYDANTIC + STRUCTURED OUTPUT
All LLM output must strictly match predefined schemas (`models.py`).

**Important Models:**
- `RegulatoryExtraction`: The factual extraction (Title, Authority, Key Requirements).
- `ImpactAnalysis`: The privileged assessment (Gaps, Risk Level, Recommended Actions).
- `EvidenceDetail`: Links a claim to an exact source quote.

**Important Distinction:**
Pydantic validates *structure and types* (e.g., ensuring a date is a string, an array is a list). Evidence verification validates whether the *facts* (claims) are actually supported by the source text.

## 8. LIVE DATA
The primary pipeline uses **REAL live regulatory information**. 
DDGS executes actual search queries against the live internet. Actual HTML/PDF content is downloaded, parsed, and analyzed by the LLM. 

**NO fake regulatory data** is generated or used in the normal workflow. (Test fixtures exist only for testing/security validation).
Supported sources include authoritative domains (e.g., rbi.org.in, meity.gov.in, cert-in.org.in, sebi.gov.in, mca.gov.in).
Note the distinction: The system uses a primary search provider (DDGS) to discover documents across multiple regulatory sources.

## 9. EVIDENCE + VERIFICATION
Every regulatory claim is explicitly linked to the source:
`claim` → `source_quote` → `page_or_section` → `verification_status`

The system automatically verifies that the `source_quote` exactly matches a substring in the retrieved HTML/PDF. This prevents the LLM from hallucinating unsupported regulatory requirements.

## 10. IMPACT + RISK
- **Applicability:** The Privileged LLM assesses if the regulation applies to the specific bank profile.
- **Affected Processes:** Identifies specific banking processes (e.g., KYC/AML, Loan Underwriting).
- **Compliance Gaps:** Identifies potential gaps between the regulation and standard banking practice.
- **Risk Scoring:** Assigns deterministic risk levels (LOW, MEDIUM, HIGH, CRITICAL).
- **Uncertainty:** If public info is insufficient, the system uses safe defaults like `UNKNOWN — REQUIRES INTERNAL BANK REVIEW` instead of guessing or falsely declaring non-compliance.

## 11. HUMAN-IN-THE-LOOP
AI discovers and recommends; **Human reviews and approves/rejects.**
High and Critical risk findings generate pending reviews. A human compliance officer must explicitly approve or reject the AI's recommendations. Decisions, reviewers, and rationales are securely stored in the audit trail.

## 12. DATABASE
SQLite (`compliance.db`) is the persistent storage layer. 
Major tables:
- `scans`: Tracks pipeline scan executions.
- `scan_events`: Real-time granular logs for SSE streaming.
- `regulations`: The core table storing all extracted facts, impact analysis, and URLs.
- `security_events`: Logs of detected prompt injections and quarantined URLs.
- `audit_events`: System-level audit log.
- `reviews`: Pending and historical human review decisions.

## 13. FRONTEND
The frontend is a Next.js (App Router) React application. It uses REAL data fetched from the FastAPI backend (no hardcoded metrics).

Major pages/features:
- **Overview:** Dashboard with live metrics and charts (`/`).
- **Regulatory Updates:** Searchable grid of discovered regulations (`/regulations`).
- **Regulation Detail:** Deep dive into a specific regulation's extraction and impact (`/regulations/[id]`).
- **Risk & Compliance:** Risk distribution and gap analysis (`/risk`).
- **Evidence Explorer:** Traceability of claims to verbatim quotes (`/evidence`).
- **Security Monitor:** Logs of quarantined sites and injection attempts (`/security`).
- **Human Review:** Queue for approving/rejecting critical findings (`/review`).
- **Audit Trail:** Historical log of system and human actions (`/audit`).

## 14. REAL-TIME FLOW
1. **Frontend** initiates a scan via `POST /api/scans`.
2. **FastAPI** spawns a background pipeline thread and returns a `scan_id`.
3. The **pipeline** executes search, extraction, and analysis, inserting granular events into `scan_events`.
4. **Frontend** connects to `GET /api/scans/{scan_id}/events`.
5. **FastAPI** streams `scan_events` as Server-Sent Events (SSE).
6. **Frontend** refreshes the dashboard automatically when the scan completes.

## 15. API
Important FastAPI Endpoints (`api/main.py`):
- `GET /api/health`: System health check.
- `GET /api/dashboard/metrics`: High-level KPI aggregations.
- `GET /api/regulations`: Paginated list of regulatory updates.
- `GET /api/regulations/{id}`: Detailed view of a single regulation.
- `POST /api/scans`: Trigger a new live pipeline scan.
- `GET /api/scans/{scan_id}/events`: SSE endpoint for real-time progress.
- `POST /api/reviews/{id}/approve`: Approve a pending compliance action.
- `POST /api/reviews/{id}/reject`: Reject a pending compliance action.

## 16. PROJECT STRUCTURE
```
/
├── api/            # FastAPI backend (main.py, database.py, scanner.py)
├── frontend/       # Next.js web application (app/, components/)
├── pipeline/       # Core Python logic (search, security, LLMs, extraction)
├── reports/        # JSON fixtures for initial database seeding
├── tests/          # pytest unit tests
├── models.py       # Pydantic schemas shared across API and Pipeline
├── config.py       # Configuration and Environment Variables
└── startallservices.ps1 # Launcher script for all processes
```

## 17. HOW TO RUN
*(Requires Python, Node.js, and Ollama installed)*

**Quick Start (Windows):**
```powershell
# Starts Ollama, FastAPI, and Next.js in separate windows
.\startallservices.ps1
```

**Manual Execution:**
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Ollama (Ensure model is pulled: `ollama pull llama3.2:1b`)
ollama serve

# 3. Start Backend API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start Frontend
cd frontend
npm install
npm run dev

# 5. Run a manual scan (CLI)
python main.py --queries 2 --max-sources 3
```

## 18. IMPORTANT DEVELOPMENT RULES
1. Do not replace live regulatory data with fake/static data.
2. Do not hardcode dashboard metrics.
3. Do not expose API keys.
4. Treat external web content as untrusted.
5. Never allow raw external content to directly control privileged analysis.
6. Do not bypass Pydantic validation.
7. Do not fabricate evidence, dates, regulations, or compliance conclusions.
8. Preserve source traceability.
9. Keep AI recommendations subject to human review.
10. Do not unnecessarily rewrite working components.
11. Before modifying architecture, inspect the existing implementation.
12. Maintain the existing security boundaries.
13. Keep frontend and backend responsibilities separated.
14. If information is unavailable, represent it as UNKNOWN/REQUIRES REVIEW instead of guessing.
