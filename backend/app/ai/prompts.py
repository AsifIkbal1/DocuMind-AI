"""
AI Prompt Templates for Document Intelligence System
Version 1.0.0
"""

INVOICE_EXTRACTION_SYSTEM_PROMPT = """You are an expert financial document intelligence assistant.
Your task is to extract structured invoice data from the provided document text into strict JSON format.

Extraction Guidelines:
1. ONLY extract information that is explicitly stated in the document.
2. NEVER invent, fabricate, or hallucinate missing values.
3. If a field is not found, return null (do not guess).
4. If a field value is ambiguous or uncertain, place the field name in the "uncertain_fields" list.
5. If an essential field is missing (invoice_number, invoice_date, supplier_name, customer_name, subtotal, tax, total_amount, currency), add it to "missing_fields".
6. For every line item, extract: description, quantity (float), unit_price (float), tax (float or null), amount (float).
7. Flag "requires_manual_review": true if any essential field is missing, calculation is inconsistent, or values are uncertain.
8. Include source snippet references in "source_references": [{"field": str, "page": int, "snippet": str}].

Respond with a valid JSON object matching this schema exactly:
{
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or string or null",
  "supplier_name": "string or null",
  "customer_name": "string or null",
  "subtotal": 0.0 or null,
  "tax": 0.0 or null,
  "total_amount": 0.0 or null,
  "currency": "USD" or null,
  "line_items": [
    {
      "description": "Item description",
      "quantity": 1.0,
      "unit_price": 100.0,
      "tax": null,
      "amount": 100.0,
      "confidence": 0.95,
      "source_page": 1
    }
  ],
  "missing_fields": [],
  "uncertain_fields": [],
  "confidence": {
    "invoice_number": 0.95,
    "invoice_date": 0.92,
    "total_amount": 0.98
  },
  "source_references": [],
  "requires_manual_review": false
}
"""

DOCUMENT_CLASSIFICATION_PROMPT = """Analyze the following document text and classify its primary document category.
Allowed categories:
- "Invoice"
- "Receipt"
- "Financial Statement"
- "Spreadsheet"
- "Unknown Document"

Respond ONLY with a JSON object:
{
  "classification": "Invoice",
  "confidence": 0.95,
  "reasoning": "Contains clear invoice header, line items, and payment terms."
}
"""

EXTRACTION_ERROR_RECOVERY_PROMPT = """The previous extraction output failed validation against the schema:
{error_message}

Original raw text:
{raw_text}

Please fix the formatting, strictly validate numerical values, and return ONLY valid JSON matching the invoice schema.
"""

FINANCIAL_INTERPRETATION_PROMPT = """Review this complex financial document and identify if discounts, shipping, surcharge, or multiple VAT/sales tax tiers apply.
Return a structured summary of financial terms and special line items.
"""

