# DocuMind AI — Database Architecture & Entity Specifications

## 1. Relational Schema Design
DocuMind AI utilizes a normalized relational architecture (PostgreSQL in containerized production with pgvector; SQLite in local standalone development) implemented via SQLAlchemy 2.0 ORM.

### Entity Relationship Diagram (ERD)

```
       [ Users ] ──────────────< [ ManualCorrections ] >──────────┐
          │                                                       │
          └───────────────────< [ AuditLogs ]                     │
                                                                  │
                                                                  ▼
 [ Documents ] ──────────1:1──────────> [ Invoices ] ──1:N──> [ LineItems ]
       │                                       │
       ├──1:N──> [ DocumentPages ]             └──1:N──> [ ValidationResults ]
       ├──1:1──> [ ExtractedTexts ]
       ├──1:N──> [ ProcessingJobs ]
       └──1:N──> [ ProcessingHistories ]

 [ VerificationReports ] ──1:N──> [ VerificationItems ]
```

---

## 2. Table Definitions

### 1. `users`
- `id` (VARCHAR(36), PK): UUID identifier
- `email` (VARCHAR(255), UNIQUE, INDEX): Login email
- `hashed_password` (VARCHAR(255)): Bcrypt password hash
- `full_name` (VARCHAR(255)): Display name
- `role` (VARCHAR(50)): `admin`, `reviewer`, `viewer`
- `is_active` (BOOLEAN): Status flag
- `created_at` (DATETIME)

### 2. `documents`
- `id` (VARCHAR(36), PK): UUID
- `original_filename` (VARCHAR(255), INDEX)
- `file_format` (VARCHAR(20), INDEX): pdf, png, jpg, tiff, xlsx, xls, csv
- `file_size` (INTEGER): Bytes
- `file_hash` (VARCHAR(64), INDEX): SHA-256 hash
- `upload_time` (DATETIME, INDEX)
- `processing_status` (VARCHAR(50), INDEX): Uploaded, Queued, Processing, OCR Processing, AI Extraction, Validation, Completed, Failed, Needs Review
- `file_storage_reference` (VARCHAR(512)): Absolute local or cloud object storage path
- `document_classification` (VARCHAR(50), INDEX): Invoice, Receipt, Financial Statement, Spreadsheet, Unknown Document
- `page_count` (INTEGER)
- `processing_duration` (FLOAT): Seconds
- `error_information` (TEXT)
- `is_duplicate` (BOOLEAN): Duplicate detection flag
- `duplicate_of_id` (VARCHAR(36)): Reference to original document

### 3. `document_pages`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE)
- `page_number` (INTEGER)
- `raw_text` (TEXT)
- `ocr_applied` (BOOLEAN)
- `ocr_confidence` (FLOAT)
- `is_empty` (BOOLEAN)
- `image_path` (VARCHAR(512))

### 4. `extracted_texts`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE, UNIQUE)
- `raw_text` (TEXT)
- `normalized_text` (TEXT)
- `page_count` (INTEGER)
- `extraction_method` (VARCHAR(50)): digital, ocr, spreadsheet, hybrid
- `created_at` (DATETIME)

### 5. `invoices`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE, UNIQUE)
- `invoice_number` (VARCHAR(100), INDEX)
- `invoice_date` (VARCHAR(50), INDEX)
- `supplier_name` (VARCHAR(255), INDEX)
- `customer_name` (VARCHAR(255), INDEX)
- `subtotal` (FLOAT)
- `tax` (FLOAT)
- `total_amount` (FLOAT, INDEX)
- `currency` (VARCHAR(20), INDEX)
- `raw_ai_response` (JSON)
- `confidence_scores` (JSON)
- `missing_fields` (JSON)
- `uncertain_fields` (JSON)
- `source_references` (JSON)
- `requires_manual_review` (BOOLEAN, INDEX)
- `is_corrected` (BOOLEAN)
- `embedding` (JSON): Vector embedding
- `created_at` (DATETIME)
- `updated_at` (DATETIME)

