# DocuMind AI — System Architecture & Workflow Specifications

## 1. System Overview
DocuMind AI is an enterprise-grade, full-stack AI Document Intelligence platform engineered to automate multi-format financial document ingestion, structured information extraction, deterministic calculation verification, and cross-reconciliation between PDF invoices and spreadsheet ledgers.

```
                                  [ Client Browser / Next.js SaaS ]
                                                 │
                                                 ▼ (HTTP REST / JSON / Multipart)
                                     [ FastAPI Gateway (Port 8000) ]
                                                 │
                   ┌─────────────────────────────┼─────────────────────────────┐
                   ▼                             ▼                             ▼
         [ Document Ingestion ]         [ Verification Engine ]        [ Hybrid Search ]
         - SHA-256 Hashing              - PDF-to-PDF Matrix            - Keyword Full-Text
         - MIME Magic Validation        - PDF-to-Excel Ledger Match    - Cosine Vector TF-IDF
         - Stream Page Splitter         - Duplicate Row Detector       - Metadata Range Filters
                   │                             │                             │
                   ▼                             │                             ▼
        [ Processing Pipeline ]                  │                     [ Database & Cache ]
   ┌───────────────────────────────┐             │                     - SQLite / PostgreSQL
   │ 1. Text Extraction (fitz/pdf) │             │                     - 13 Normalized Tables
   │ 2. Scanned Page Fallback OCR  │             │                     - Redis Job Broker
   │ 3. Multi-sheet Spreadsheet    │             │                     - Celery Concurrency (4)
   │ 4. Normalization (NFKC, regex)│             │                             ▲
   │ 5. Document Classifier        │             │                             │
   │ 6. AI Extraction (Gemini/OAI) │─────────────┴─────────────────────────────┘
   │ 7. Deterministic Validation   │
   │ 8. Search Vector Indexing     │
   └───────────────────────────────┘
```

---

## 2. Processing Workflow
1. **Upload & Ingestion**:
   - Accepts multi-file payload (`.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`, `.xlsx`, `.xls`, `.csv`).
   - Validates file size (limit 50 MB) and header magic bytes.
   - Computes SHA-256 hash to detect exact duplicate document uploads immediately.
2. **Text Extraction & Hybrid OCR**:
   - Digital PDFs are parsed with page-by-page streaming to support large documents (up to 1,000 pages) without high memory overhead.
   - If a page has low text density (< 15 characters), page rendering renders the canvas to a 150 DPI image and applies image preprocessing (grayscale, contrast boost, median filter noise reduction) and OCR.
   - Spreadsheets (XLSX, XLS, CSV) parse all worksheets, detect header synonyms, and track row/sheet coordinates.
3. **Classification & Normalization**:
   - Multi-signal classifier assigns documents to `Invoice`, `Receipt`, `Financial Statement`, `Spreadsheet`, or `Unknown Document`.
   - Normalizer applies Unicode NFKC cleaning, removes excess whitespaces, and normalizes currency symbols ($ € £ ৳ ₹).
4. **AI Information Extraction**:
   - Modular AI provider layer supports Google Gemini (`gemini-2.0-flash`), OpenAI (`gpt-4o`), and an offline Heuristic Extractor.
   - Strict Pydantic JSON schema validation ensures no hallucinated keys and populates field confidence scores, missing fields, and uncertain fields.
5. **Deterministic Validation Engine**:
   - Runs independent mathematical checks:
     - $\text{Subtotal} + \text{Tax} = \text{Total Amount} \pm \text{Tolerance}$
     - $\text{Quantity} \times \text{Unit Price} = \text{Line Item Amount}$
     - $\sum \text{Line Items} = \text{Subtotal}$
   - Normalizes invoice number, vendor name, and date to flag exact and potential duplicate invoices.
   - Assigns severity scores: `Critical`, `High`, `Medium`, and `Low`.
6. **Cross-Verification Engine**:
   - **PDF-to-PDF**: Side-by-side field differential matrix and similarity score.
   - **PDF-to-Excel**: Automated reconciliation of PDF batches against Excel ledgers, highlighting missing rows in either file, duplicate rows, and amount variances.
7. **Storage & Search Indexing**:
   - Persists all results across 13 relational tables.
   - Automatically builds vector space representation for instant keyword and semantic natural-language retrieval.
