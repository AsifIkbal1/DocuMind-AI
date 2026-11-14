import pytest
from backend.app.ai.extractor import ai_extraction_engine, HeuristicFallbackProvider


def test_ai_extraction_standard_invoice():
    sample_text = """
    TAX INVOICE
    Invoice Number: INV-2026-888
    Date: 2026-11-14
    Supplier: Cloud Services International
    Customer: Tech Innovators Inc.
    
    Description: Managed Kubernetes Cluster 1 $3,500.00 $3,500.00
    Description: 24/7 Enterprise Support 1 $1,500.00 $1,500.00
    
    Subtotal: 5000.00
    Tax: 500.00
    Total Amount: 5500.00 USD
    """

    schema, raw, provider = ai_extraction_engine.extract(sample_text)
    assert schema.invoice_number == "INV-2026-888"
    assert schema.invoice_date == "2026-11-14"
    assert schema.total_amount == 5500.00
    assert schema.subtotal == 5000.00
    assert schema.tax == 500.00
    assert schema.currency == "USD"
    assert len(schema.line_items) >= 2


def test_ai_extraction_missing_fields():
    incomplete_text = """
    Invoice: INV-999
    Only some partial text without date, supplier, or total amount.
    """
    schema, raw, provider = ai_extraction_engine.extract(incomplete_text)
    assert "invoice_date" in schema.missing_fields or schema.invoice_date is None
    assert schema.requires_manual_review is True


def test_ai_extraction_multiple_currencies():
    bdt_text = """
    INVOICE #INV-BDT-01
    Date: 2026-10-01
    Supplier: Dhaka Software Ltd
    Total Amount: ৳ 75,000.00 BDT
    """
    schema, raw, provider = ai_extraction_engine.extract(bdt_text)
    assert schema.currency == "BDT"
    assert schema.total_amount == 75000.00
