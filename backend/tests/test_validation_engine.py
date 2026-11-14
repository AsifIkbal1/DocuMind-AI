import pytest
from backend.app.models.entities import Invoice, InvoiceLineItem, Document
from backend.app.validators.validation_engine import data_validation_engine


def test_validation_detects_math_mismatch(db_session):
    doc = Document(
        original_filename="test_math.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="hash_test_math",
        file_storage_reference="dummy_path",
    )
    db_session.add(doc)
    db_session.flush()

    # Subtotal 5000 + Tax 500 = 5500, but Total is 6200
    inv = Invoice(
        document_id=doc.id,
        invoice_number="INV-MATH-ERR",
        invoice_date="2026-11-10",
        supplier_name="Math Test Vendor",
        subtotal=5000.00,
        tax=500.00,
        total_amount=6200.00,
        currency="USD",
    )
    db_session.add(inv)
    db_session.flush()

    results = data_validation_engine.run_all_validations(inv, doc, db_session)
    types = [r.validation_type for r in results]
    assert "CALCULATION_MISMATCH" in types
    assert doc.processing_status == "Needs Review"


def test_validation_detects_missing_fields(db_session):
    doc = Document(
        original_filename="test_missing.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="hash_missing",
        file_storage_reference="dummy_path",
    )
    db_session.add(doc)
    db_session.flush()

    # Missing supplier and missing date
    inv = Invoice(
        document_id=doc.id,
        invoice_number=None,
        invoice_date=None,
        supplier_name=None,
        total_amount=100.00,
    )
    db_session.add(inv)
    db_session.flush()

    results = data_validation_engine.run_all_validations(inv, doc, db_session)
    missing_fields = [r.field_name for r in results if r.validation_type == "MISSING_FIELD"]
    assert "invoice_number" in missing_fields
    assert "invoice_date" in missing_fields
    assert "supplier_name" in missing_fields


def test_validation_detects_exact_duplicate(db_session):
    # Existing invoice
    doc1 = Document(
        original_filename="original.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="hash1",
        file_storage_reference="p1",
    )
    db_session.add(doc1)
    db_session.flush()

    inv1 = Invoice(
        document_id=doc1.id,
        invoice_number="INV-DUP-100",
        invoice_date="2026-11-10",
        supplier_name="Same Vendor Corp",
        subtotal=1000.00,
        tax=100.00,
        total_amount=1100.00,
    )
    db_session.add(inv1)
    db_session.commit()

    # New duplicate invoice
    doc2 = Document(
        original_filename="duplicate.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="hash2",
        file_storage_reference="p2",
    )
    db_session.add(doc2)
    db_session.flush()

    inv2 = Invoice(
        document_id=doc2.id,
        invoice_number="inv-dup-100",  # lowercase
        invoice_date="2026-11-10",
        supplier_name="Same Vendor Corp.",  # slight punctuation diff
        subtotal=1000.00,
        tax=100.00,
        total_amount=1100.00,
    )
    db_session.add(inv2)
    db_session.flush()

    results = data_validation_engine.run_all_validations(inv2, doc2, db_session)
    val_types = [r.validation_type for r in results]
    assert "EXACT_DUPLICATE_INVOICE" in val_types
    assert doc2.is_duplicate is True

