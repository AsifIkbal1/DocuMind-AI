import pytest
from backend.app.models.entities import Document, Invoice
from backend.app.verification.verification_engine import verification_engine


def test_pdf_to_pdf_verification(db_session):
    doc1 = Document(
        original_filename="inv_a.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="h1",
        file_storage_reference="p1",
    )
    db_session.add(doc1)
    db_session.flush()

    inv1 = Invoice(
        document_id=doc1.id,
        invoice_number="INV-A",
        invoice_date="2026-11-10",
        supplier_name="ABC Tech",
        total_amount=1000.00,
        currency="USD",
    )
    db_session.add(inv1)

    doc2 = Document(
        original_filename="inv_b.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="h2",
        file_storage_reference="p2",
    )
    db_session.add(doc2)
    db_session.flush()

    inv2 = Invoice(
        document_id=doc2.id,
        invoice_number="INV-A",
        invoice_date="2026-11-10",
        supplier_name="ABC Tech",
        total_amount=1000.00,
        currency="USD",
    )
    db_session.add(inv2)
    db_session.commit()

    report = verification_engine.compare_pdf_to_pdf(doc1, doc2, db_session)
    assert report.report_type == "PDF_PDF"
    assert report.matching_score >= 80.0
    assert len(report.items) > 0


def test_pdf_to_excel_verification(db_session):
    # Load actual sample excel
    excel_path = "sample_data/excel/monthly_reconciliation_2026.xlsx"
    excel_doc = Document(
        original_filename="monthly_reconciliation_2026.xlsx",
        file_format="xlsx",
        file_size=5000,
        file_hash="hexcel",
        file_storage_reference=excel_path,
    )
    db_session.add(excel_doc)
    db_session.flush()

    pdf_doc = Document(
        original_filename="invoice_valid_001.pdf",
        file_format="pdf",
        file_size=2000,
        file_hash="hpdf",
        file_storage_reference="sample_data/pdf/invoice_valid_001.pdf",
    )
    db_session.add(pdf_doc)
    db_session.flush()

    pdf_inv = Invoice(
        document_id=pdf_doc.id,
        invoice_number="INV-2026-001",
        invoice_date="2026-11-10",
        supplier_name="ABC Technologies Ltd.",
        total_amount=11500.00,
        currency="USD",
    )
    db_session.add(pdf_inv)
    db_session.commit()

    report = verification_engine.compare_pdf_to_excel([pdf_doc], excel_doc, db_session)
    assert report.report_type == "PDF_EXCEL"
    assert report.summary["matched_records"] >= 1
    # Check that report detected the match
    matched_items = [item for item in report.items if item.is_match]
    assert len(matched_items) >= 1

