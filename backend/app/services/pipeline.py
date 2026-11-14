import os
import time
import datetime
import traceback
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.entities import (
    Document,
    DocumentPage,
    ExtractedText,
    Invoice,
    InvoiceLineItem,
    ProcessingJob,
    ProcessingHistory,
    AuditLog,
)
from backend.app.processors.file_validator import validate_file, FileValidationError
from backend.app.processors.pdf_processor import pdf_processor
from backend.app.processors.spreadsheet_processor import spreadsheet_processor
from backend.app.processors.classifier import document_classifier
from backend.app.processors.normalizer import text_normalizer
from backend.app.ocr.ocr_engine import ocr_engine
from backend.app.ai.extractor import ai_extraction_engine
from backend.app.validators.validation_engine import data_validation_engine
from backend.app.search.search_engine import search_engine


class ProcessingPipeline:
    """
    Complete Document Intelligence Processing Pipeline.
    Implements all 12 stages from Upload to Search Indexing with state recovery.
    """

    def _log_history(
        self,
        db: Session,
        document_id: str,
        stage: str,
        status: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        history = ProcessingHistory(
            document_id=document_id,
            stage=stage,
            status=status,
            message=message,
            details=details or {},
        )
        db.add(history)
        db.commit()

    def process_document(self, document_id: str, db: Session) -> Document:
        """
        Executes the full pipeline for a given document.
        Safe against retries: clears previous partial extractions before re-processing.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document {document_id} not found.")

        start_time = time.time()
        job = (
            db.query(ProcessingJob)
            .filter(ProcessingJob.document_id == document_id)
            .order_by(ProcessingJob.created_at.desc())
            .first()
        )
        if not job:
            job = ProcessingJob(
                document_id=document_id,
                job_type="PIPELINE_FULL",
                status="Processing",
                progress=5,
                started_at=datetime.datetime.utcnow(),
            )
            db.add(job)
            db.commit()
        else:
            job.status = "Processing"
            job.progress = 5
            job.started_at = datetime.datetime.utcnow()
            db.commit()

        try:
            # 1. FILE VALIDATION & HASHING
            doc.processing_status = "Processing"
            db.commit()
            self._log_history(db, doc.id, "FILE_VALIDATION", "INFO", "Validating file and computing hash.")

            is_valid, file_fmt, file_size, file_hash = validate_file(
                doc.file_storage_reference, doc.original_filename
            )
            doc.file_format = file_fmt
            doc.file_size = file_size
            doc.file_hash = file_hash
            job.progress = 15
            db.commit()

            # 2. TEXT EXTRACTION & OCR / SPREADSHEET PARSING
            extracted_pages_data = []
            raw_full_text = ""
            extraction_method = "digital"

            if file_fmt == "pdf":
                doc.processing_status = "OCR Processing"
                db.commit()
                self._log_history(db, doc.id, "PDF_PARSING", "INFO", "Extracting text and running OCR on pages if scanned.")
                meta = pdf_processor.extract_metadata(doc.file_storage_reference)
                doc.page_count = meta.get("page_count", 1)

                pages_result = pdf_processor.process_pdf_pages(doc.file_storage_reference)
                
                # Delete existing pages to avoid duplicates on retry
                db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
                
                text_chunks = []
                for p in pages_result:
                    dp = DocumentPage(
                        document_id=doc.id,
                        page_number=p["page_number"],
                        raw_text=p["raw_text"],
                        ocr_applied=p["ocr_applied"],
                        ocr_confidence=p["ocr_confidence"],
                        is_empty=p["is_empty"],
                    )
                    db.add(dp)
                    if p["raw_text"]:
                        text_chunks.append(f"--- Page {p['page_number']} ---\n{p['raw_text']}")
                    if p["ocr_applied"]:
                        extraction_method = "hybrid"

                raw_full_text = "\n\n".join(text_chunks)

            elif file_fmt in ("xlsx", "xls", "csv"):
                self._log_history(db, doc.id, "SPREADSHEET_PARSING", "INFO", "Parsing spreadsheet sheets and rows.")
                parsed = spreadsheet_processor.process_file(doc.file_storage_reference, file_fmt)
                raw_full_text = parsed["combined_text"]
                extraction_method = "spreadsheet"
                doc.page_count = len(parsed["sheets"])

            elif file_fmt in ("jpg", "jpeg", "png", "tiff"):
                doc.processing_status = "OCR Processing"
                db.commit()
                self._log_history(db, doc.id, "IMAGE_OCR", "INFO", "Executing image preprocessing and OCR extraction.")
                ocr_text, conf = ocr_engine.extract_text_from_image(doc.file_storage_reference)
                raw_full_text = ocr_text
                extraction_method = "ocr"
                doc.page_count = 1

                # Save single page
                db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
                dp = DocumentPage(
                    document_id=doc.id,
                    page_number=1,
                    raw_text=ocr_text,
                    ocr_applied=True,
                    ocr_confidence=conf,
                    is_empty=len(ocr_text.strip()) == 0,
                )
                db.add(dp)

            job.progress = 40
            db.commit()

            # 3. TEXT NORMALIZATION
            self._log_history(db, doc.id, "TEXT_NORMALIZATION", "INFO", "Normalizing text representations.")
            normalized_text = text_normalizer.normalize(raw_full_text)

            # Save ExtractedText entity
            db.query(ExtractedText).filter(ExtractedText.document_id == doc.id).delete()
            ext_text_record = ExtractedText(
                document_id=doc.id,
                raw_text=raw_full_text,
                normalized_text=normalized_text,
                page_count=doc.page_count,
                extraction_method=extraction_method,
            )
            db.add(ext_text_record)
            job.progress = 50
            db.commit()

            # 4. DOCUMENT CLASSIFICATION
            self._log_history(db, doc.id, "DOCUMENT_CLASSIFICATION", "INFO", "Classifying document category.")
            classification = document_classifier.classify(file_fmt, normalized_text)
            doc.document_classification = classification
            job.progress = 60
            db.commit()

            # 5. AI EXTRACTION
            doc.processing_status = "AI Extraction"
            db.commit()
            self._log_history(db, doc.id, "AI_EXTRACTION", "INFO", "Extracting structured financial fields.")

            extracted_invoice_schema, raw_ai_dict, provider_name = ai_extraction_engine.extract(normalized_text)

            # Store Invoice in DB (clean existing if retry)
            existing_inv = db.query(Invoice).filter(Invoice.document_id == doc.id).first()
            if existing_inv:
                db.delete(existing_inv)
                db.commit()

            inv = Invoice(
                document_id=doc.id,
                invoice_number=extracted_invoice_schema.invoice_number,
                invoice_date=extracted_invoice_schema.invoice_date,
                supplier_name=extracted_invoice_schema.supplier_name,
                customer_name=extracted_invoice_schema.customer_name,
                subtotal=extracted_invoice_schema.subtotal,
                tax=extracted_invoice_schema.tax,
                total_amount=extracted_invoice_schema.total_amount,
                currency=extracted_invoice_schema.currency or "USD",
                raw_ai_response=raw_ai_dict,
                confidence_scores=extracted_invoice_schema.confidence,
                missing_fields=extracted_invoice_schema.missing_fields,
                uncertain_fields=extracted_invoice_schema.uncertain_fields,
                source_references=extracted_invoice_schema.source_references,
                requires_manual_review=extracted_invoice_schema.requires_manual_review,
            )
            db.add(inv)
            db.flush()

            # Add Line Items
            for idx, item in enumerate(extracted_invoice_schema.line_items):
                line_item = InvoiceLineItem(
                    invoice_id=inv.id,
                    item_order=idx + 1,
                    description=item.description,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    tax=item.tax,
                    amount=item.amount,
                    confidence=item.confidence,
                    source_page=item.source_page or 1,
                )
                db.add(line_item)

            job.progress = 75
            db.commit()

            # 6. DATA VALIDATION ENGINE
            doc.processing_status = "Validation"
            db.commit()
            self._log_history(db, doc.id, "DATA_VALIDATION", "INFO", "Running deterministic mathematical & duplicate checks.")

            validation_issues = data_validation_engine.run_all_validations(inv, doc, db)

            job.progress = 90
            db.commit()

            # 7. SEARCH INDEXING
            self._log_history(db, doc.id, "SEARCH_INDEXING", "INFO", "Updating search index with vector representation.")
            search_engine.fit_corpus(db)

            # 8. COMPLETION
            duration = round(time.time() - start_time, 2)
            doc.processing_duration = duration

            if doc.processing_status != "Needs Review":
                doc.processing_status = "Completed"

            job.status = "Completed"
            job.progress = 100
            job.completed_at = datetime.datetime.utcnow()
            job.duration_seconds = duration

            # Add Audit Log
            audit = AuditLog(
                action="PROCESS_DOCUMENT",
                entity_type="Document",
                entity_id=doc.id,
                details={
                    "duration": duration,
                    "status": doc.processing_status,
                    "validation_issues_count": len(validation_issues),
                    "classification": doc.document_classification,
                    "provider": provider_name,
                },
            )
            db.add(audit)
            db.commit()
            db.refresh(doc)
            return doc

        except Exception as e:
            db.rollback()
            duration = round(time.time() - start_time, 2)
            err_msg = f"{type(e).__name__}: {str(e)}"
            doc.processing_status = "Failed"
            doc.error_information = err_msg
            doc.processing_duration = duration

            job.status = "Failed"
            job.error_message = err_msg
            job.completed_at = datetime.datetime.utcnow()
            job.duration_seconds = duration

            self._log_history(
                db,
                doc.id,
                "FAILURE",
                "FAILED",
                f"Processing failed: {err_msg}",
                {"traceback": traceback.format_exc()},
            )
            db.commit()
            return doc


pipeline = ProcessingPipeline()
