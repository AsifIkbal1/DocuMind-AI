# DocuMind AI — Enterprise AI-Powered Document Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-38B2AC.svg)](https://tailwindcss.com/)
[![Tests Passing](https://img.shields.io/badge/Tests-22%2F22%20Passing-brightgreen.svg)](docs/testing_report.md)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](docker-compose.yml)

**DocuMind AI** is an enterprise-grade, end-to-end Intelligent Document Processing (IDP), AI Information Extraction, Deterministic Financial Validation, and Automated Ledger Reconciliation platform. Designed to process digital PDFs, scanned documents, low-resolution receipts, multi-sheet Excel spreadsheets, and CSV ledgers with zero mathematical hallucinations, non-destructive human-in-the-loop review, and immutable audit logging.

---

## Table of Contents
1. [Key Features](#key-features)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Prerequisites & Quick Start](#prerequisites--quick-start)
5. [Docker Compose Deployment](#docker-compose-deployment)
6. [Automated Testing & Benchmark Results](#automated-testing--benchmark-results)
7. [API Documentation & Swagger UI](#api-documentation--swagger-ui)
8. [Frontend SaaS Interface](#frontend-saas-interface)
9. [Project Directory Layout](#project-directory-layout)
10. [AI Model Configuration & Prompts](#ai-model-configuration--prompts)
11. [Troubleshooting Guide](#troubleshooting-guide)

---

## Key Features

- **Multi-Format Ingestion Engine**:
  - Streams digital PDFs page-by-page (scalable to 1,000+ pages without memory bottlenecks).
  - Computer vision preprocessing (grayscale, contrast auto-balancing, median denoising, unsharp mask).
  - Optical Character Recognition (OCR) with confidence scoring.
  - Multi-sheet Excel (`.xlsx`, `.xls`) and CSV ingestion with automatic header normalization and intra-sheet duplicate row detection.
  - Multi-signal document classifier (`Invoice`, `Receipt`, `Financial Statement`, `Spreadsheet`, `Unknown Document`).
- **AI-Powered Information Extraction**:
  - Modular AI provider architecture supporting **Google Gemini 2.0 Flash**, **OpenAI GPT-4o**, and an offline **Heuristic Regex/Layout Fallback Engine**.
  - Pydantic schema validation for invoices: invoice number, supplier details, tax IDs, buyer details, dates, currency, line items, subtotals, tax rates, and total amounts.
- **Deterministic Financial Validation Engine (Zero-Hallucination Math)**:
  - Line-item verification ($\text{Quantity} \times \text{Unit Price} = \text{Amount}$ with $\pm0.01$ tolerance).
  - Invoice total reconciliation ($\sum \text{Line Items} = \text{Subtotal}$, $\text{Subtotal} + \text{Tax} = \text{Total}$).
  - Multi-factor duplicate invoice detection across invoice number, supplier name, date, and amount.
  - Severity-tiered validation flags (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`).
- **Automated Document Verification & Reconciliation**:
  - **PDF-to-PDF**: Side-by-side revision diff highlighting changes in header metadata and itemized line totals with confidence scores.
  - **PDF-to-Excel**: Automated reconciliation of invoice PDFs against general ledger spreadsheets and bank payment statements.
- **Non-Destructive Human-in-the-Loop Review**:
  - Full audit logging of manual edits without overwriting original raw OCR extracts.
  - Tracks editor identity, timestamp, prior value, corrected value, and business rationale.
- **Hybrid Keyword & Semantic Vector Search**:
  - Combines structured SQL filters (supplier, date range, amount) with TF-IDF cosine similarity vector retrieval across extracted text bodies.
- **Real-Time Job Queue & State Machine**:
  - Asynchronous background execution via Celery / FastAPI background tasks with step milestones, error recovery, and retry controls.

---

## System Architecture

```
                                 ┌─────────────────────────┐
                                 │   Next.js 14 Frontend   │
                                 │   (Tailwind / Recharts) │
                                 └────────────┬────────────┘
                                              │ REST API / JSON
                                              ▼
                                 ┌─────────────────────────┐
                                 │    FastAPI REST Engine  │
                                 │   (OpenAPI 3.0 / JWT)   │
                                 └────────────┬────────────┘
                                              │
         ┌────────────────────────────────────┼────────────────────────────────────┐
         │                                    │                                    │
         ▼                                    ▼                                    ▼
┌──────────────────┐               ┌──────────────────────┐              ┌──────────────────┐
│ Ingestion Layer  │               │ AI Extraction Engine │              │ Validation & Rec │
├──────────────────┤               ├──────────────────────┤              ├──────────────────┤
│ - pdfplumber     │               │ - Gemini 2.0 Flash   │              │ - Deterministic  │
│ - Tesseract OCR  │               │ - OpenAI GPT-4o      │              │   Math Checks    │
│ - openpyxl / CSV │               │ - Local Heuristic    │              │ - Duplicate Clust│
│ - OpenCV / PIL   │               │ - Pydantic Schema    │              │ - Ledger Reconcil│
└────────┬─────────┘               └──────────┬───────────┘              └────────┬─────────┘
         │                                    │                                   │
         └────────────────────────────────────┼───────────────────────────────────┘
                                              │
                                              ▼
                               ┌─────────────────────────────┐
                               │     Storage & Audit Trail   │
                               ├─────────────────────────────┤
                               │ - PostgreSQL / SQLite DB    │
                               │ - 13 Core Relational Models │
                               │ - SHA-256 File Vault        │
                               │ - Immutable AuditLog Table  │
                               └─────────────────────────────┘
```

---

## Technology Stack

- **Backend**: Python 3.11 - 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0, Celery, Uvicorn, Bcrypt.
- **Document Processing**: `pdfplumber`, `pypdf`, `pypdfium2`, `openpyxl`, `pillow`, `pytesseract`.
- **AI & ML**: Google Generative AI (Gemini), OpenAI API, scikit-learn (TF-IDF vectorizer & cosine similarity).
- **Database**: PostgreSQL 16 (production) / SQLite 3 (lightweight local/testing mode).
- **Frontend**: Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, Lucide React, Recharts.
- **DevOps**: Docker, Docker Compose, Multi-stage builds, Gunicorn.

---

## Prerequisites & Quick Start

### 1. System Requirements
- Python 3.11, 3.12, or 3.13
- Node.js 18+ and npm 9+
- (Optional) Docker & Docker Compose for containerized execution.

### 2. Environment Configuration
Copy the environment template and configure as needed:
```bash
cp .env.example .env
```
Default parameters run completely offline out-of-the-box using the local SQLite database and Heuristic Extraction Engine (no cloud API keys strictly required to test all features).

---

### 3. Backend Setup & Startup

```bash
# 1. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Seed demo data (creates admin account and processes sample documents)
python scripts/seed_demo_data.py

# 4. Start the FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend API is now accessible at `http://localhost:8000`. Interactive documentation: `http://localhost:8000/docs`.

**Default Admin Credentials**:
- **Email**: `admin@documind.ai`
- **Password**: `AdminPass2026!`

---

### 4. Frontend Setup & Startup

In a new terminal window:
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Build for production or start development server
npm run dev
```
Open your browser at `http://localhost:3000`.

---

## Docker Compose Deployment

To launch the complete DocuMind AI stack (PostgreSQL database, Redis queue, FastAPI backend, and Next.js frontend) with a single command:

```bash
docker compose up --build
```

- **Frontend**: `http://localhost:3000`
- **Backend API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`

To stop the services:
```bash
docker compose down
```

---

## Automated Testing & Benchmark Results

### Automated Unit & Integration Tests
DocuMind AI includes a rigorous automated test suite covering document processing, AI extraction fallback, deterministic validation math, reconciliation verification, and REST API endpoints.

To run the test suite:
```bash
source venv/bin/activate
PYTHONPATH=. pytest backend/tests/ -v
```

**Test Results Summary**:
- **Total Test Cases**: 22
- **Passing**: 22 (100% pass rate)
- **Execution Time**: ~1.27 seconds
- Detailed report: [docs/testing_report.md](file:///Users/apple/Downloads/DocuMind%20AI/docs/testing_report.md)

---

### Ground-Truth Evaluation Benchmark
DocuMind AI was evaluated against a labeled evaluation dataset (`sample_data/ground_truth.json`) containing native invoices, scanned receipts, mathematical calculation errors, multi-sheet ledgers, and duplicate submissions.

To run the evaluation script:
```bash
source venv/bin/activate
python scripts/run_evaluation.py
```

**Measured Benchmark Metrics**:
```json
{
  "total_documents_evaluated": 7,
  "successful_extractions": 7,
  "processing_success_rate": 100.0,
  "average_processing_time_sec": 0.222,
  "validation_rules_evaluated": 7,
  "calculation_error_detection_rate": 100.0,
  "duplicate_detection_rate": 100.0,
  "verification_matching_accuracy": 100.0
}
```
Detailed evaluation report: [docs/evaluation_report.md](file:///Users/apple/Downloads/DocuMind%20AI/docs/evaluation_report.md)

---

## API Documentation & Swagger UI

Interactive OpenAPI / Swagger documentation is automatically hosted at `http://localhost:8000/docs`.

### Key Endpoints

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/api/health` | System health, database connection, AI provider readiness |
| **Authentication** | `POST` | `/api/auth/login` | OAuth2 form login returning JWT access token |
| | `POST` | `/api/auth/register` | Register new user organization account |
| **Documents** | `POST` | `/api/documents/upload` | Multipart file upload (PDF, Excel, Images, CSV) |
| | `GET` | `/api/documents/` | Paginated document listing with status/format filtering |
| | `GET` | `/api/documents/{id}` | Complete document details, pages, and metadata |
| | `GET` | `/api/documents/{id}/results` | Structured invoice extraction results & line items |
| | `GET` | `/api/documents/{id}/validation` | Deterministic validation flags and arithmetic errors |
| | `PATCH` | `/api/documents/{id}/corrections` | Non-destructive manual correction with audit logging |
| | `POST` | `/api/documents/{id}/retry` | Re-queue and re-process failed/flagged documents |
| **Verification** | `POST` | `/api/verification/pdf-pdf` | Side-by-side diff comparison between two PDF documents |
| | `POST` | `/api/verification/pdf-excel` | Automated reconciliation between PDF invoice and Excel ledger |
| | `GET` | `/api/verification/history` | Historical verification and reconciliation reports |
| **Search** | `POST` | `/api/search/` | Hybrid structured keyword and TF-IDF semantic vector search |
| **Jobs** | `GET` | `/api/jobs/` | Background worker queue monitoring and progress metrics |
| **Analytics** | `GET` | `/api/analytics/overview` | Platform-wide KPIs, format distributions, processing velocity |
| | `GET` | `/api/analytics/export` | Download operational processing audit log as CSV |

Complete endpoint specifications: [docs/api_documentation.md](file:///Users/apple/Downloads/DocuMind%20AI/docs/api_documentation.md).

---

## Frontend SaaS Interface

The Next.js 14 frontend provides 10+ responsive views built with modern design principles:
- **Executive Dashboard** (`/dashboard`): Real-time metrics, throughput charts, format breakdown.
- **Document Center** (`/documents`): Drag-and-drop upload, status filtering, batch actions.
- **Document Details** (`/documents/[id]`): Multi-tab viewer (Extracted Invoice, Validation, Raw Pages/OCR, Audit Trail).
- **AI Extraction Center** (`/extraction`): Field inspector with inline editing and recalculation.
- **Deterministic Validation Center** (`/validation`): Severity filterable math anomalies, duplicate alerts.
- **Verification & Reconciliation Hub** (`/verification`): PDF-to-PDF comparison and PDF-to-Excel ledger matching.
- **Hybrid Search Engine** (`/search`): Natural language semantic vector search and structured filtering.
- **Background Jobs Queue** (`/jobs`): Active job progress tracking and failure diagnostics.
- **Operational Analytics** (`/analytics`): System throughput trends and CSV export.
- **System Settings** (`/settings`): AI provider selection, model configuration, and environment diagnostics.

---

## Project Directory Layout

```
DocuMind AI/
├── backend/
│   ├── app/
│   │   ├── ai/               # AI Extractor (Gemini, OpenAI, Heuristic fallback)
│   │   ├── api/              # REST Endpoints (auth, docs, verification, search, jobs, analytics)
│   │   ├── core/             # Configuration, settings, security, logging
│   │   ├── database/         # Session factory, connection pooling, base models
│   │   ├── models/           # 13 SQLAlchemy database entities
│   │   ├── ocr/              # Tesseract OCR engine & image preprocessing
│   │   ├── processors/       # PDF, Excel, CSV, classifier, normalizer, validator
│   │   ├── schemas/          # Pydantic schemas (request/response validation)
│   │   ├── search/           # TF-IDF vectorizer + Cosine similarity search engine
│   │   ├── services/         # 12-stage document processing pipeline orchestrator
│   │   ├── tasks/            # Celery worker & background job tasks
│   │   ├── validators/       # Deterministic financial validation engine
│   │   ├── verification/     # PDF-to-PDF diff and PDF-to-Excel reconciliation
│   │   └── main.py           # FastAPI application entrypoint
│   ├── tests/                # 22 automated Pytest unit and integration tests
│   ├── Dockerfile            # Multi-stage production backend container
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── app/                  # Next.js 14 App Router pages (10+ views)
│   ├── components/           # Reusable UI widgets (Navbar, Sidebar, Badges, Cards)
│   ├── lib/                  # API client, TypeScript interfaces, utilities
│   ├── public/               # Static assets and icons
│   ├── Dockerfile            # Multi-stage production frontend container
│   └── package.json          # Node dependencies & Next.js scripts
├── docs/
│   ├── architecture.md       # High-level architecture & pipeline lifecycle
│   ├── database_schema.md    # Database ERD, 13 entities, indexing strategy
│   ├── api_documentation.md  # Detailed REST API endpoint specification
│   ├── testing_report.md     # Pytest test execution results
│   ├── evaluation_report.md  # Ground-truth evaluation metrics
│   ├── walkthrough.md        # 12-step recorded presentation script
│   └── ai_prompts_disclosure.md # AI prompts, schemas, and AI vs Deterministic disclosure
├── sample_data/              # Test documents (PDF, Excel, Images, CSV, Ground Truth)
├── scripts/
│   ├── run_evaluation.py     # Evaluation runner calculating real metrics
│   └── seed_demo_data.py     # Database seeder for demo environment
├── docker-compose.yml        # Multi-container orchestration (DB, Redis, Backend, Frontend)
├── DEVELOPMENT_STATUS.md     # Master task implementation tracking checklist
├── .env.example              # Environment variables template
└── README.md                 # Master documentation
```

---

## AI Model Configuration & Prompts

DocuMind AI strictly enforces that **AI models are utilized solely for unstructured data perception and schema extraction**, while **all calculations, verifications, and duplicate checks are executed by deterministic code**.

Complete system prompts, error-recovery instructions, and architectural boundaries are documented in:
[docs/ai_prompts_disclosure.md](file:///Users/apple/Downloads/DocuMind%20AI/docs/ai_prompts_disclosure.md).

---

## Troubleshooting Guide

### 1. Database Connection Issues
- **Symptom**: `OperationalError: unable to open database file`
- **Solution**: Ensure the `storage/` directory exists with write permissions:
  ```bash
  mkdir -p storage && chmod 755 storage
  ```

### 2. Missing Tesseract OCR Binary
- **Symptom**: `TesseractNotFound` or OCR warnings in logs.
- **Solution**: DocuMind AI automatically falls back to layout-guided heuristic OCR. To enable native Tesseract:
  - macOS: `brew install tesseract`
  - Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr`

### 3. Frontend Cannot Connect to Backend
- **Symptom**: Network error or CORS errors in browser console.
- **Solution**: Verify `NEXT_PUBLIC_API_URL` in `frontend/.env.local` points to `http://localhost:8000/api`. Verify backend is running and `CORS_ORIGINS` in `.env` includes `http://localhost:3000`.

---

## License & Compliance

Developed as an enterprise-grade reference implementation for AI-Powered Document Intelligence, automated ledger reconciliation, and deterministic data integrity. All rights reserved.
