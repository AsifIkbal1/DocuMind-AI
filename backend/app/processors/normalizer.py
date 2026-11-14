import re
import unicodedata
from typing import Dict, Any


class TextNormalizer:
    """
    Normalizes extracted text across formats:
    - Unicode NFKC normalization
    - Multiple whitespace & newline cleanup
    - Currency symbol standardization
    - Punctuation normalization
    """

    CURRENCY_MAP = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "¥": "JPY",
        "৳": "BDT",
        "₹": "INR",
        "C$": "CAD",
        "A$": "AUD",
    }

    def normalize(self, text: str) -> str:
        if not text:
            return ""

        # 1. Unicode NFKC normalization (turns special quotes, non-breaking spaces into standard)
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Replace non-breaking spaces
        normalized = normalized.replace("\u00a0", " ").replace("\u200b", "")

        # 3. Clean carriage returns
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

        # 4. Collapse runs of 3+ newlines into 2
        normalized = re.sub(r"\n{3,}", "\n\n", normalized)

        # 5. Collapse multiple horizontal spaces
        normalized = re.sub(r"[ \t]+", " ", normalized)

        return normalized.strip()

    def clean_currency_amount(self, value_str: str) -> float:
        """Converts strings like '$12,450.50' or '12.450,50' or 'BDT 1,500.00' into a float."""
        if not value_str:
            return 0.0

        clean = str(value_str).strip()
        # Remove currency symbols and letters
        clean = re.sub(r"[^\d.,\-]", "", clean)

        # If has both dot and comma
        if "." in clean and "," in clean:
            if clean.rfind(".") > clean.rfind(","):
                # standard 1,234.56
                clean = clean.replace(",", "")
            else:
                # European 1.234,56
                clean = clean.replace(".", "").replace(",", ".")
        elif "," in clean and clean.count(",") == 1 and len(clean.split(",")[1]) == 2:
            # European decimal 1234,56
            clean = clean.replace(",", ".")
        else:
            clean = clean.replace(",", "")

        try:
            return float(clean)
        except ValueError:
            return 0.0


text_normalizer = TextNormalizer()
