import re
import numpy as np
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.models.entities import Document, Invoice, ExtractedText, ValidationResult
from backend.app.schemas.schemas import SearchResultItem, SearchResponse


class SearchEngine:
    """
    Unified Search Engine supporting:
    1. Exact & Structured Keyword Search (SQL filters + full-text matching)
    2. Vector Semantic Search (TF-IDF vector space + cosine similarity embeddings)
    3. Metadata filtering (amounts, date ranges, suppliers, document types)
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        self._is_fitted = False
        self._corpus_doc_ids = []
        self._corpus_matrix = None

    def _build_document_representation(self, doc: Document) -> str:
        parts = [
            doc.original_filename,
            doc.document_classification,
            doc.file_format,
        ]
        if doc.invoice:
            inv = doc.invoice
            if inv.invoice_number:
                parts.append(f"invoice {inv.invoice_number}")
            if inv.supplier_name:
                parts.append(f"supplier {inv.supplier_name}")
            if inv.customer_name:
                parts.append(f"customer {inv.customer_name}")
            if inv.total_amount is not None:
                parts.append(f"total amount {inv.total_amount} {inv.currency}")
            for item in inv.line_items:
                parts.append(f"{item.description} qty {item.quantity} price {item.unit_price}")
        if doc.extracted_text_rel:
            parts.append(doc.extracted_text_rel.normalized_text[:1000])
        return " ".join(parts)

    def fit_corpus(self, db: Session):
        """Indexes all documents into the vector space for semantic retrieval."""
        docs = db.query(Document).all()
        if not docs:
            self._is_fitted = False
            return

        corpus = []
        self._corpus_doc_ids = []
        for doc in docs:
            rep = self._build_document_representation(doc)
            corpus.append(rep)
            self._corpus_doc_ids.append(doc.id)

        if corpus:
            try:
                self._corpus_matrix = self.vectorizer.fit_transform(corpus)
                self._is_fitted = True
            except ValueError:
                self._is_fitted = False

    def search(
        self,
        db: Session,
        query: str,
        search_type: str = "all",
        document_types: Optional[List[str]] = None,
        supplier: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        limit: int = 20,
    ) -> List[SearchResultItem]:
        """
        Executes hybrid keyword + semantic search with metadata filters.
        """
        all_docs = db.query(Document).all()
        if not all_docs:
            return []

        # 1. Apply metadata pre-filters
        candidate_docs = []
        for doc in all_docs:
            if document_types and doc.document_classification not in document_types:
                continue

            inv = doc.invoice
            if supplier and inv:
                if not inv.supplier_name or supplier.lower() not in inv.supplier_name.lower():
                    continue

            if min_amount is not None:
                if not inv or inv.total_amount is None or inv.total_amount < min_amount:
                    continue

            if max_amount is not None:
                if not inv or inv.total_amount is None or inv.total_amount > max_amount:
                    continue

            candidate_docs.append(doc)

        if not candidate_docs:
            return []

        results = []
        clean_q = query.strip().lower()

        # Check for natural language numeric intents like "greater than 50000"
        nl_amount_match = re.search(r"(?:greater than|more than|>|above)\s*([\d,]+)", clean_q)
        nl_min_amount = None
        if nl_amount_match:
            try:
                nl_min_amount = float(nl_amount_match.group(1).replace(",", ""))
            except ValueError:
                pass

        # Always re-fit corpus to include newly uploaded documents
        self.fit_corpus(db)

        # 2. Vector Semantic Scoring
        semantic_scores = {}
        if self._is_fitted and clean_q:
            try:
                query_vec = self.vectorizer.transform([query])
                sims = cosine_similarity(query_vec, self._corpus_matrix).flatten()
                for doc_id, sim in zip(self._corpus_doc_ids, sims):
                    semantic_scores[doc_id] = float(sim)
            except Exception:
                pass

        # 3. Combine scores & construct results
        for doc in candidate_docs:
            inv = doc.invoice
            inv_dict = (
                {
                    "invoice_number": inv.invoice_number,
                    "invoice_date": inv.invoice_date,
                    "supplier_name": inv.supplier_name,
                    "customer_name": inv.customer_name,
                    "total_amount": inv.total_amount,
                    "currency": inv.currency,
                }
                if inv
                else None
            )

            # Natural language filter filter check
            if nl_min_amount is not None and inv and inv.total_amount:
                if inv.total_amount <= nl_min_amount:
                    continue

            # Exact keyword match
            text_corpus = self._build_document_representation(doc).lower()
            keyword_score = 0.0
            matched_by = "keyword"

            if clean_q:
                terms = clean_q.split()
                matched_terms = sum(1 for term in terms if term in text_corpus)
                keyword_score = matched_terms / len(terms) if terms else 0.0

            sem_score = semantic_scores.get(doc.id, 0.0)

            # Hybrid scoring
            if search_type == "keyword":
                final_score = keyword_score
                matched_by = "keyword"
            elif search_type == "semantic":
                final_score = sem_score
                matched_by = "semantic"
            else:
                final_score = max(keyword_score * 1.2, sem_score)
                matched_by = "semantic" if sem_score > keyword_score else "keyword"

            if not clean_q or final_score > 0.05 or (clean_q and clean_q in text_corpus):
                # Build snippet
                snippet = ""
                if doc.extracted_text_rel and doc.extracted_text_rel.normalized_text:
                    sample = doc.extracted_text_rel.normalized_text
                    if clean_q and clean_q in sample.lower():
                        idx = sample.lower().find(clean_q)
                        start = max(0, idx - 40)
                        end = min(len(sample), idx + 80)
                        snippet = "..." + sample[start:end].replace("\n", " ") + "..."
                    else:
                        snippet = sample[:120].replace("\n", " ") + "..."
                else:
                    snippet = f"Document: {doc.original_filename} ({doc.document_classification})"

                results.append(
                    SearchResultItem(
                        document_id=doc.id,
                        filename=doc.original_filename,
                        document_type=doc.document_classification,
                        file_format=doc.file_format,
                        upload_time=doc.upload_time,
                        relevance_score=round(final_score, 3),
                        matched_by=matched_by,
                        snippet=snippet,
                        invoice_details=inv_dict,
                    )
                )

        # Sort by relevance score descending
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:limit]


search_engine = SearchEngine()
