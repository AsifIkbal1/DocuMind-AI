import io
import pytest


def test_health_api(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["backend"] == "healthy"
    assert "ai_provider" in data


def test_document_upload_and_list_api(client):
    with open("sample_data/pdf/invoice_valid_001.pdf", "rb") as f:
        file_content = f.read()
    files = [
        ("files", ("test_upload_valid.pdf", io.BytesIO(file_content), "application/pdf"))
    ]
    res = client.post("/api/documents/upload", files=files)
    assert res.status_code == 200
    uploaded = res.json()
    assert len(uploaded) == 1
    doc_id = uploaded[0]["id"]
    assert uploaded[0]["original_filename"] == "test_upload_valid.pdf"

    # List documents
    res_list = client.get("/api/documents")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["total"] >= 1


def test_manual_correction_api(client, db_session):
    from backend.app.models.entities import Document, Invoice

    doc = Document(
        original_filename="corr_test.pdf",
        file_format="pdf",
        file_size=1000,
        file_hash="corr_hash",
        file_storage_reference="dummy",
    )
    db_session.add(doc)
    db_session.flush()

    inv = Invoice(
        document_id=doc.id,
        invoice_number="OLD-NUM",
        total_amount=100.0,
    )
    db_session.add(inv)
    db_session.commit()

    patch_res = client.patch(
        f"/api/documents/{doc.id}/corrections",
        json={
            "field_name": "invoice_number",
            "corrected_value": "CORRECTED-NUM-2026",
            "reason": "Typo in original OCR scan",
            "reviewer_name": "QA Auditor",
        },
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["status"] == "success"
    assert data["corrected_value"] == "CORRECTED-NUM-2026"


def test_analytics_api(client):
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert "measured_extraction_accuracy" in data
    assert "file_type_distribution" in data


def test_search_api(client):
    res = client.get("/api/search?q=invoice")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
