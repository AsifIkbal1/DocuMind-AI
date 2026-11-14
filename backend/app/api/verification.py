from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import Document, VerificationReport
from backend.app.schemas.schemas import (
    PDFtoPDFVerificationRequest,
    PDFtoExcelVerificationRequest,
    VerificationReportResponse,
)
from backend.app.verification.verification_engine import verification_engine

router = APIRouter()


@router.post("/pdf-pdf", response_model=VerificationReportResponse, summary="Cross-verify two PDF documents")
def verify_pdf_to_pdf(
    request: PDFtoPDFVerificationRequest,
    db: Session = Depends(get_db),
):
    source_doc = db.query(Document).filter(Document.id == request.source_document_id).first()
    target_doc = db.query(Document).filter(Document.id == request.target_document_id).first()

    if not source_doc or not target_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both PDF documents not found.",
        )

    report = verification_engine.compare_pdf_to_pdf(source_doc, target_doc, db)
    return report


@router.post("/pdf-excel", response_model=VerificationReportResponse, summary="Cross-verify PDF invoices against Excel workbook")
def verify_pdf_to_excel(
    request: PDFtoExcelVerificationRequest,
    db: Session = Depends(get_db),
):
    if not request.pdf_document_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide at least one PDF invoice ID.",
        )

    pdf_docs = (
        db.query(Document)
        .filter(Document.id.in_(request.pdf_document_ids))
        .all()
    )
    excel_doc = db.query(Document).filter(Document.id == request.excel_document_id).first()

    if not excel_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Excel workbook document {request.excel_document_id} not found.",
        )

    report = verification_engine.compare_pdf_to_excel(pdf_docs, excel_doc, db)
    return report


@router.get("", response_model=List[VerificationReportResponse], summary="Get verification history")
def list_verification_reports(db: Session = Depends(get_db)):
    reports = (
        db.query(VerificationReport)
        .order_by(VerificationReport.created_at.desc())
        .limit(50)
        .all()
    )
    return reports


@router.get("/{report_id}", response_model=VerificationReportResponse, summary="Get verification report details")
def get_verification_report(report_id: str, db: Session = Depends(get_db)):
    report = (
        db.query(VerificationReport)
        .filter(VerificationReport.id == report_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Verification report not found.")
    return report
