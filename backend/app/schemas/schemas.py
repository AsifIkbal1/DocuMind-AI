import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Auth Schemas
# ---------------------------------------------------------------------------
class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None
    role: str = "reviewer"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Invoice & Line Item Schemas
# ---------------------------------------------------------------------------
class LineItemSchema(BaseModel):
    description: str
    quantity: float = 1.0
    unit_price: float = 0.0
    tax: Optional[float] = None
    amount: float = 0.0
    confidence: Optional[float] = None
    source_page: Optional[int] = 1


class SourceReference(BaseModel):
    field: str
    page: int
    snippet: str


class InvoiceExtractionSchema(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    supplier_name: Optional[str] = None
    customer_name: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = "USD"
    line_items: List[LineItemSchema] = Field(default_factory=list)
    missing_fields: List[str] = Field(default_factory=list)
    uncertain_fields: List[str] = Field(default_factory=list)
    confidence: Dict[str, float] = Field(default_factory=dict)
    source_references: List[Dict[str, Any]] = Field(default_factory=list)
    requires_manual_review: bool = False


class InvoiceResponse(InvoiceExtractionSchema):
    id: str
    document_id: str
    is_corrected: bool = False
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Document Schemas
# ---------------------------------------------------------------------------
class DocumentPageSchema(BaseModel):
    page_number: int
    raw_text: Optional[str] = None
    ocr_applied: bool = False
    ocr_confidence: Optional[float] = None
    is_empty: bool = False

    class Config:
        from_attributes = True


class ExtractedTextSchema(BaseModel):
    raw_text: str
    normalized_text: str
    page_count: int
    extraction_method: str

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    file_format: str
    file_size: int
    file_hash: str
    upload_time: datetime.datetime
    processing_status: str
    document_classification: str
    page_count: int
    processing_duration: float
    error_information: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    pages: List[DocumentPageSchema] = Field(default_factory=list)
    extracted_text: Optional[ExtractedTextSchema] = None
    invoice: Optional[InvoiceResponse] = None
    validation_issues_count: int = 0


# ---------------------------------------------------------------------------
# Validation Schemas
# ---------------------------------------------------------------------------
class ValidationResultSchema(BaseModel):
    id: str
    document_id: str
    invoice_id: Optional[str] = None
    validation_type: str
    field_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    difference: Optional[str] = None
    severity: str  # Critical, High, Medium, Low
    description: str
    status: str  # Pending, Resolved, Ignored
    created_timestamp: datetime.datetime

    class Config:
        from_attributes = True


class ManualCorrectionRequest(BaseModel):
    field_name: str
    corrected_value: Any
    reason: Optional[str] = "Manual review correction"
    reviewer_name: Optional[str] = "User Reviewer"


# ---------------------------------------------------------------------------
# Verification Schemas
# ---------------------------------------------------------------------------
class PDFtoPDFVerificationRequest(BaseModel):
    source_document_id: str
    target_document_id: str


class PDFtoExcelVerificationRequest(BaseModel):
    pdf_document_ids: List[str]
    excel_document_id: str


class VerificationItemSchema(BaseModel):
    id: str
    field_name: str
    source_value: Optional[str] = None
    target_value: Optional[str] = None
    is_match: bool
    discrepancy_type: Optional[str] = None
    severity: str
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class VerificationReportResponse(BaseModel):
    id: str
    report_type: str
    source_document_id: Optional[str] = None
    target_document_id: Optional[str] = None
    matching_score: float
    status: str
    summary: Dict[str, Any]
    items: List[VerificationItemSchema] = Field(default_factory=list)
    created_at: datetime.datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Search Schemas
# ---------------------------------------------------------------------------
class SearchRequest(BaseModel):
    query: str
    search_type: str = "all"  # "all", "keyword", "semantic"
    document_types: Optional[List[str]] = None
    supplier: Optional[str] = None
    customer: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = 20
    offset: int = 0


class SearchResultItem(BaseModel):
    document_id: str
    filename: str
    document_type: str
    file_format: str
    upload_time: datetime.datetime
    relevance_score: float
    matched_by: str  # "keyword", "semantic", "exact"
    snippet: str
    invoice_details: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: str
    search_type: str
    total_results: int
    results: List[SearchResultItem]


# ---------------------------------------------------------------------------
# Analytics & Jobs Schemas
# ---------------------------------------------------------------------------
class AnalyticsOverviewResponse(BaseModel):
    total_documents: int
    processed_documents: int
    pending_documents: int
    failed_documents: int
    validation_errors_count: int
    duplicate_invoices_count: int
    documents_awaiting_review: int
    average_processing_time: float
    measured_extraction_accuracy: float
    file_type_distribution: Dict[str, int]
    document_processing_trend: List[Dict[str, Any]]
    validation_error_distribution: Dict[str, int]
    recent_activity: List[Dict[str, Any]]


class JobResponse(BaseModel):
    id: str
    document_id: str
    document_name: str
    job_type: str
    current_status: str
    progress: int
    creation_time: datetime.datetime
    processing_duration: float
    error_message: Optional[str] = None

    class Config:
        from_attributes = True
