import re
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.entities import Invoice, Document, ValidationResult


class DataValidationEngine:
    """
    Deterministic Financial Validation Engine.
    Executes independent mathematical and structural verification without LLM hallucinations.
    """

    def __init__(self, tolerance: float = None):
        self.tolerance = tolerance if tolerance is not None else settings.ROUNDING_TOLERANCE

    def _normalize_string(self, text: Optional[str]) -> str:
        if not text:
            return ""
        # Lowercase, strip punctuation and whitespace
        return re.sub(r"[^\w]", "", text.lower())

    def validate_missing_fields(
        self, invoice: Invoice, document_id: str
    ) -> List[Dict[str, Any]]:
        """Identifies missing mandatory and optional invoice fields."""
        issues = []
        critical_fields = [
            ("total_amount", "Total Amount", "Critical"),
            ("invoice_number", "Invoice Number", "High"),
            ("invoice_date", "Invoice Date", "High"),
            ("supplier_name", "Supplier Name", "Medium"),
        ]
        secondary_fields = [
            ("customer_name", "Customer Name", "Medium"),
            ("subtotal", "Subtotal", "Medium"),
            ("tax", "Tax", "Low"),
            ("currency", "Currency", "Low"),
        ]

        for field_key, field_label, severity in critical_fields:
            val = getattr(invoice, field_key, None)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(
                    {
                        "document_id": document_id,
                        "invoice_id": invoice.id,
                        "validation_type": "MISSING_FIELD",
                        "field_name": field_key,
                        "expected_value": "Present",
                        "actual_value": "Null / Empty",
                        "difference": "Missing required field",
                        "severity": severity,
                        "description": f"Essential financial field '{field_label}' was not detected in the document.",
                        "status": "Pending",
                    }
                )

        for field_key, field_label, severity in secondary_fields:
            val = getattr(invoice, field_key, None)
            if val is None or (isinstance(val, str) and not val.strip()):
                issues.append(
                    {
                        "document_id": document_id,
                        "invoice_id": invoice.id,
                        "validation_type": "MISSING_FIELD",
                        "field_name": field_key,
                        "expected_value": "Present",
                        "actual_value": "Null / Empty",
                        "difference": "Missing secondary field",
                        "severity": severity,
                        "description": f"Field '{field_label}' is missing or unparsed.",
                        "status": "Pending",
                    }
                )

        return issues

    def validate_financial_calculations(
        self, invoice: Invoice, document_id: str
    ) -> List[Dict[str, Any]]:
        """
        Verifies:
        1. Subtotal + Tax = Total Amount (with configurable tolerance)
        2. Quantity x Unit Price = Line Item Amount
        3. Sum(Line Items Amount) = Subtotal
        """
        issues = []

        subtotal = invoice.subtotal
        tax = invoice.tax or 0.0
        total = invoice.total_amount

        # 1. Subtotal + Tax vs Total Amount
        if subtotal is not None and total is not None:
            expected_total = round(subtotal + tax, 2)
            actual_total = round(total, 2)
            diff = round(abs(expected_total - actual_total), 2)

            if diff > self.tolerance:
                severity = "Critical" if diff > 5.0 else "High"
                issues.append(
                    {
                        "document_id": document_id,
                        "invoice_id": invoice.id,
                        "validation_type": "CALCULATION_MISMATCH",
                        "field_name": "total_amount",
                        "expected_value": f"{expected_total:.2f}",
                        "actual_value": f"{actual_total:.2f}",
                        "difference": f"{diff:.2f}",
                        "severity": severity,
                        "description": (
                            f"Total calculation mismatch: Subtotal ({subtotal:.2f}) + Tax ({tax:.2f}) = "
                            f"{expected_total:.2f}, but extracted Total is {actual_total:.2f} (diff: {diff:.2f})."
                        ),
                        "status": "Pending",
                    }
                )

        # 2. Line Item Calculations
        line_item_sum = 0.0
        has_items = False

        if invoice.line_items:
            has_items = True
            for item in invoice.line_items:
                qty = item.quantity or 0.0
                uprice = item.unit_price or 0.0
                amt = item.amount or 0.0
                line_item_sum += amt

                expected_item_amt = round(qty * uprice, 2)
                item_diff = round(abs(expected_item_amt - amt), 2)

                if uprice > 0 and qty > 0 and item_diff > self.tolerance:
                    issues.append(
                        {
                            "document_id": document_id,
                            "invoice_id": invoice.id,
                            "validation_type": "LINE_ITEM_ARITHMETIC",
                            "field_name": f"line_item:{item.description[:30]}",
                            "expected_value": f"{expected_item_amt:.2f}",
                            "actual_value": f"{amt:.2f}",
                            "difference": f"{item_diff:.2f}",
                            "severity": "Medium",
                            "description": (
                                f"Line item arithmetic error for '{item.description}': "
                                f"Qty {qty} × Unit Price {uprice:.2f} = {expected_item_amt:.2f}, but Amount is {amt:.2f}."
                            ),
                            "status": "Pending",
                        }
                    )

        # 3. Sum of Line Items vs Subtotal
        if has_items and subtotal is not None and len(invoice.line_items) > 0:
            sum_diff = round(abs(line_item_sum - subtotal), 2)
            if sum_diff > self.tolerance:
                issues.append(
                    {
                        "document_id": document_id,
                        "invoice_id": invoice.id,
                        "validation_type": "LINE_ITEMS_SUBTOTAL_MISMATCH",
                        "field_name": "subtotal",
                        "expected_value": f"{line_item_sum:.2f}",
                        "actual_value": f"{subtotal:.2f}",
                        "difference": f"{sum_diff:.2f}",
                        "severity": "High",
                        "description": (
                            f"Sum of line items ({line_item_sum:.2f}) does not match invoice subtotal ({subtotal:.2f})."
                        ),
                        "status": "Pending",
                    }
                )

        return issues

    def detect_duplicates(
        self, invoice: Invoice, document: Document, db: Session
    ) -> List[Dict[str, Any]]:
        """
        Detects potential and exact duplicates using:
        - Invoice number
        - Supplier name
        - Invoice date
        - Total amount
        Uses normalized matching across case, spaces, and punctuation.
        """
        issues = []
        if not invoice.invoice_number:
            return issues

        norm_inv_num = self._normalize_string(invoice.invoice_number)
        norm_supplier = self._normalize_string(invoice.supplier_name)

        # Query all existing invoices in database
        existing_invoices = (
            db.query(Invoice)
            .filter(Invoice.id != invoice.id, Invoice.document_id != document.id)
            .all()
        )

        for other in existing_invoices:
            if not other.invoice_number:
                continue

            other_norm_inv = self._normalize_string(other.invoice_number)
            other_norm_supp = self._normalize_string(other.supplier_name)

            # Match criteria
            same_number = (norm_inv_num == other_norm_inv) and len(norm_inv_num) > 2
            same_supplier = bool(norm_supplier and other_norm_supp and (norm_supplier == other_norm_supp or norm_supplier in other_norm_supp))
            same_amount = (
                invoice.total_amount is not None
                and other.total_amount is not None
                and abs(invoice.total_amount - other.total_amount) <= self.tolerance
            )

            if same_number and same_supplier and same_amount:
                # Exact Duplicate
                document.is_duplicate = True
                document.duplicate_of_id = other.document_id
                issues.append(
                    {
                        "document_id": document.id,
                        "invoice_id": invoice.id,
                        "validation_type": "EXACT_DUPLICATE_INVOICE",
                        "field_name": "invoice_number",
                        "expected_value": "Unique Invoice",
                        "actual_value": f"Duplicate of Doc ID {other.document_id} (Inv #{other.invoice_number})",
                        "difference": "Exact match across number, supplier, and total amount",
                        "severity": "Critical",
                        "description": (
                            f"Exact duplicate detected! Document matches existing invoice #{other.invoice_number} "
                            f"from '{other.supplier_name}' with identical total amount ({other.total_amount})."
                        ),
                        "status": "Pending",
                    }
                )
            elif same_number or (same_supplier and same_amount):
                # Potential Duplicate
                issues.append(
                    {
                        "document_id": document.id,
                        "invoice_id": invoice.id,
                        "validation_type": "POTENTIAL_DUPLICATE_INVOICE",
                        "field_name": "invoice_number" if same_number else "total_amount",
                        "expected_value": "Unique Record",
                        "actual_value": f"Matches Doc ID {other.document_id} (Inv #{other.invoice_number})",
                        "difference": "Partial match on key financial identifiers",
                        "severity": "High",
                        "description": (
                            f"Potential duplicate invoice: matches invoice #{other.invoice_number} "
                            f"from supplier '{other.supplier_name}'."
                        ),
                        "status": "Pending",
                    }
                )

        return issues

    def run_all_validations(
        self, invoice: Invoice, document: Document, db: Session
    ) -> List[ValidationResult]:
        """Runs missing fields, math calculations, and duplicate checks, saving results to DB."""
        raw_issues = []
        raw_issues.extend(self.validate_missing_fields(invoice, document.id))
        raw_issues.extend(self.validate_financial_calculations(invoice, document.id))
        raw_issues.extend(self.detect_duplicates(invoice, document, db))

        # Clear existing pending validation results for this document
        db.query(ValidationResult).filter(
            ValidationResult.document_id == document.id,
            ValidationResult.status == "Pending",
        ).delete()

        created_results = []
        for item in raw_issues:
            vr = ValidationResult(
                document_id=item["document_id"],
                invoice_id=item.get("invoice_id"),
                validation_type=item["validation_type"],
                field_name=item.get("field_name"),
                expected_value=item.get("expected_value"),
                actual_value=item.get("actual_value"),
                difference=item.get("difference"),
                severity=item["severity"],
                description=item["description"],
                status=item["status"],
            )
            db.add(vr)
            created_results.append(vr)

        # Flag invoice for manual review if critical or high issues exist
        has_critical_or_high = any(
            item["severity"] in ("Critical", "High") for item in raw_issues
        )
        if has_critical_or_high:
            invoice.requires_manual_review = True
            document.processing_status = "Needs Review"

        db.commit()
        return created_results


data_validation_engine = DataValidationEngine()

