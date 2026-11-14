import os
import pytest
from backend.app.processors.file_validator import validate_file, FileValidationError
from backend.app.processors.pdf_processor import pdf_processor
from backend.app.processors.spreadsheet_processor import spreadsheet_processor
from backend.app.processors.classifier import document_classifier
from backend.app.processors.normalizer import text_normalizer
from backend.app.ocr.ocr_engine import ocr_engine


def test_file_validator_valid_pdf():
    pdf_path = "sample_data/pdf/invoice_valid_001.pdf"
    is_valid, fmt, size, h = validate_file(pdf_path, "invoice_valid_001.pdf")
    assert is_valid is True
    assert fmt == "pdf"
    assert size > 0
    assert len(h) == 64


def test_file_validator_unsupported_extension(tmp_path):
    bad_file = tmp_path / "test.exe"
    bad_file.write_text("dummy binary")
    with pytest.raises(FileValidationError, match="not supported"):
        validate_file(str(bad_file), "test.exe")


def test_file_validator_corrupted_pdf(tmp_path):
    bad_pdf = tmp_path / "fake.pdf"
    bad_pdf.write_text("NOT A REAL PDF HEADER")
    with pytest.raises(FileValidationError, match="Corrupted or invalid PDF"):
        validate_file(str(bad_pdf), "fake.pdf")


def test_digital_pdf_extraction():
    pdf_path = "sample_data/pdf/invoice_valid_001.pdf"
    pages = pdf_processor.process_pdf_pages(pdf_path)
    assert len(pages) >= 1
    page1 = pages[0]
    assert "INV-2026-001" in page1["raw_text"]
    assert "ABC Technologies" in page1["raw_text"]
    assert page1["is_empty"] is False


def test_scanned_pdf_ocr_fallback():
    scanned_path = "sample_data/scanned/scanned_receipt_003.pdf"
    pages = pdf_processor.process_pdf_pages(scanned_path)
    assert len(pages) >= 1
    # Either OCR applied or fallback text extracted
    assert len(pages[0]["raw_text"]) > 0


def test_spreadsheet_processing():
    xlsx_path = "sample_data/excel/monthly_reconciliation_2026.xlsx"
    res = spreadsheet_processor.process_file(xlsx_path, "xlsx")
    assert "Invoice_Ledger" in res["sheets"]
    assert "Dept_Summary" in res["sheets"]
    assert res["total_records"] >= 5
    assert len(res["duplicate_rows"]) >= 1  # Detect duplicate row in sheet


def test_csv_processing():
    csv_path = "sample_data/csv/vendor_payments.csv"
    res = spreadsheet_processor.process_file(csv_path, "csv")
    assert res["total_records"] >= 3
    assert "INV-2026-001" in res["combined_text"]


def test_document_classification():
    inv_class = document_classifier.classify("pdf", "TAX INVOICE Invoice Number: INV-001 Subtotal: 100 Tax: 10 Total: 110")
    assert inv_class == "Invoice"

    receipt_class = document_classifier.classify("pdf", "Official Store Receipt #REC-99 Tender Cash Change Due Cashier: John")
    assert receipt_class == "Receipt"

    sheet_class = document_classifier.classify("xlsx", "Any content")
    assert sheet_class == "Spreadsheet"

    unknown_class = document_classifier.classify("pdf", "Hello this is a personal letter to a friend.")
    assert unknown_class == "Unknown Document"


def test_text_normalizer():
    raw = "Invoice  #INV-100\n\n\n\nDate:  2026-11-10 \u00a0 Total: $12,500.50"
    norm = text_normalizer.normalize(raw)
    assert "\u00a0" not in norm
    assert "\n\n\n" not in norm
    amt = text_normalizer.clean_currency_amount("$12,500.50")
    assert amt == 12500.50

