# DocuMind AI — AI Prompts Architecture & System Disclosure

This document provides complete transparency into the artificial intelligence models, prompt engineering patterns, safety guidelines, and architectural boundaries implemented within **DocuMind AI**.

---

## 1. AI Provider Configuration & Selection Matrix

DocuMind AI implements a provider-agnostic AI extraction layer through an extensible interface (`backend/app/ai/extractor.py`).

| Provider | Model ID | Primary Use Case | Temperature | Fallback Priority |
|---|---|---|---|---|
| **Google Gemini** | `gemini-2.0-flash` | High-throughput document understanding, multimodal layout reasoning, fast structured JSON parsing | `0.1` | 1 (Default Cloud) |
| **OpenAI** | `gpt-4o` | Complex table parsing, multi-currency invoice extraction, ambiguous text structuring | `0.0` | 2 (Cloud Alternative) |
| **Heuristic Fallback** | `Local Regex + Spatial Engine` | Air-gapped deployments, zero API cost environments, offline CI/CD test suites, instant cold-starts | N/A | 3 (Automatic Fallback) |

### Environment Configuration
```bash
# Provider selection: "gemini", "openai", or "heuristic"
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# OpenAI alternative
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
```
*Note: If no API key is provided or cloud network access is restricted, DocuMind AI automatically falls back to the deterministic local Heuristic Engine without crashing or blocking document processing.*

---

## 2. Extraction System Prompts & Schemas

### Prompt 1: Invoice & Financial Document Extraction
Used by both Gemini and OpenAI providers to extract structured Pydantic data from OCR / text streams:

```markdown
You are an expert financial document intelligence system. Your objective is to extract key fields and tabular line items from the provided document text into strict, valid JSON matching the exact schema below.

CRITICAL INSTRUCTIONS:
1. Extract numerical values as floats or integers. Do NOT include currency symbols ($, €, £) in numeric fields.
2. If a field is not present or cannot be determined with certainty, set it to null.
3. For line items, extract every individual row itemized on the document with its description, quantity, unit price, and total amount.
4. If quantity or unit price is missing on a line item, default quantity to 1.0 and unit price to the line item amount.
5. Standardize dates to ISO 8601 format (YYYY-MM-DD) whenever possible.
6. Extract supplier tax ID / VAT registration if present.
7. Output ONLY the raw JSON object. Do not include markdown codeblocks or conversational preamble.

JSON SCHEMA:
{
  "invoice_number": "string or null",
  "supplier_name": "string or null",
  "supplier_address": "string or null",
  "supplier_tax_id": "string or null",
  "buyer_name": "string or null",
  "buyer_address": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "currency": "USD, EUR, GBP, or null",
  "subtotal": float or null,
  "tax_amount": float or null,
  "tax_rate": float or null,
  "total_amount": float or null,
  "payment_terms": "string or null",
  "line_items": [
    {
      "item_description": "string",
      "quantity": float,
      "unit_price": float,
      "amount": float
    }
  ]
}
```

---

### Prompt 2: Document Classification Prompt
Used for classifying un-indexed document streams when layout heuristics require multi-modal validation:

```markdown
You are a document classifier for an enterprise document management platform.
Examine the document text and categorize it into exactly one of the following classes:
- "Invoice"
- "Receipt"
- "Financial Statement"
- "Spreadsheet"
- "Unknown Document"

Provide a confidence score between 0.0 and 1.0 and a brief reason.

Output JSON format:
{
  "document_type": "Invoice",
  "confidence": 0.98,
  "reason": "Contains invoice header, line items, supplier information, and billing terms."
}
```

---

### Prompt 3: OCR Error Recovery & Character Disambiguation
Used when scanned text exhibits common optical recognition noise (e.g., `O` vs `0`, `l` vs `1`, missing decimal points in currency strings):

```markdown
Analyze the following noisy OCR text excerpt. Clean up obvious character recognition artifacts (e.g., '1nv-2O26-OO1' -> 'INV-2026-001', 'Total: $ 5,OOO.OO' -> '5000.00').
Preserve the original meaning and structure. Output only the cleaned text.
```

