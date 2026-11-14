import os
import shutil
from backend.app.database.session import SessionLocal, Base, engine
from backend.app.models.entities import Document, User
from backend.app.core.security import get_password_hash
from backend.app.processors.file_validator import compute_file_hash
from backend.app.services.pipeline import pipeline
from backend.app.core.config import settings


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Create admin user
    admin_email = "admin@documind.ai"
    user = db.query(User).filter(User.email == admin_email).first()
    if not user:
        user = User(
            email=admin_email,
            hashed_password=get_password_hash("AdminPass2026!"),
            full_name="Principal Reviewer",
            role="admin",
        )
        db.add(user)
        db.commit()
        print("Default admin user created: admin@documind.ai / AdminPass2026!")

    sample_files = [
        "sample_data/pdf/invoice_valid_001.pdf",
        "sample_data/pdf/invoice_duplicate_001.pdf",
        "sample_data/pdf/invoice_math_error_002.pdf",
        "sample_data/scanned/scanned_receipt_003.pdf",
        "sample_data/images/invoice_image_004.png",
        "sample_data/excel/monthly_reconciliation_2026.xlsx",
        "sample_data/csv/vendor_payments.csv",
    ]

    for src_path in sample_files:
        if not os.path.exists(src_path):
            continue

        filename = os.path.basename(src_path)
        dest_path = os.path.join(settings.UPLOAD_DIR, filename)
        shutil.copyfile(src_path, dest_path)

        fmt = filename.rsplit(".", 1)[1].lower()
        file_hash = compute_file_hash(dest_path)
        size = os.path.getsize(dest_path)

        doc = db.query(Document).filter(Document.original_filename == filename).first()
        if not doc:
            doc = Document(
                original_filename=filename,
                file_format=fmt,
                file_size=size,
                file_hash=file_hash,
                file_storage_reference=os.path.abspath(dest_path),
                processing_status="Queued",
                document_classification="Unknown Document",
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

        pipeline.process_document(doc.id, db)
        print(f"Ingested and processed: {filename}")

    db.close()
    print("Demo dataset seeded successfully!")


if __name__ == "__main__":
    seed_demo_data()

