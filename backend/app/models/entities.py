import datetime
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    JSON,
    Enum,
)
from sqlalchemy.orm import relationship
from backend.app.database.session import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), default="reviewer")  # admin, reviewer, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    corrections = relationship("ManualCorrection", back_populates="reviewer")
    audit_logs = relationship("AuditLog", back_populates="user")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    original_filename = Column(String(255), nullable=False, index=True)
    file_format = Column(String(20), nullable=False, index=True)  # pdf, xlsx, xls, csv, jpg, etc.
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256
    upload_time = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    processing_status = Column(
        String(50),
        default="Uploaded",
        index=True,
    )  # Uploaded, Queued, Processing, OCR Processing, AI Extraction, Validation, Completed, Failed, Needs Review
    file_storage_reference = Column(String(512), nullable=False)
    document_classification = Column(
        String(50),
        default="Unknown Document",
        index=True,
    )  # Invoice, Receipt, Financial Statement, Spreadsheet, Unknown Document
    page_count = Column(Integer, default=1)
    processing_duration = Column(Float, default=0.0)
    error_information = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String(36), nullable=True)

    # Relationships
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    extracted_text_rel = relationship("ExtractedText", back_populates="document", uselist=False, cascade="all, delete-orphan")
    invoice = relationship("Invoice", back_populates="document", uselist=False, cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="document", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="document", cascade="all, delete-orphan")
    processing_history = relationship("ProcessingHistory", back_populates="document", cascade="all, delete-orphan")
    corrections = relationship("ManualCorrection", back_populates="document", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=True)
    ocr_applied = Column(Boolean, default=False)
    ocr_confidence = Column(Float, nullable=True)
    is_empty = Column(Boolean, default=False)
    image_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="pages")


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    raw_text = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    page_count = Column(Integer, default=1)
    extraction_method = Column(String(50), default="digital")  # digital, ocr, spreadsheet, hybrid
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="extracted_text_rel")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    invoice_date = Column(String(50), nullable=True, index=True)
    supplier_name = Column(String(255), nullable=True, index=True)
    customer_name = Column(String(255), nullable=True, index=True)
    subtotal = Column(Float, nullable=True)
    tax = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=True, index=True)
    currency = Column(String(20), default="USD", index=True)
    
    # AI Metadata & Quality flags
    raw_ai_response = Column(JSON, nullable=True)
    confidence_scores = Column(JSON, nullable=True)  # {field: float}
    missing_fields = Column(JSON, default=list)  # ["tax", "customer_name"]
    uncertain_fields = Column(JSON, default=list)  # ["invoice_number"]
    source_references = Column(JSON, default=list)  # [{field: str, page: int, snippet: str}]
    requires_manual_review = Column(Boolean, default=False, index=True)
    is_corrected = Column(Boolean, default=False)
    
    # Vector embedding representation (for semantic search, stored as JSON array if SQLite or native vector if pgvector)
    embedding = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="invoice")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    validation_results = relationship("ValidationResult", back_populates="invoice", cascade="all, delete-orphan")
    corrections = relationship("ManualCorrection", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceLineItem(Base):
    __tablename__ = "invoice_line_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    item_order = Column(Integer, default=1)
    description = Column(Text, nullable=False)
    quantity = Column(Float, default=1.0)
    unit_price = Column(Float, default=0.0)
    tax = Column(Float, nullable=True)
    amount = Column(Float, default=0.0)
    confidence = Column(Float, nullable=True)
    source_page = Column(Integer, default=1)

    invoice = relationship("Invoice", back_populates="line_items")


class ValidationResult(Base):
    __tablename__ = "validation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True, index=True)
    validation_type = Column(String(100), nullable=False)  # MISSING_FIELD, CALCULATION_MISMATCH, DUPLICATE_INVOICE, etc.
    field_name = Column(String(100), nullable=True)
    expected_value = Column(String(255), nullable=True)
    actual_value = Column(String(255), nullable=True)
    difference = Column(String(255), nullable=True)
    severity = Column(String(20), default="Medium", index=True)  # Critical, High, Medium, Low
    description = Column(Text, nullable=False)
    status = Column(String(50), default="Pending", index=True)  # Pending, Resolved, Ignored
    created_timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    document = relationship("Document", back_populates="validation_results")
    invoice = relationship("Invoice", back_populates="validation_results")


class VerificationReport(Base):
    __tablename__ = "verification_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_type = Column(String(50), nullable=False, index=True)  # PDF_PDF or PDF_EXCEL
    source_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    target_document_id = Column(String(36), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True)
    matching_score = Column(Float, default=0.0)
    status = Column(String(50), default="Completed", index=True)  # Completed, Needs Review, Mismatched
    summary = Column(JSON, default=dict)  # {total_fields, matched, mismatched, missing}
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    items = relationship("VerificationItem", back_populates="report", cascade="all, delete-orphan")


class VerificationItem(Base):
    __tablename__ = "verification_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("verification_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    source_value = Column(String(500), nullable=True)
    target_value = Column(String(500), nullable=True)
    is_match = Column(Boolean, default=False)
    discrepancy_type = Column(String(100), nullable=True)  # VALUE_MISMATCH, MISSING_IN_TARGET, FORMAT_DIFF
    severity = Column(String(20), default="Medium")  # Critical, High, Medium, Low
    notes = Column(Text, nullable=True)

    report = relationship("VerificationReport", back_populates="items")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(100), nullable=False)  # PIPELINE_FULL, OCR_ONLY, AI_EXTRACTION, VALIDATION
    status = Column(String(50), default="Queued", index=True)  # Queued, Processing, Completed, Failed, Retrying
    progress = Column(Integer, default=0)  # 0 to 100
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    document = relationship("Document", back_populates="processing_jobs")


class ProcessingHistory(Base):
    __tablename__ = "processing_histories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    stage = Column(String(100), nullable=False)  # UPLOAD, CLASSIFICATION, OCR, AI_EXTRACTION, VALIDATION
    status = Column(String(50), nullable=False)  # SUCCESS, FAILED, WARNING, INFO
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    document = relationship("Document", back_populates="processing_history")


class ManualCorrection(Base):
    __tablename__ = "manual_corrections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    field_name = Column(String(100), nullable=False)
    original_value = Column(Text, nullable=True)
    corrected_value = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewer_name = Column(String(255), default="Human Reviewer")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    document = relationship("Document", back_populates="corrections")
    invoice = relationship("Invoice", back_populates="corrections")
    reviewer = relationship("User", back_populates="corrections")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action = Column(String(100), nullable=False, index=True)  # UPLOAD, EXTRACT, VALIDATE, CORRECT, VERIFY, RETRY, LOGIN
    entity_type = Column(String(50), nullable=False, index=True)  # Document, Invoice, ValidationResult, User
    entity_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email = Column(String(255), nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

