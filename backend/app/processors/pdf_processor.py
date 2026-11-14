import os
import io
from typing import List, Dict, Any, Generator, Tuple
import pdfplumber
from pypdf import PdfReader
from backend.app.ocr.ocr_engine import ocr_engine


class PDFProcessor:
    """
    High-performance, memory-efficient PDF processing engine.
    Supports digital PDFs, scanned PDFs (with OCR), mixed pages, and up to 1,000+ page documents.
    """

    def __init__(self, chunk_size: int = 25):
        self.chunk_size = chunk_size

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extracts PDF document metadata and total page count."""
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            meta = reader.metadata or {}
            return {
                "page_count": num_pages,
                "title": str(meta.get("/Title", "") or ""),
                "author": str(meta.get("/Author", "") or ""),
                "creator": str(meta.get("/Creator", "") or ""),
                "producer": str(meta.get("/Producer", "") or ""),
                "creation_date": str(meta.get("/CreationDate", "") or ""),
            }
        except Exception as e:
            # Fallback with pdfplumber
            try:
                with pdfplumber.open(file_path) as pdf:
                    return {
                        "page_count": len(pdf.pages),
                        "title": str(pdf.metadata.get("Title", "") or ""),
                        "author": str(pdf.metadata.get("Author", "") or ""),
                        "creator": str(pdf.metadata.get("Creator", "") or ""),
                        "producer": str(pdf.metadata.get("Producer", "") or ""),
                        "creation_date": str(pdf.metadata.get("CreationDate", "") or ""),
                    }
            except Exception:
                return {"page_count": 1, "title": "", "author": "", "creator": "", "error": str(e)}

    def process_pdf_pages(
        self, file_path: str, max_pages_to_process: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Processes PDF page-by-page to prevent high memory consumption on large (1,000-page) documents.
        Identifies digital vs scanned pages, applies OCR when needed, and extracts tables.
        """
        pages_result = []

        try:
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                pages_to_read = min(total_pages, max_pages_to_process)

                for page_idx in range(pages_to_read):
                    page_num = page_idx + 1
                    page = pdf.pages[page_idx]

                    # 1. Try digital text extraction
                    digital_text = page.extract_text() or ""
                    cleaned_text = digital_text.strip()

                    ocr_applied = False
                    ocr_confidence = None
                    is_empty = False

                    # 2. Check if page contains usable text or is scanned
                    # If digital text has fewer than 15 characters, attempt OCR
                    if len(cleaned_text) < 15:
                        # Render page image for OCR
                        try:
                            # Render to PIL image at reasonable resolution (150 DPI)
                            page_image = page.to_image(resolution=150).original
                            ocr_text, confidence = ocr_engine.extract_text_from_image(page_image)
                            if len(ocr_text.strip()) > len(cleaned_text):
                                cleaned_text = ocr_text.strip()
                                ocr_applied = True
                                ocr_confidence = confidence
                        except Exception:
                            # If rendering fails, keep whatever was extracted
                            pass

                    if not cleaned_text:
                        is_empty = True

                    # 3. Table extraction
                    tables = []
                    try:
                        raw_tables = page.extract_tables()
                        for table in raw_tables:
                            if table:
                                # clean None values
                                cleaned_table = [
                                    [str(cell).strip() if cell is not None else "" for cell in row]
                                    for row in table
                                ]
                                tables.append(cleaned_table)
                    except Exception:
                        tables = []

                    pages_result.append(
                        {
                            "page_number": page_num,
                            "raw_text": cleaned_text,
                            "ocr_applied": ocr_applied,
                            "ocr_confidence": ocr_confidence,
                            "is_empty": is_empty,
                            "tables": tables,
                        }
                    )
        except Exception as e:
            # Fallback using pypdf if pdfplumber fails
            reader = PdfReader(file_path)
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages_result.append(
                    {
                        "page_number": page_idx + 1,
                        "raw_text": text.strip(),
                        "ocr_applied": False,
                        "ocr_confidence": None,
                        "is_empty": len(text.strip()) == 0,
                        "tables": [],
                    }
                )

        return pages_result


pdf_processor = PDFProcessor()
