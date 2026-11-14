import os
import json
import re
from typing import Dict, Any, Optional, Tuple, List
from pydantic import ValidationError
from backend.app.core.config import settings
from backend.app.schemas.schemas import InvoiceExtractionSchema, LineItemSchema
from backend.app.processors.normalizer import text_normalizer
from backend.app.ai.prompts import INVOICE_EXTRACTION_SYSTEM_PROMPT


class BaseAIProvider:
    def extract_invoice(self, text: str) -> Dict[str, Any]:
        raise NotImplementedError


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=INVOICE_EXTRACTION_SYSTEM_PROMPT,
                generation_config={"response_mime_type": "application/json"},
            )
        return self._model

    def extract_invoice(self, text: str) -> Dict[str, Any]:
        model = self._get_model()
        response = model.generate_content(f"Extract invoice data from this document:\n\n{text}")
        content = response.text.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def extract_invoice(self, text: str) -> Dict[str, Any]:
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model_name,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": INVOICE_EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Extract invoice data from this document:\n\n{text}"},
            ],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        return json.loads(content)


class HeuristicFallbackProvider(BaseAIProvider):
    """
    Intelligent heuristic regex/layout extraction engine when live LLM API keys are not provided.
    Does not hallucinate or use static mock data — extracts real text patterns directly from the document.
    """

    def extract_invoice(self, text: str) -> Dict[str, Any]:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # 1. Invoice Number
        inv_no = None
        inv_match = re.search(r"(?:invoice\s*(?:no|number|#)|\binv\b\s*#?)\s*[:.\-]?\s*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if not inv_match:
            inv_match = re.search(r"\binvoice\b\s*[:.\-]\s*([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
        if inv_match:
            val = inv_match.group(1).strip()
            if val.lower() not in ("invoice", "number", "date", "tax", "total", "copy", "oice"):
                inv_no = val

        # 2. Invoice Date
        inv_date = None
        date_match = re.search(r"(?:date|invoice\s*date|dated)\s*[:.\-]?\s*(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4})", text, re.IGNORECASE)
        if date_match:
            inv_date = date_match.group(1).strip()

        # 3. Currency
        currency = "USD"
        if "BDT" in text or "৳" in text:
            currency = "BDT"
        elif "EUR" in text or "€" in text:
            currency = "EUR"
        elif "GBP" in text or "£" in text:
            currency = "GBP"
        elif "INR" in text or "₹" in text:
            currency = "INR"

        # 4. Supplier & Customer
        supplier_name = None
        customer_name = None
        supp_match = re.search(r"(?:from|supplier|vendor|biller)\s*[:.\-]?\s*([^\n,]+)", text, re.IGNORECASE)
        if supp_match:
            supplier_name = supp_match.group(1).strip()
        elif len(lines) > 0 and "invoice" not in lines[0].lower():
            supplier_name = lines[0].strip()

        cust_match = re.search(r"(?:bill\s*to|customer|client|sold\s*to)\s*[:.\-]?\s*([^\n,]+)", text, re.IGNORECASE)
        if cust_match:
            customer_name = cust_match.group(1).strip()

        # 5. Amounts
        subtotal = None
        tax = None
        total_amount = None

        sub_match = re.search(r"(?:\bsubtotal\b|\bsub\s*total\b|\bnet\s*amount\b)\s*[:.\-]?\s*([$€£৳₹]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if sub_match:
            subtotal = text_normalizer.clean_currency_amount(sub_match.group(1))

        tax_match = re.search(r"(?:\btax\b|\bvat\b|\bgst\b|\bsales\s*tax\b)\s*(?:\([^)]*\))?\s*[:.\-]?\s*([$€£৳₹]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tax_match:
            tax = text_normalizer.clean_currency_amount(tax_match.group(1))

        tot_match = re.search(r"(?:\btotal\s*amount\b|\bgrand\s*total\b|\bamount\s*due\b|\bbalance\s*due\b|\btotal\b)\s*[:.\-]?\s*([$€£৳₹]?\s*[\d,]+(?:\.\d{2})?)", text, re.IGNORECASE)
        if tot_match:
            total_amount = text_normalizer.clean_currency_amount(tot_match.group(1))

        # 6. Line Items Extraction Heuristics
        line_items = []
        item_patterns = re.findall(r"([A-Za-z0-9\s\-_/]+?)\s+(\d+(?:\.\d+)?)\s+([$€£৳₹]?\s*[\d,]+(?:\.\d{2})?)\s+([$€£৳₹]?\s*[\d,]+(?:\.\d{2})?)", text)
        for p in item_patterns:
            desc = p[0].strip()
            if any(w in desc.lower() for w in ["subtotal", "total", "tax", "vat", "invoice", "date", "description", "quantity"]):
                continue
            try:
                qty = float(p[1])
                uprice = text_normalizer.clean_currency_amount(p[2])
                amt = text_normalizer.clean_currency_amount(p[3])
                if uprice > 0 or amt > 0:
                    line_items.append({
                        "description": desc,
                        "quantity": qty,
                        "unit_price": uprice,
                        "tax": None,
                        "amount": amt if amt > 0 else round(qty * uprice, 2),
                        "confidence": 0.85,
                        "source_page": 1,
                    })
            except Exception:
                pass

        if subtotal is None and line_items:
            subtotal = round(sum(item["amount"] for item in line_items), 2)
        if total_amount is None:
            if subtotal is not None and tax is not None:
                total_amount = round(subtotal + tax, 2)
            elif subtotal is not None:
                total_amount = subtotal

        missing_fields = []
        if not inv_no:
            missing_fields.append("invoice_number")
        if not inv_date:
            missing_fields.append("invoice_date")
        if not supplier_name:
            missing_fields.append("supplier_name")
        if total_amount is None:
            missing_fields.append("total_amount")

        return {
            "invoice_number": inv_no,
            "invoice_date": inv_date,
            "supplier_name": supplier_name,
            "customer_name": customer_name,
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total_amount,
            "currency": currency,
            "line_items": line_items,
            "missing_fields": missing_fields,
            "uncertain_fields": [],
            "confidence": {
                "invoice_number": 0.88 if inv_no else 0.0,
                "invoice_date": 0.85 if inv_date else 0.0,
                "supplier_name": 0.82 if supplier_name else 0.0,
                "total_amount": 0.90 if total_amount is not None else 0.0,
            },
            "source_references": [
                {"field": "total_amount", "page": 1, "snippet": f"Total: {total_amount}"}
            ] if total_amount is not None else [],
            "requires_manual_review": len(missing_fields) > 0,
        }


class AIExtractionEngine:
    def __init__(self):
        self._provider = None

    def get_provider(self) -> BaseAIProvider:
        if self._provider is None:
            provider_name = (settings.AI_PROVIDER or "").lower()
            gemini_key = (settings.GEMINI_API_KEY or "").strip()
            openai_key = (settings.OPENAI_API_KEY or "").strip()

            if provider_name == "gemini" and gemini_key:
                try:
                    self._provider = GeminiProvider(gemini_key, settings.AI_MODEL)
                except Exception:
                    self._provider = HeuristicFallbackProvider()
            elif provider_name == "openai" and openai_key:
                try:
                    self._provider = OpenAIProvider(openai_key, settings.AI_MODEL)
                except Exception:
                    self._provider = HeuristicFallbackProvider()
            else:
                self._provider = HeuristicFallbackProvider()
        return self._provider

    def extract(self, text: str) -> Tuple[InvoiceExtractionSchema, Dict[str, Any], str]:
        provider = self.get_provider()
        provider_name = type(provider).__name__
        raw_result = {}
        try:
            raw_result = provider.extract_invoice(text)
        except Exception as e:
            fallback = HeuristicFallbackProvider()
            raw_result = fallback.extract_invoice(text)
            provider_name = f"HeuristicFallbackProvider (recovered from: {type(e).__name__})"

        try:
            validated = InvoiceExtractionSchema(**raw_result)
        except ValidationError:
            cleaned_line_items = []
            for item in raw_result.get("line_items", []):
                try:
                    cleaned_line_items.append(LineItemSchema(**item))
                except Exception:
                    pass
            raw_result["line_items"] = [item.model_dump() for item in cleaned_line_items]
            validated = InvoiceExtractionSchema(**raw_result)

        return validated, raw_result, provider_name


ai_extraction_engine = AIExtractionEngine()
