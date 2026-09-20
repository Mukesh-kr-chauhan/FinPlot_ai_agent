import io
import re
import csv
import pandas as pd
from typing import List, Tuple, Dict
from agent.state import Transaction


class DataNormalizer:
    """Normalizes heterogeneous transaction inputs into an immutable, strictly typed representation."""

    CATEGORY_KEYWORDS: Dict[str, List[str]] = {
        "Housing": ["rent", "maintenance", "landlord", "apartment", "society"],
        "Food": ["swiggy", "zomato", "restaurant", "cafe", "grocery", "supermarket", "starbucks", "mcdonalds", "bakery"],
        "Transport": ["uber", "ola", "metro", "fuel", "petrol", "parking", "train", "flight", "irctc"],
        "Shopping": ["amazon", "flipkart", "myntra", "zara", "clothing", "electronics", "retail", "watch"],
        "Subscription": ["netflix", "spotify", "prime", "youtube", "hotstar", "gym", "apple.com/bill", "cloud"],
        "Utilities": ["electricity", "water", "internet", "broadband", "bescom", "airtel", "jio", "gas"],
        "Healthcare": ["pharmacy", "apollo", "hospital", "clinic", "medplus", "diagnostic", "doctor"],
        "Entertainment": ["cinema", "movie", "bookmyshow", "gaming", "steam", "theatre"],
        "Education": ["udemy", "coursera", "tuition", "books", "course", "college"],
        "Transfer": ["neft", "rtgs", "upi transfer", "self transfer", "wallet"],
    }

    REQUIRED_COLUMNS = ["date", "description", "amount"]

    @classmethod
    def parse_csv(cls, file_content: str | bytes) -> Tuple[List[Transaction], List[str]]:
        errors = []
        if isinstance(file_content, bytes):
            file_content = file_content.decode("utf-8", errors="replace")

        # Strip empty lines and leading/trailing whitespace
        lines = [line.strip() for line in file_content.strip().splitlines() if line.strip()]
        if not lines:
            return [], ["The uploaded CSV file is empty."]

        cleaned_content = "\n".join(lines)

        # Resilient CSV delimiter sniffing
        try:
            sample = cleaned_content[:2048]
            dialect = csv.Sniffer().sniff(sample, delimiters=",\t;|")
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        try:
            df = pd.read_csv(io.StringIO(cleaned_content), sep=delimiter, engine="python")
        except Exception as e:
            # Fallback attempt with standard comma
            try:
                df = pd.read_csv(io.StringIO(cleaned_content), sep=",", engine="python")
            except Exception as e2:
                return [], [f"CSV Engine Failure: {str(e2)}"]

        # Standardize column headers
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        # Column validation
        missing = [rc for rc in cls.REQUIRED_COLUMNS if rc not in df.columns]
        if missing:
            return [], [
                f"Missing mandatory schema columns: {', '.join(missing)}. "
                f"Found columns: {list(df.columns)}. Ensure the header is comma-separated."
            ]

        transactions: List[Transaction] = []

        for idx, row in df.iterrows():
            row_idx = idx + 1

            # Sanitize and validate Date
            raw_date = str(row["date"]).strip()
            # If comma leaked into date string, isolate the date part
            if "," in raw_date:
                raw_date = raw_date.split(",")[0].strip()

            try:
                parsed_date = pd.to_datetime(raw_date).strftime("%Y-%m-%d")
            except Exception:
                errors.append(f"Row {row_idx}: Unparseable date format '{raw_date}'")
                continue

            # Sanitize and validate Amount
            raw_amount = row["amount"]
            try:
                if isinstance(raw_amount, str):
                    raw_amount = raw_amount.replace(",", "").replace("₹", "").replace("$", "").strip()
                amount_float = float(raw_amount)
            except Exception:
                errors.append(f"Row {row_idx}: Non-numeric amount value '{raw_amount}'")
                continue

            desc = str(row["description"]).strip() if pd.notna(row["description"]) else "Unknown Merchant"
            account = str(row.get("account", "Primary")).strip()

            # Determine transaction type
            tx_type = str(row.get("type", "")).strip().lower()
            if not tx_type:
                if amount_float < 0:
                    tx_type = "credit"
                    amount_float = abs(amount_float)
                elif any(k in desc.lower() for k in ["salary", "deposit", "credit", "refund"]):
                    tx_type = "credit"
                else:
                    tx_type = "debit"
            else:
                if tx_type in ["income", "credit", "cr"]:
                    tx_type = "credit"
                else:
                    tx_type = "debit"
                amount_float = abs(amount_float)

            user_category = str(row.get("category", "")).strip() if pd.notna(row.get("category")) else ""
            final_category = cls.categorize(desc, user_category, tx_type)

            tx = Transaction(
                transaction_id=f"tx_{row_idx:05d}",
                date=parsed_date,
                description=desc,
                amount=round(amount_float, 2),
                category=final_category,
                account=account,
                transaction_type=tx_type
            )
            transactions.append(tx)

        transactions.sort(key=lambda x: x.date)
        return transactions, errors

    @classmethod
    def categorize(cls, description: str, existing_category: str = "", tx_type: str = "debit") -> str:
        if existing_category and existing_category.lower() not in ["", "nan", "other", "unknown"]:
            return existing_category.capitalize()

        if tx_type == "credit":
            return "Income"

        desc_lower = description.lower()
        for category, keywords in cls.CATEGORY_KEYWORDS.items():
            for kw in keywords:
                if re.search(rf"\b{re.escape(kw)}", desc_lower):
                    return category

        return "Other"