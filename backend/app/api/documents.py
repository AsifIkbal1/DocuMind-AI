import os
import uuid
import datetime
from typing import List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
    BackgroundTasks,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.core.config import settings
from backend.app.models.entities import (
    Document,
    Invoice,
    ValidationResult,
    ManualCorrection,
    ProcessingJob,
    AuditLog,
)
from backend.app.schemas.schemas import (
    DocumentResponse,
    DocumentDetailResponse,
    InvoiceResponse,
    ValidationResultSchema,
    ManualCorrectionRequest,
)
from backend.app.processors.file_validator import compute_file_hash
from backend.app.services.pipeline import pipeline

router = APIRouter()


def run_pipeline_task(document_id: str):
    from backend.app.database.session import SessionLocal

    db = SessionLocal()
    try:
        pipeline.process_document(document_id, db)
    finally:
        db.close()


@router.post("/upload", response_model=List[DocumentResponse], summary="Upload documents")
async def upload_documents(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    """
    Upload one or more documents (PDF, JPG, PNG, TIFF, XLSX, XLS, CSV).
    Validates size and format, computes SHA-256 hash, detects duplicates,
    and enqueues background processing.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded.",
        )

    uploaded_docs = []

    for file in files:
        filename = file.filename or "unknown_file"
        parts = filename.rsplit(".", 1)
        ext = parts[1].lower() if len(parts) > 1 else ""

        if ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' format '.{ext}' is not supported. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}",
            )

        # Unique storage path to avoid collision
        doc_id = str(uuid.uuid4())
        save_name = f"{doc_id}_{filename}"
        save_path = os.path.join(settings.UPLOAD_DIR, save_name)

        content = await file.read()
        file_size = len(content)

        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File '{filename}' exceeds {settings.MAX_FILE_SIZE_MB} MB limit.",
            )

        with open(save_path, "wb") as f:
            f.write(content)

        file_hash = compute_file_hash(save_path)

        # Check existing duplicate hash
        existing_doc = (
            db.query(Document)
            .filter(Document.file_hash == file_hash)
            .first()
        )
        is_dup = existing_doc is not None
        dup_of = existing_doc.id if is_dup else None

        doc = Document(
            id=doc_id,
            original_filename=filename,
            file_format=ext,
            file_size=file_size,
            file_hash=file_hash,
            upload_time=datetime.datetime.utcnow(),
            processing_status="Queued",
            file_storage_reference=save_path,
            document_classification="Unknown Document",
            page_count=1,
            is_duplicate=is_dup,
            duplicate_of_id=dup_of,
        )
        db.add(doc)

        job = ProcessingJob(
            document_id=doc_id,
            job_type="PIPELINE_FULL",
            status="Queued",
            progress=0,
        )
        db.add(job)
        db.commit()
        db.refresh(doc)

        uploaded_docs.append(doc)

        # Enqueue asynchronous processing
        if background_tasks:
            background_tasks.add_task(run_pipeline_task, doc_id)

    return uploaded_docs


@router.get("", summary="List documents")
def list_documents(
    status: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Document)
    if status:
        query = query.filter(Document.processing_status == status)
    if classification:
        query = query.filter(Document.document_classification == classification)
    if search:
        query = query.filter(Document.original_filename.ilike(f"%{search}%"))

    total = query.count()
    documents = (
        query.order_by(Document.upload_time.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "documents": [DocumentResponse.model_validate(d) for d in documents],
    }


@router.get("/{document_id}", response_model=DocumentDetailResponse, summary="Get document details")
def get_document_details(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    val_count = (
        db.query(ValidationResult)
        .filter(ValidationResult.document_id == document_id, ValidationResult.status == "Pending")
        .count()
    )

    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "file_format": doc.file_format,
        "file_size": doc.file_size,
        "file_hash": doc.file_hash,
        "upload_time": doc.upload_time,
        "processing_status": doc.processing_status,
        "document_classification": doc.document_classification,
        "page_count": doc.page_count,
        "processing_duration": doc.processing_duration,
        "error_information": doc.error_information,
        "is_duplicate": doc.is_duplicate,
        "duplicate_of_id": doc.duplicate_of_id,
        "pages": doc.pages,
        "extracted_text": doc.extracted_text_rel,
        "invoice": doc.invoice,
        "validation_issues_count": val_count,
    }


@router.get("/{document_id}/status", summary="Get processing status")
def get_processing_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    job = (
        db.query(ProcessingJob)
        .filter(ProcessingJob.document_id == document_id)
        .order_by(ProcessingJob.created_at.desc())
        .first()
    )

    return {
        "document_id": doc.id,
        "filename": doc.original_filename,
        "processing_status": doc.processing_status,
        "job_progress": job.progress if job else 100,
        "duration_seconds": doc.processing_duration,
        "error_information": doc.error_information,
    }


@router.get("/{document_id}/results", response_model=Optional[InvoiceResponse], summary="Get extracted JSON results")
def get_extracted_results(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return doc.invoice


@router.get("/{document_id}/validation", response_model=List[ValidationResultSchema], summary="Get validation issues")
def get_validation_results(
    document_id: str,
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ValidationResult).filter(ValidationResult.document_id == document_id)
    if severity:
        query = query.filter(ValidationResult.severity == severity)
    if status_filter:
        query = query.filter(ValidationResult.status == status_filter)

    return query.order_by(ValidationResult.created_timestamp.desc()).all()


@router.patch("/{document_id}/corrections", summary="Apply manual correction")
def apply_manual_correction(
    document_id: str,
    correction: ManualCorrectionRequest,
    db: Session = Depends(get_db),
):
    """
    Non-destructively edits extracted invoice fields:
    - Preserves audit log and manual corrections history.
    - Updates target field on Invoice.
    - Re-runs mathematical validation to verify resolution!
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not doc.invoice:
        raise HTTPException(status_code=404, detail="Document or invoice not found.")

    inv = doc.invoice
    field = correction.field_name
    original_val = getattr(inv, field, None)

    # Cast to float if numerical field
    val_to_save = correction.corrected_value
    if field in ("subtotal", "tax", "total_amount"):
        try:
            val_to_save = float(val_to_save)
        except (ValueError, TypeError):
            pass

    if hasattr(inv, field):
        setattr(inv, field, val_to_save)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid field name '{field}'.")

    inv.is_corrected = True
    inv.updated_at = datetime.datetime.utcnow()

    # Create ManualCorrection audit record
    record = ManualCorrection(
        document_id=doc.id,
        invoice_id=inv.id,
        field_name=field,
        original_value=str(original_val),
        corrected_value=str(val_to_save),
        reason=correction.reason,
        reviewer_name=correction.reviewer_name,
    )
    db.add(record)
    db.commit()

    # Re-run validation with updated values
    from backend.app.validators.validation_engine import data_validation_engine

    remaining_issues = data_validation_engine.run_all_validations(inv, doc, db)

    # If all critical and high issues are resolved, update document status
    has_critical_or_high = any(i.severity in ("Critical", "High") for i in remaining_issues)
    if not has_critical_or_high:
        doc.processing_status = "Completed"
        inv.requires_manual_review = False
        db.commit()

    return {
        "status": "success",
        "message": f"Field '{field}' successfully updated.",
        "field_name": field,
        "original_value": original_val,
        "corrected_value": val_to_save,
        "document_status": doc.processing_status,
        "active_validation_issues_count": len(remaining_issues),
    }


@router.post("/{document_id}/retry", summary="Reprocess failed or needs-review document")
def retry_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    doc.processing_status = "Queued"
    doc.error_information = None
    db.commit()

    if background_tasks:
        background_tasks.add_task(run_pipeline_task, doc.id)

    return {"status": "success", "message": f"Processing queued for retry on '{doc.original_filename}'."}


@router.get("/{document_id}/file", summary="Preview / Download original file")
def get_original_file(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc or not os.path.exists(doc.file_storage_reference):
        raise HTTPException(status_code=404, detail="File not found on server.")

    media_types = {
        "pdf": "application/pdf",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "tiff": "image/tiff",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xls": "application/vnd.ms-excel",
        "csv": "text/csv",
    }
    media_type = media_types.get(doc.file_format, "application/octet-stream")

    return FileResponse(
        path=doc.file_storage_reference,
        media_type=media_type,
        filename=doc.original_filename,
    )