---

## 3. Clear Boundaries: AI vs. Deterministic Architecture

A fundamental design tenet of **DocuMind AI** is:
> **"Use AI for unstructured perception and parsing; use deterministic code for mathematics, validation, reconciliation, and audit security."**

To ensure 100% financial accuracy, audit compliance, and eliminate LLM hallucinations, the system strictly delineates responsibilities:

```
┌──────────────────────────────────────────────────────────────┐
│                    DOCUMENT INGESTION                        │
└──────────────────────────────┬───────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
       [ AI-POWERED LAYER ]          [ DETERMINISTIC LAYER ]
       - OCR Text Recognition        - File Size & MIME Verification
       - Multimodal Layout Parsing   - SHA-256 Checksum & Dedup
       - Unstructured Entity Extract - Table Extraction via pdfplumber
       - Semantic Cosine Embeddings  - Excel Multi-Sheet Parsing
               │                               │
               └───────────────┬───────────────┘
                               ▼
               ┌───────────────────────────────┐
               │ DETERMINISTIC ENGINE (NO AI)  │
               ├───────────────────────────────┤
               │ 1. Subtotal + Tax = Total     │
               │ 2. Qty * Price = Amount       │
               │ 3. Line Items Sum = Subtotal  │
               │ 4. Duplicate Invoice Check    │
               │ 5. Ledger Reconcile Diff = 0  │
               │ 6. Immutable Audit Trail      │
               └───────────────────────────────┘
```

### Detailed Functional Delineation

| System Function | Engine Type | Technology Stack | Rationale |
|---|---|---|---|
| **File Format & Size Validation** | Deterministic | Python `os`, MIME detection | Fast, secure rejection of malicious files |
| **Duplicate File Ingestion** | Deterministic | SHA-256 Hash Digest | Zero false positives in duplicate file detection |
| **PDF Text & Table Extraction** | Deterministic | `pdfplumber`, `pypdf` | High-fidelity character stream without hallucinations |
| **Scanned Image OCR** | Hybrid / AI | Tesseract + PIL Preprocessing | Best optical symbol recovery on degraded scans |
| **Field Extraction (Vendor, Dates)** | AI Layer | Gemini 2.0 / GPT-4o / Regex | High generalization across thousands of invoice templates |
| **Arithmetic Validation** | **Strict Deterministic** | Python `decimal` & `math` | LLMs cannot be trusted for financial math ($\pm0.01\$$ precision) |
| **Duplicate Invoice Detection** | **Strict Deterministic** | SQL Composite Index Check | Absolute certainty on invoice number, vendor, amount match |
| **PDF-to-PDF Verification** | **Strict Deterministic** | Exact String/Float Delta Match | Computes exact mathematical variances and match percentages |
| **PDF-to-Excel Reconciliation** | **Strict Deterministic** | Multi-key Join & Value Diff | Guarantees ERP general ledger audit compliance |
| **Semantic Natural Language Search** | AI / Vector | TF-IDF + Cosine Similarity | Enables conceptual retrieval without rigid keywords |
| **Manual Data Correction** | Deterministic | SQLAlchemy State Transaction | Non-destructive audit trail with immutable change log |

---

## 4. Hallucination Mitigation & Guardrails

1. **Schema Enforcement via Pydantic**: Every LLM response is parsed and validated against strict Pydantic schemas (`InvoiceExtractionSchema`). Malformed JSON triggers an automatic retry.
2. **Temperature Clamping**: Extraction models are pinned to `temperature: 0.1` (or `0.0` for OpenAI) to enforce deterministic, repeatable token generation.
3. **Zero-Math Reliance**: The LLM is instructed **never** to compute sums or infer missing math values. All calculations are evaluated independently by `backend/app/validators/validation_engine.py`.
4. **Audit Immutability**: All original extracted data is stored in `extracted_texts` and `invoices`. When manual corrections are made, they are recorded in `manual_corrections` without altering the initial AI extraction baseline, providing forensic transparency for enterprise auditors.
