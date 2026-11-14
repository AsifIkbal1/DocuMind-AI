import re
from typing import Dict, Any, Optional


class DocumentClassifier:
    """
    Classifies documents into:
    - Invoice
    - Receipt
    - Financial Statement
    - Spreadsheet
    - Unknown Document

    Uses multi-signal classification: file format + content heuristics + regex token analysis.
    """

    INVOICE_KEYWORDS = [
        "invoice", "tax invoice", "bill to", "invoice number", "invoice no",
        "remit to", "due date", "subtotal", "terms of payment", "balance due"
    ]
    RECEIPT_KEYWORDS = [
        "receipt", "sales receipt", "cash receipt", "payment receipt",
        "tender", "change due", "store #", "register #", "cashier", "terminal #"
    ]
    FINANCIAL_STATEMENT_KEYWORDS = [
        "balance sheet", "income statement", "cash flow statement", "profit and loss",
        "assets", "liabilities", "equity", "retained earnings", "fiscal year",
        "quarterly report", "annual report"
    ]

    def classify(
        self,
        file_format: str,
        text_content: str,
        extracted_tables_count: int = 0
    ) -> str:
        # Check spreadsheet file types directly
        if file_format in ("xlsx", "xls", "csv"):
            return "Spreadsheet"

        clean_text = text_content.lower()

        # Score matching categories
        invoice_score = sum(1 for kw in self.INVOICE_KEYWORDS if kw in clean_text)
        receipt_score = sum(1 for kw in self.RECEIPT_KEYWORDS if kw in clean_text)
        statement_score = sum(1 for kw in self.FINANCIAL_STATEMENT_KEYWORDS if kw in clean_text)

        # Invoices typically have line items and terms
        if invoice_score >= 2 and invoice_score >= receipt_score and invoice_score >= statement_score:
            return "Invoice"

        if receipt_score >= 2 and receipt_score > invoice_score:
            return "Receipt"

        if statement_score >= 2:
            return "Financial Statement"

        # Check for single strong signals
        if "invoice" in clean_text or "bill to" in clean_text:
            return "Invoice"
        if "receipt" in clean_text or "cashier" in clean_text:
            return "Receipt"
        if "balance sheet" in clean_text or "profit and loss" in clean_text:
            return "Financial Statement"

        return "Unknown Document"


document_classifier = DocumentClassifier()

