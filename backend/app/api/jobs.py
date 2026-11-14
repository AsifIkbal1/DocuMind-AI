from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.models.entities import ProcessingJob, Document
from backend.app.schemas.schemas import JobResponse

router = APIRouter()


@router.get("", response_model=List[JobResponse], summary="List processing jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = (
        db.query(ProcessingJob)
        .order_by(ProcessingJob.created_at.desc())
        .limit(50)
        .all()
    )

    results = []
    for j in jobs:
        doc_name = "Unknown Document"
        if j.document:
            doc_name = j.document.original_filename
        results.append(
            JobResponse(
                id=j.id,
                document_id=j.document_id,
                document_name=doc_name,
                job_type=j.job_type,
                current_status=j.status,
                progress=j.progress,
                creation_time=j.created_at,
                processing_duration=j.duration_seconds,
                error_message=j.error_message,
            )
        )
    return results


@router.get("/{job_id}", response_model=JobResponse, summary="Get job details")
def get_job_details(job_id: str, db: Session = Depends(get_db)):
    j = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    if not j:
        raise HTTPException(status_code=404, detail="Job not found.")

    doc_name = j.document.original_filename if j.document else "Unknown Document"
    return JobResponse(
        id=j.id,
        document_id=j.document_id,
        document_name=doc_name,
        job_type=j.job_type,
        current_status=j.status,
        progress=j.progress,
        creation_time=j.created_at,
        processing_duration=j.duration_seconds,
        error_message=j.error_message,
    )
