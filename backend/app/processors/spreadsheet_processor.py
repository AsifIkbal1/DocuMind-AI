import os
import io
import pandas as pd
from typing import List, Dict, Any, Optional


class SpreadsheetProcessor:
    """
    Parses XLSX, XLS, and CSV files:
    - Multi-sheet support with sheet names
    - Header detection & flexible column mapping
    - Data type preservation (numbers, dates)
    - Row reference tracking (sheet_name, row_number)
    - Duplicate row detection within spreadsheets
    """

    COLUMN_SYNONYMS = {
        "invoice_number": ["inv #", "invoice #", "invoice no", "inv no", "invoice_number", "bill no", "bill number", "invoice_id"],
        "date": ["date", "invoice date", "bill date", "inv date", "transaction date", "created at", "doc date"],
        "supplier": ["supplier", "vendor", "supplier name", "vendor name", "seller", "from", "company", "biller"],
        "customer": ["customer", "client", "customer name", "client name", "buyer", "bill to", "recipient"],
        "subtotal": ["subtotal", "sub total", "net amount", "taxable amount", "before tax"],
        "tax": ["tax", "vat", "gst", "sales tax", "tax amount", "total tax"],
        "total_amount": ["total", "total amount", "grand total", "invoice total", "gross amount", "amount due", "final amount"],
        "currency": ["currency", "curr", "ccy"],
        "description": ["description", "item", "product", "details", "particulars", "service"],
        "quantity": ["qty", "quantity", "units", "count"],
        "unit_price": ["unit price", "rate", "price", "unit cost", "cost per unit"],
        "amount": ["amount", "line total", "total price", "item total", "extended price"]
    }

    def _normalize_header(self, header: str) -> str:
        clean = str(header).strip().lower().replace("_", " ").replace("-", " ")
        for standard_key, synonyms in self.COLUMN_SYNONYMS.items():
            if clean in synonyms or any(s in clean for s in synonyms):
                return standard_key
        return clean.replace(" ", "_")

    def process_file(self, file_path: str, file_format: str) -> Dict[str, Any]:
        """
        Processes spreadsheet or CSV file.
        Returns sheets metadata, extracted records, and duplicate row flags.
        """
        sheets_data = {}
        all_records = []
        duplicate_rows_found = []

        if file_format == "csv":
            try:
                df = pd.read_csv(file_path)
            except Exception:
                # Retry with latin-1 encoding if utf-8 fails
                df = pd.read_csv(file_path, encoding="latin-1")
            sheet_map = {"Sheet1": df}
        elif file_format in ("xlsx", "xls"):
            engine = "openpyxl" if file_format == "xlsx" else "xlrd"
            excel_file = pd.ExcelFile(file_path, engine=engine)
            sheet_map = {sheet_name: excel_file.parse(sheet_name) for sheet_name in excel_file.sheet_names}
        else:
            raise ValueError(f"Unsupported spreadsheet format: {file_format}")

        for sheet_name, df in sheet_map.items():
            # Drop completely empty rows and columns
            cleaned_df = df.dropna(how="all").dropna(how="all", axis=1)
            if cleaned_df.empty:
                sheets_data[sheet_name] = {"row_count": 0, "columns": [], "records": []}
                continue

            # Identify duplicates within sheet
            duplicated_mask = cleaned_df.duplicated(keep=False)
            dup_indices = cleaned_df[duplicated_mask].index.tolist()
            if dup_indices:
                duplicate_rows_found.extend([{"sheet": sheet_name, "row_index": int(idx) + 2} for idx in dup_indices])

            # Normalize column names
            normalized_cols = {col: self._normalize_header(col) for col in cleaned_df.columns}
            renamed_df = cleaned_df.rename(columns=normalized_cols)

            sheet_records = []
            for row_idx, row in renamed_df.iterrows():
                # Convert row to dict, converting NaNs to None
                row_dict = {}
                for k, v in row.items():
                    if pd.isna(v):
                        row_dict[str(k)] = None
                    elif isinstance(v, (pd.Timestamp, pd.DatetimeIndex)):
                        row_dict[str(k)] = v.strftime("%Y-%m-%d")
                    elif isinstance(v, (int, float)):
                        row_dict[str(k)] = round(float(v), 2)
                    else:
                        row_dict[str(k)] = str(v).strip()

                row_dict["_sheet_name"] = sheet_name
                row_dict["_row_number"] = int(row_idx) + 2  # 1-indexed Excel row after header
                sheet_records.append(row_dict)
                all_records.append(row_dict)

            sheets_data[sheet_name] = {
                "row_count": len(sheet_records),
                "columns": [str(c) for c in cleaned_df.columns],
                "normalized_columns": list(renamed_df.columns),
                "records": sheet_records,
            }

        # Build combined text representation for downstream processing
        text_lines = []
        for sheet_name, data in sheets_data.items():
            text_lines.append(f"--- SHEET: {sheet_name} ({data['row_count']} rows) ---")
            for rec in data["records"][:100]:  # Up to first 100 rows preview in text
                formatted_pairs = [f"{k}: {v}" for k, v in rec.items() if not k.startswith("_") and v is not None]
                text_lines.append(f"[Row {rec['_row_number']}] " + " | ".join(formatted_pairs))

        return {
            "sheets": sheets_data,
            "all_records": all_records,
            "total_records": len(all_records),
            "duplicate_rows": duplicate_rows_found,
            "combined_text": "\n".join(text_lines),
        }


spreadsheet_processor = SpreadsheetProcessor()
