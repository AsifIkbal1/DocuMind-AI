# DocuMind AI — Interactive REST API Documentation

The complete OpenAPI specification is interactively accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Below are documented endpoint details, schemas, and example API calls.

---

## 1. Document Upload
- **Method & Route**: `POST /api/documents/upload`
- **Content-Type**: `multipart/form-data`
- **Payload**: `files: List[UploadFile]` (PDF, JPG, PNG, TIFF, XLSX, XLS, CSV)
- **Example Request**:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "files=@sample_data/pdf/invoice_valid_001.pdf"
```
- **Example Response (HTTP 200)**:
```json
[
  {
    "id": "e285ebc6-993c-4e4b-91bb-fb02fba7b74f",
    "original_filename": "invoice_valid_001.pdf",
    "file_format": "pdf",
    "file_size": 2182,
    "file_hash": "a4d3f56b...",
    "upload_time": "2026-11-14T08:00:00Z",
    "processing_status": "Queued",
    "document_classification": "Unknown Document",
    "page_count": 1,
    "processing_duration": 0.0,
    "is_duplicate": false
  }
]
```

---

## 2. Processing Status
- **Method & Route**: `GET /api/documents/{document_id}/status`
- **Example Request**:
```bash
curl -X GET "http://localhost:8000/api/documents/e285ebc6-993c-4e4b-91bb-fb02fba7b74f/status"
```
- **Example Response (HTTP 200)**:
```json
{
  "document_id": "e285ebc6-993c-4e4b-91bb-fb02fba7b74f",
  "filename": "invoice_valid_001.pdf",
  "processing_status": "Completed",
  "job_progress": 100,
  "duration_seconds": 0.207,
  "error_information": null
}
```

---

## 3. Extracted Results
- **Method & Route**: `GET /api/documents/{document_id}/results`
- **Example Request**:
```bash
curl -X GET "http://localhost:8000/api/documents/e285ebc6-993c-4e4b-91bb-fb02fba7b74f/results"
```
- **Example Response (HTTP 200)**:
```json
{
  "id": "3bb62e92-3165-4f40-84a1-03004bb49b49",
  "document_id": "e285ebc6-993c-4e4b-91bb-fb02fba7b74f",
  "invoice_number": "INV-2026-001",
  "invoice_date": "2026-11-10",
  "supplier_name": "ABC Technologies Ltd.",
  "customer_name": "XYZ Corporation",
  "subtotal": 10000.0,
  "tax": 1500.0,
  "total_amount": 11500.0,
  "currency": "USD",
  "line_items": [
    {
      "description": "Cloud Hosting Infrastructure",
      "quantity": 2.0,
      "unit_price": 2500.0,
      "amount": 5000.0
    },
    {
      "description": "Database Clustering Engine",
      "quantity": 1.0,
      "unit_price": 5000.0,
      "amount": 5000.0
    }
  ],
  "missing_fields": [],
  "uncertain_fields": [],
  "confidence": {
    "invoice_number": 0.88,
    "invoice_date": 0.85,
    "total_amount": 0.90
  },
  "requires_manual_review": false,
  "is_corrected": false
}
```

---

## 4. Search (Hybrid & Semantic)
- **Method & Route**: `GET /api/search?q={query}&type={all|keyword|semantic}`
- **Example Request**:
```bash
curl -X GET "http://localhost:8000/api/search?q=ABC+Technologies&type=all"
```
- **Example Response (HTTP 200)**:
```json
{
  "query": "ABC Technologies",
  "search_type": "all",
  "total_results": 2,
  "results": [
    {
      "document_id": "e285ebc6-993c-4e4b-91bb-fb02fba7b74f",
      "filename": "invoice_valid_001.pdf",
      "document_type": "Invoice",
      "file_format": "pdf",
      "upload_time": "2026-11-14T08:00:00Z",
      "relevance_score": 0.942,
      "matched_by": "keyword",
      "snippet": "...Supplier: ABC Technologies Ltd. Customer: XYZ Corporation Total: 11500.00 USD...",
      "invoice_details": {
        "invoice_number": "INV-2026-001",
        "supplier_name": "ABC Technologies Ltd.",
        "total_amount": 11500.0,
        "currency": "USD"
      }
    }
  ]
}
```

---

## 5. Non-Destructive Manual Correction
- **Method & Route**: `PATCH /api/documents/{document_id}/corrections`
- **Payload**:
```json
{
  "field_name": "invoice_number",
  "corrected_value": "INV-2026-001-REV",
  "reason": "Corrected invoice sequence identifier",
  "reviewer_name": "Senior QA Auditor"
}
```
- **Example Response (HTTP 200)**:
```json
{
  "status": "success",
  "message": "Field 'invoice_number' successfully updated.",
  "field_name": "invoice_number",
  "original_value": "INV-2026-001",
  "corrected_value": "INV-2026-001-REV",
  "document_status": "Completed",
  "active_validation_issues_count": 0
}
```

---

## 6. PDF-to-PDF Cross-Verification
- **Method & Route**: `POST /api/verification/pdf-pdf`
- **Payload**:
```json
{
  "source_document_id": "e285ebc6-993c-4e4b-91bb-fb02fba7b74f",
  "target_document_id": "84a7e942-019a-4c22-bcf5-dc90aef92182"
}
```
- **Example Response (HTTP 200)**:
```json
{
  "id": "rep-48f9-4b61-9c88",
  "report_type": "PDF_PDF",
  "matching_score": 87.5,
  "status": "Needs Review",
  "summary": {
    "total_fields": 8,
    "matched_fields": 7,
    "mismatched_fields": 1
  },
  "items": [
    {
      "field_name": "Total Amount",
      "source_value": "11500.0",
      "target_value": "11500.0",
      "is_match": true,
      "severity": "Low"
    }
  ]
}
```

---

## 7. PDF-to-Excel Cross-Verification
- **Method & Route**: `POST /api/verification/pdf-excel`
- **Payload**:
```json
{
  "pdf_document_ids": ["e285ebc6-993c-4e4b-91bb-fb02fba7b74f"],
  "excel_document_id": "78ffbc10-33a2-4ea5-a223-99ab081829e1"
}
```
- **Example Response (HTTP 200)**:
```json
{
  "id": "rep-excel-9102",
  "report_type": "PDF_EXCEL",
  "matching_score": 100.0,
  "status": "Completed",
  "summary": {
    "total_pdf_invoices": 1,
    "total_excel_records": 5,
    "matched_records": 1,
    "missing_in_excel": 0,
    "missing_in_pdf": 4,
    "duplicate_excel_rows_count": 1
  }
}
```

---

## 8. Reprocess Failed Document
- **Method & Route**: `POST /api/documents/{document_id}/retry`
- **Example Request**:
```bash
curl -X POST "http://localhost:8000/api/documents/e285ebc6-993c-4e4b-91bb-fb02fba7b74f/retry"
```
- **Example Response (HTTP 200)**:
```json
{
  "status": "success",
  "message": "Processing queued for retry on 'invoice_valid_001.pdf'."
}
```
