from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import SearchResponse, SearchRequest
from backend.app.search.search_engine import search_engine

router = APIRouter()


@router.get("", response_model=SearchResponse, summary="Search documents (Keyword & Semantic)")
def search_documents_get(
    q: str = Query("", description="Search query string"),
    type: str = Query("all", description="Search mode: 'all', 'keyword', or 'semantic'"),
    doc_type: Optional[str] = Query(None, description="Filter by classification, e.g. Invoice, Receipt"),
    supplier: Optional[str] = Query(None, description="Filter by supplier name"),
    min_amount: Optional[float] = Query(None, description="Minimum invoice total"),
    max_amount: Optional[float] = Query(None, description="Maximum invoice total"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    doc_types = [doc_type] if doc_type else None
    results = search_engine.search(
        db=db,
        query=q,
        search_type=type,
        document_types=doc_types,
        supplier=supplier,
        min_amount=min_amount,
        max_amount=max_amount,
        limit=limit,
    )
    return SearchResponse(
        query=q,
        search_type=type,
        total_results=len(results),
        results=results,
    )


@router.post("", response_model=SearchResponse, summary="Advanced search documents")
def search_documents_post(
    body: SearchRequest,
    db: Session = Depends(get_db),
):
    results = search_engine.search(
        db=db,
        query=body.query,
        search_type=body.search_type,
        document_types=body.document_types,
        supplier=body.supplier,
        min_amount=body.min_amount,
        max_amount=body.max_amount,
        limit=body.limit,
    )
    return SearchResponse(
        query=body.query,
        search_type=body.search_type,
        total_results=len(results),
        results=results,
    )