### 6. `invoice_line_items`
- `id` (VARCHAR(36), PK)
- `invoice_id` (VARCHAR(36), FK -> invoices.id ON DELETE CASCADE)
- `item_order` (INTEGER)
- `description` (TEXT)
- `quantity` (FLOAT)
- `unit_price` (FLOAT)
- `tax` (FLOAT)
- `amount` (FLOAT)
- `confidence` (FLOAT)
- `source_page` (INTEGER)

### 7. `validation_results`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE)
- `invoice_id` (VARCHAR(36), FK -> invoices.id ON DELETE CASCADE)
- `validation_type` (VARCHAR(100)): MISSING_FIELD, CALCULATION_MISMATCH, EXACT_DUPLICATE_INVOICE, POTENTIAL_DUPLICATE_INVOICE, LINE_ITEM_ARITHMETIC, LINE_ITEMS_SUBTOTAL_MISMATCH
- `field_name` (VARCHAR(100))
- `expected_value` (VARCHAR(255))
- `actual_value` (VARCHAR(255))
- `difference` (VARCHAR(255))
- `severity` (VARCHAR(20), INDEX): Critical, High, Medium, Low
- `description` (TEXT)
- `status` (VARCHAR(50), INDEX): Pending, Resolved, Ignored
- `created_timestamp` (DATETIME)

### 8. `verification_reports`
- `id` (VARCHAR(36), PK)
- `report_type` (VARCHAR(50)): PDF_PDF, PDF_EXCEL
- `source_document_id` (VARCHAR(36))
- `target_document_id` (VARCHAR(36))
- `matching_score` (FLOAT): 0 - 100%
- `status` (VARCHAR(50)): Completed, Needs Review
- `summary` (JSON)
- `created_at` (DATETIME)

### 9. `verification_items`
- `id` (VARCHAR(36), PK)
- `report_id` (VARCHAR(36), FK -> verification_reports.id ON DELETE CASCADE)
- `field_name` (VARCHAR(100))
- `source_value` (VARCHAR(500))
- `target_value` (VARCHAR(500))
- `is_match` (BOOLEAN)
- `discrepancy_type` (VARCHAR(100))
- `severity` (VARCHAR(20))
- `notes` (TEXT)

### 10. `processing_jobs`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE)
- `job_type` (VARCHAR(100)): PIPELINE_FULL, OCR_ONLY, AI_EXTRACTION, VALIDATION
- `status` (VARCHAR(50), INDEX): Queued, Processing, Completed, Failed, Retrying
- `progress` (INTEGER): 0 - 100%
- `error_message` (TEXT)
- `started_at` (DATETIME)
- `completed_at` (DATETIME)
- `duration_seconds` (FLOAT)

### 11. `processing_histories`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE)
- `stage` (VARCHAR(100))
- `status` (VARCHAR(50))
- `message` (TEXT)
- `details` (JSON)
- `timestamp` (DATETIME)

### 12. `manual_corrections`
- `id` (VARCHAR(36), PK)
- `document_id` (VARCHAR(36), FK -> documents.id ON DELETE CASCADE)
- `invoice_id` (VARCHAR(36), FK -> invoices.id ON DELETE CASCADE)
- `field_name` (VARCHAR(100))
- `original_value` (TEXT)
- `corrected_value` (TEXT)
- `reason` (TEXT)
- `reviewer_name` (VARCHAR(255))
- `timestamp` (DATETIME)

### 13. `audit_logs`
- `id` (VARCHAR(36), PK)
- `action` (VARCHAR(100), INDEX): UPLOAD, PROCESS_DOCUMENT, CORRECT_FIELD, VERIFY, LOGIN
- `entity_type` (VARCHAR(50), INDEX)
- `entity_id` (VARCHAR(36), INDEX)
- `user_email` (VARCHAR(255))
- `details` (JSON)
- `timestamp` (DATETIME)
