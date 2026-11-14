import datetime
import re
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.models.entities import (
    Document,
    Invoice,
    VerificationReport,
    VerificationItem,
)
from backend.app.processors.spreadsheet_processor import spreadsheet_processor
from backend.app.processors.normalizer import text_normalizer


class VerificationEngine:
    """
    Cross-Verification Engine:
    - PDF-to-PDF side-by-side comparison & discrepancy detector
    - PDF-to-Excel cross-document reconciliation and reconciliation reporting
    """

    def _normalize_string(self, text: Optional[str]) -> str:
        if not text:
            return ""
        return re.sub(r"[^\w]", "", text.lower())

    def compare_pdf_to_pdf(
        self, source_doc: Document, target_doc: Document, db: Session
    ) -> VerificationReport:
        """Compares two extracted PDF documents field by field and generates report."""
        source_inv = source_doc.invoice
        target_inv = target_doc.invoice

        fields_to_compare = [
            ("invoice_number", "Invoice Number", "High"),
            ("invoice_date", "Invoice Date", "Medium"),
            ("supplier_name", "Supplier Name", "High"),
            ("customer_name", "Customer Name", "Medium"),
            ("subtotal", "Subtotal", "Medium"),
            ("tax", "Tax", "Medium"),
            ("total_amount", "Total Amount", "Critical"),
            ("currency", "Currency", "Low"),
        ]

        report = VerificationReport(
            report_type="PDF_PDF",
            source_document_id=source_doc.id,
            target_document_id=target_doc.id,
            matching_score=0.0,
            status="Completed",
            summary={},
        )
        db.add(report)
        db.flush()

        matched_count = 0
        total_fields = len(fields_to_compare)
        items = []

        for field_key, field_label, severity in fields_to_compare:
            src_val = getattr(source_inv, field_key, None) if source_inv else None
            tgt_val = getattr(target_inv, field_key, None) if target_inv else None

            is_match = False
            discrepancy_type = None
            notes = None

            if src_val is None and tgt_val is None:
                is_match = True
                notes = "Both values absent."
            elif src_val is None or tgt_val is None:
                is_match = False
                discrepancy_type = "MISSING_IN_TARGET" if tgt_val is None else "MISSING_IN_SOURCE"
                notes = f"Field is missing in {'target' if tgt_val is None else 'source'} document."
            elif isinstance(src_val, (int, float)) or isinstance(tgt_val, (int, float)):
                try:
                    f_src = round(float(src_val), 2)
                    f_tgt = round(float(tgt_val), 2)
                    diff = round(abs(f_src - f_tgt), 2)
                    if diff <= 0.05:
                        is_match = True
                    else:
                        is_match = False
                        discrepancy_type = "VALUE_MISMATCH"
                        notes = f"Numeric variance: source={f_src:.2f}, target={f_tgt:.2f}, difference={diff:.2f}"
                except ValueError:
                    is_match = str(src_val).strip() == str(tgt_val).strip()
            else:
                s1 = self._normalize_string(str(src_val))
                s2 = self._normalize_string(str(tgt_val))
                if s1 == s2 or s1 in s2 or s2 in s1:
                    is_match = True
                else:
                    is_match = False
                    discrepancy_type = "TEXT_MISMATCH"
                    notes = f"Text difference between '{src_val}' and '{tgt_val}'."

            if is_match:
                matched_count += 1

            v_item = VerificationItem(
                report_id=report.id,
                field_name=field_label,
                source_value=str(src_val) if src_val is not None else None,
                target_value=str(tgt_val) if tgt_val is not None else None,
                is_match=is_match,
                discrepancy_type=discrepancy_type,
                severity=severity if not is_match else "Low",
                notes=notes,
            )
            db.add(v_item)
            items.append(v_item)

        score = round((matched_count / total_fields) * 100.0, 1)
        report.matching_score = score
        report.status = "Needs Review" if score < 100.0 else "Completed"
        report.summary = {
            "total_fields": total_fields,
            "matched_fields": matched_count,
            "mismatched_fields": total_fields - matched_count,
            "source_filename": source_doc.original_filename,
            "target_filename": target_doc.original_filename,
        }

        db.commit()
        db.refresh(report)
        return report

    def compare_pdf_to_excel(
        self, pdf_docs: List[Document], excel_doc: Document, db: Session
    ) -> VerificationReport:
        """
        Reconciles one or more PDF invoices against an Excel workbook.
        Matches records by invoice number, supplier, and total amount.
        Identifies missing PDF records, missing Excel records, and amount/date discrepancies.
        """
        # Parse Excel workbook
        parsed_excel = spreadsheet_processor.process_file(
            excel_doc.file_storage_reference, excel_doc.file_format
        )
        excel_records = parsed_excel["all_records"]

        report = VerificationReport(
            report_type="PDF_EXCEL",
            source_document_id=pdf_docs[0].id if pdf_docs else None,
            target_document_id=excel_doc.id,
            matching_score=0.0,
            status="Completed",
            summary={},
        )
        db.add(report)
        db.flush()

        matched_records = 0
        total_pdf_invoices = len(pdf_docs)
        items = []

        unmatched_excel = list(excel_records)

        for pdf_doc in pdf_docs:
            inv = pdf_doc.invoice
            if not inv:
                v_item = VerificationItem(
                    report_id=report.id,
                    field_name=f"PDF Record: {pdf_doc.original_filename}",
                    source_value="Unparsed PDF",
                    target_value="N/A",
                    is_match=False,
                    discrepancy_type="UNPARSED_SOURCE",
                    severity="High",
                    notes="PDF has no extracted invoice data to reconcile.",
                )
                db.add(v_item)
                continue

            inv_no_norm = self._normalize_string(inv.invoice_number)
            total_amt = inv.total_amount

            # Search in excel records
            best_match = None
            best_match_idx = -1

            for idx, rec in enumerate(unmatched_excel):
                rec_inv_no = self._normalize_string(str(rec.get("invoice_number", "")))
                rec_total = rec.get("total_amount")
                if rec_total is not None:
                    try:
                        rec_total = float(rec_total)
                    except ValueError:
                        rec_total = None

                # Match logic: invoice number match or (same supplier and total amount match)
                if inv_no_norm and rec_inv_no and (inv_no_norm == rec_inv_no):
                    best_match = rec
                    best_match_idx = idx
                    break
                elif total_amt is not None and rec_total is not None and abs(total_amt - rec_total) <= 0.05:
                    best_match = rec
                    best_match_idx = idx
                    break

            if best_match:
                unmatched_excel.pop(best_match_idx)
                rec_inv = best_match.get("invoice_number")
                rec_total = best_match.get("total_amount")
                rec_date = best_match.get("date")
                rec_supp = best_match.get("supplier")

                # Check amount match
                amount_match = True
                amount_notes = "Amounts match exactly."
                if total_amt is not None and rec_total is not None:
                    diff = round(abs(float(total_amt) - float(rec_total)), 2)
                    if diff > 0.05:
                        amount_match = False
                        amount_notes = f"Amount discrepancy: PDF={total_amt}, Excel={rec_total} (diff: {diff})"

                is_record_match = (
                    inv.invoice_number == rec_inv
                    and amount_match
                )
                if is_record_match:
                    matched_records += 1

                v_item = VerificationItem(
                    report_id=report.id,
                    field_name=f"Invoice #{inv.invoice_number or 'N/A'}",
                    source_value=f"PDF: {inv.invoice_number} | {total_amt} {inv.currency} | {inv.supplier_name}",
                    target_value=f"Excel [Sheet: {best_match.get('_sheet_name')}, Row: {best_match.get('_row_number')}]: {rec_inv} | {rec_total} | {rec_supp}",
                    is_match=is_record_match,
                    discrepancy_type=None if is_record_match else "DISCREPANCY_IN_RECORD",
                    severity="Critical" if not amount_match else ("Medium" if not is_record_match else "Low"),
                    notes=amount_notes,
                )
                db.add(v_item)
            else:
                # Missing in Excel
                v_item = VerificationItem(
                    report_id=report.id,
                    field_name=f"Invoice #{inv.invoice_number or 'N/A'}",
                    source_value=f"PDF: {inv.invoice_number} | {total_amt} {inv.currency}",
                    target_value="NOT FOUND IN EXCEL",
                    is_match=False,
                    discrepancy_type="MISSING_IN_EXCEL",
                    severity="High",
                    notes="This invoice exists in PDF batch but was not found anywhere in the Excel spreadsheet.",
                )
                db.add(v_item)

        # Flag any remaining Excel rows as missing in PDF
        for leftover in unmatched_excel[:20]:  # Limit top 20 leftovers
            v_item = VerificationItem(
                report_id=report.id,
                field_name=f"Excel Record: {leftover.get('invoice_number', 'Row ' + str(leftover.get('_row_number')))}",
                source_value="NOT FOUND IN PDFS",
                target_value=f"Excel [Sheet: {leftover.get('_sheet_name')}, Row {leftover.get('_row_number')}]: {leftover.get('invoice_number')} | {leftover.get('total_amount')} | {leftover.get('supplier')}",
                is_match=False,
                discrepancy_type="MISSING_IN_PDF",
                severity="Medium",
                notes="Row exists in Excel but no matching PDF invoice was found.",
            )
            db.add(v_item)

        score = round((matched_records / max(total_pdf_invoices, 1)) * 100.0, 1)
        report.matching_score = score
        report.status = "Needs Review" if score < 100.0 else "Completed"
        report.summary = {
            "total_pdf_invoices": total_pdf_invoices,
            "total_excel_records": len(excel_records),
            "matched_records": matched_records,
            "missing_in_excel": total_pdf_invoices - matched_records,
            "missing_in_pdf": len(unmatched_excel),
            "duplicate_excel_rows_count": len(parsed_excel["duplicate_rows"]),
        }

        db.commit()
        db.refresh(report)
        return report


verification_engine = VerificationEngine()

