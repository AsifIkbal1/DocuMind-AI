import os
import json
import csv
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def generate_all_samples():
    base_dir = os.path.abspath("sample_data")
    os.makedirs(os.path.join(base_dir, "pdf"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "scanned"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "excel"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "csv"), exist_ok=True)

    ground_truth = {}

    # -------------------------------------------------------------
    # 1. Digital PDF 1: Valid Standard Invoice
    # -------------------------------------------------------------
    pdf_path_1 = os.path.join(base_dir, "pdf", "invoice_valid_001.pdf")
    doc = SimpleDocTemplate(pdf_path_1, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(
        "InvoiceTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
    )
    story.append(Paragraph("TAX INVOICE", title_style))
    story.append(Spacer(1, 10))

    meta_text = """
    <b>Invoice Number:</b> INV-2026-001<br/>
    <b>Date:</b> 2026-11-10<br/>
    <b>Supplier:</b> ABC Technologies Ltd.<br/>
    <b>Customer:</b> XYZ Corporation<br/>
    <b>Currency:</b> USD
    """
    story.append(Paragraph(meta_text, styles["Normal"]))
    story.append(Spacer(1, 15))

    data = [
        ["Description", "Qty", "Unit Price", "Amount"],
        ["Cloud Hosting Infrastructure", "2", "2500.00", "5000.00"],
        ["Database Clustering Engine", "1", "5000.00", "5000.00"],
    ]
    t = Table(data, colWidths=[240, 60, 100, 100])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 15))

    tot_text = """
    <b>Subtotal:</b> 10000.00<br/>
    <b>Tax (15%):</b> 1500.00<br/>
    <b>Total Amount:</b> 11500.00
    """
    story.append(Paragraph(tot_text, styles["Normal"]))
    doc.build(story)

    ground_truth["invoice_valid_001.pdf"] = {
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-11-10",
        "supplier_name": "ABC Technologies Ltd.",
        "customer_name": "XYZ Corporation",
        "subtotal": 10000.00,
        "tax": 1500.00,
        "total_amount": 11500.00,
        "currency": "USD",
        "expected_valid": True,
        "classification": "Invoice",
    }

    # -------------------------------------------------------------
    # 2. Digital PDF 2: Duplicate of 001 with slight name variation
    # -------------------------------------------------------------
    pdf_path_2 = os.path.join(base_dir, "pdf", "invoice_duplicate_001.pdf")
    doc2 = SimpleDocTemplate(pdf_path_2, pagesize=letter)
    story2 = []
    story2.append(Paragraph("TAX INVOICE COPY", title_style))
    story2.append(Spacer(1, 10))
    meta_text2 = """
    <b>Invoice Number:</b> INV-2026-001<br/>
    <b>Date:</b> 2026-11-10<br/>
    <b>Supplier:</b> ABC Technologies Ltd<br/>
    <b>Customer:</b> XYZ Corporation<br/>
    <b>Currency:</b> USD
    """
    story2.append(Paragraph(meta_text2, styles["Normal"]))
    story2.append(Spacer(1, 15))
    story2.append(t)
    story2.append(Spacer(1, 15))
    story2.append(Paragraph(tot_text, styles["Normal"]))
    doc2.build(story2)

    ground_truth["invoice_duplicate_001.pdf"] = {
        "invoice_number": "INV-2026-001",
        "invoice_date": "2026-11-10",
        "supplier_name": "ABC Technologies Ltd",
        "customer_name": "XYZ Corporation",
        "subtotal": 10000.00,
        "tax": 1500.00,
        "total_amount": 11500.00,
        "currency": "USD",
        "expected_duplicate": True,
        "classification": "Invoice",
    }

    # -------------------------------------------------------------
    # 3. Digital PDF 3: Invalid Calculation (Math Error)
    # -------------------------------------------------------------
    pdf_path_3 = os.path.join(base_dir, "pdf", "invoice_math_error_002.pdf")
    doc3 = SimpleDocTemplate(pdf_path_3, pagesize=letter)
    story3 = []
    story3.append(Paragraph("INVOICE WITH MATH ERROR", title_style))
    story3.append(Spacer(1, 10))
    meta_text3 = """
    <b>Invoice Number:</b> INV-2026-002<br/>
    <b>Date:</b> 2026-11-11<br/>
    <b>Supplier:</b> Global Telecom Inc.<br/>
    <b>Customer:</b> Acme Enterprises<br/>
    <b>Currency:</b> USD
    """
    story3.append(Paragraph(meta_text3, styles["Normal"]))
    story3.append(Spacer(1, 15))

    data3 = [
        ["Description", "Qty", "Unit Price", "Amount"],
        ["Dedicated Fiber Line", "1", "4000.00", "4000.00"],
        ["VoIP Gateway Setup", "2", "500.00", "1000.00"],
    ]
    t3 = Table(data3, colWidths=[240, 60, 100, 100])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    story3.append(t3)
    story3.append(Spacer(1, 15))

    # Intentionally incorrect total: Subtotal 5000 + Tax 500 != 6200.00
    tot_text3 = """
    <b>Subtotal:</b> 5000.00<br/>
    <b>Tax:</b> 500.00<br/>
    <b>Total Amount:</b> 6200.00
    """
    story3.append(Paragraph(tot_text3, styles["Normal"]))
    doc3.build(story3)

    ground_truth["invoice_math_error_002.pdf"] = {
        "invoice_number": "INV-2026-002",
        "invoice_date": "2026-11-11",
        "supplier_name": "Global Telecom Inc.",
        "customer_name": "Acme Enterprises",
        "subtotal": 5000.00,
        "tax": 500.00,
        "total_amount": 6200.00,
        "expected_valid": False,
        "expected_error": "CALCULATION_MISMATCH",
        "classification": "Invoice",
    }

    # -------------------------------------------------------------
    # 4. Scanned PDF (Rendered Image Embedded in PDF)
    # -------------------------------------------------------------
    scanned_pdf_path = os.path.join(base_dir, "scanned", "scanned_receipt_003.pdf")
    # Create an image that looks like a paper receipt
    img = Image.new("RGB", (600, 800), color=(250, 248, 245))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 580, 780], outline=(150, 150, 150), width=2)
    draw.text((50, 50), "OFFICIAL RECEIPT", fill=(30, 30, 30))
    draw.text((50, 90), "Receipt Number: REC-2026-8801", fill=(30, 30, 30))
    draw.text((50, 120), "Date: 2026-11-12", fill=(30, 30, 30))
    draw.text((50, 150), "Supplier: Metro Office Supplies", fill=(30, 30, 30))
    draw.text((50, 180), "Customer: Alpha Holdings", fill=(30, 30, 30))
    draw.text((50, 230), "Item: Premium Printer Toner x 2 @ 150.00 = 300.00", fill=(30, 30, 30))
    draw.text((50, 270), "Subtotal: 300.00", fill=(30, 30, 30))
    draw.text((50, 300), "Tax: 30.00", fill=(30, 30, 30))
    draw.text((50, 340), "Total Amount: 330.00 USD", fill=(30, 30, 30))

    img_temp_path = os.path.join(base_dir, "images", "temp_receipt.png")
    img.save(img_temp_path)

    # Embed as pure image PDF
    c = canvas.Canvas(scanned_pdf_path, pagesize=(600, 800))
    c.drawImage(img_temp_path, 0, 0, width=600, height=800)
    c.save()

    ground_truth["scanned_receipt_003.pdf"] = {
        "invoice_number": "REC-2026-8801",
        "invoice_date": "2026-11-12",
        "supplier_name": "Metro Office Supplies",
        "customer_name": "Alpha Holdings",
        "total_amount": 330.00,
        "classification": "Receipt",
    }

    # -------------------------------------------------------------
    # 5. Standalone Image (PNG & JPG)
    # -------------------------------------------------------------
    img_path = os.path.join(base_dir, "images", "invoice_image_004.png")
    img4 = Image.new("RGB", (700, 900), color=(255, 255, 255))
    d4 = ImageDraw.Draw(img4)
    d4.text((60, 60), "INVOICE", fill=(0, 0, 0))
    d4.text((60, 100), "Invoice Number: INV-2026-004", fill=(0, 0, 0))
    d4.text((60, 130), "Date: 2026-11-13", fill=(0, 0, 0))
    d4.text((60, 160), "Supplier: Apex Cyber Security", fill=(0, 0, 0))
    d4.text((60, 190), "Customer: Enterprise Bank Ltd", fill=(0, 0, 0))
    d4.text((60, 240), "Description: Penetration Testing Services", fill=(0, 0, 0))
    d4.text((60, 270), "Subtotal: 8000.00", fill=(0, 0, 0))
    d4.text((60, 300), "Tax: 800.00", fill=(0, 0, 0))
    d4.text((60, 340), "Total Amount: 8800.00 USD", fill=(0, 0, 0))
    img4.save(img_path)

    # Also save as JPG
    img4.save(os.path.join(base_dir, "images", "invoice_image_004.jpg"))

    ground_truth["invoice_image_004.png"] = {
        "invoice_number": "INV-2026-004",
        "invoice_date": "2026-11-13",
        "supplier_name": "Apex Cyber Security",
        "customer_name": "Enterprise Bank Ltd",
        "subtotal": 8000.00,
        "tax": 800.00,
        "total_amount": 8800.00,
        "classification": "Invoice",
    }

    # -------------------------------------------------------------
    # 6. Excel Workbook (Multi-sheet with duplicates & reconciliation targets)
    # -------------------------------------------------------------
    excel_path = os.path.join(base_dir, "excel", "monthly_reconciliation_2026.xlsx")
    writer = pd.ExcelWriter(excel_path, engine="openpyxl")

    # Sheet 1: Invoices Ledger
    df_ledger = pd.DataFrame(
        [
            {
                "Invoice Number": "INV-2026-001",
                "Date": "2026-11-10",
                "Supplier": "ABC Technologies Ltd.",
                "Customer": "XYZ Corporation",
                "Subtotal": 10000.00,
                "Tax": 1500.00,
                "Total Amount": 11500.00,
            },
            {
                "Invoice Number": "INV-2026-002",
                "Date": "2026-11-11",
                "Supplier": "Global Telecom Inc.",
                "Customer": "Acme Enterprises",
                "Subtotal": 5000.00,
                "Tax": 500.00,
                "Total Amount": 5500.00,  # Note: in PDF total was wrong (6200.00), in Excel ledger it is correct (5500.00)!
            },
            {
                "Invoice Number": "INV-2026-004",
                "Date": "2026-11-13",
                "Supplier": "Apex Cyber Security",
                "Customer": "Enterprise Bank Ltd",
                "Subtotal": 8000.00,
                "Tax": 800.00,
                "Total Amount": 8800.00,
            },
            {
                "Invoice Number": "INV-2026-999",
                "Date": "2026-11-05",
                "Supplier": "Missing In PDF Corp",
                "Customer": "Test Client",
                "Subtotal": 1200.00,
                "Tax": 120.00,
                "Total Amount": 1320.00,
            },
            # Intentionally duplicate row to test duplicate row detection
            {
                "Invoice Number": "INV-2026-001",
                "Date": "2026-11-10",
                "Supplier": "ABC Technologies Ltd.",
                "Customer": "XYZ Corporation",
                "Subtotal": 10000.00,
                "Tax": 1500.00,
                "Total Amount": 11500.00,
            },
        ]
    )
    df_ledger.to_excel(writer, sheet_name="Invoice_Ledger", index=False)

    # Sheet 2: Department Summary
    df_dept = pd.DataFrame(
        [
            {"Department": "IT Infrastructure", "Budget": 50000.00, "Spent": 20300.00},
            {"Department": "Security", "Budget": 30000.00, "Spent": 8800.00},
        ]
    )
    df_dept.to_excel(writer, sheet_name="Dept_Summary", index=False)
    writer.close()

    ground_truth["monthly_reconciliation_2026.xlsx"] = {
        "sheets": ["Invoice_Ledger", "Dept_Summary"],
        "records_count": 5,
        "duplicate_rows": 1,
        "classification": "Spreadsheet",
    }

    # -------------------------------------------------------------
    # 7. CSV File
    # -------------------------------------------------------------
    csv_path = os.path.join(base_dir, "csv", "vendor_payments.csv")
    with open(csv_path, "w", newline="") as f:
        writer_csv = csv.writer(f)
        writer_csv.writerow(["invoice_number", "date", "supplier", "total_amount", "status"])
        writer_csv.writerow(["INV-2026-001", "2026-11-10", "ABC Technologies Ltd.", 11500.00, "PAID"])
        writer_csv.writerow(["INV-2026-002", "2026-11-11", "Global Telecom Inc.", 5500.00, "PENDING"])
        writer_csv.writerow(["INV-2026-004", "2026-11-13", "Apex Cyber Security", 8800.00, "PAID"])

    # -------------------------------------------------------------
    # 8. Save Ground Truth JSON
    # -------------------------------------------------------------
    with open(os.path.join(base_dir, "ground_truth.json"), "w") as f:
        json.dump(ground_truth, f, indent=2)

    print("All sample datasets generated successfully in sample_data/.")


if __name__ == "__main__":
    generate_all_samples()

