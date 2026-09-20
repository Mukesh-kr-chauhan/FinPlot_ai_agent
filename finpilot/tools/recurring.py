from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List
from agent.state import Transaction, RecurringPattern


class RecurringEngine:
    """Detects repeated payments, periodic subscriptions, and estimates future obligations."""

    KNOWN_SUBSCRIPTION_IDENTIFIERS = [
        "netflix", "spotify", "prime", "amazon prime", "youtube", "hotstar",
        "hulu", "disney", "apple.com", "google storage", "github", "gym", "fitness"
    ]

    @classmethod
    def detect_recurring(cls, transactions: List[Transaction]) -> List[RecurringPattern]:
        expenses = [t for t in transactions if t.transaction_type == "debit"]
        if not expenses:
            return []

        df = pd.DataFrame([t.model_dump() for t in expenses])
        df["date_dt"] = pd.to_datetime(df["date"])

        patterns: List[RecurringPattern] = []

        for merchant, group in df.groupby("description"):
            if len(group) < 2:
                continue

            group = group.sort_values("date_dt")
            intervals = group["date_dt"].diff().dt.days.dropna().tolist()

            if not intervals:
                continue

            avg_interval = float(np.mean(intervals))
            interval_std = float(np.std(intervals)) if len(intervals) > 1 else 0.0

            amounts = group["amount"].tolist()
            avg_amount = float(np.mean(amounts))
            amount_std = float(np.std(amounts)) if len(amounts) > 1 else 0.0
            amount_variation = (amount_std / avg_amount) * 100 if avg_amount > 0 else 0.0

            # Determine frequency profile
            frequency = "Irregular"
            is_periodic = False

            if 5 <= avg_interval <= 9 and interval_std <= 3:
                frequency = "Weekly"
                is_periodic = True
            elif 25 <= avg_interval <= 35 and interval_std <= 6:
                frequency = "Monthly"
                is_periodic = True
            elif 80 <= avg_interval <= 100 and interval_std <= 10:
                frequency = "Quarterly"
                is_periodic = True

            # If periodicity is detected or amounts are nearly identical over reasonable intervals
            if is_periodic and amount_variation <= 15.0:
                # Calculate confidence score
                conf_score = 0.5
                if amount_variation < 2.0:
                    conf_score += 0.25
                if interval_std < 3.0:
                    conf_score += 0.15
                if len(group) >= 3:
                    conf_score += 0.10
                conf_score = min(conf_score, 0.99)

                # Determine if it qualifies as a subscription
                is_sub = False
                desc_lower = merchant.lower()
                has_sub_keyword = any(k in desc_lower for k in cls.KNOWN_SUBSCRIPTION_IDENTIFIERS)
                
                if (has_sub_keyword or group["category"].iloc[0] == "Subscription") and avg_amount < 5000:
                    is_sub = True
                elif frequency in ["Monthly", "Weekly"] and amount_variation < 1.0 and avg_amount < 2000:
                    is_sub = True

                last_date = group["date_dt"].max()
                next_date = last_date + timedelta(days=int(round(avg_interval)))

                patterns.append(RecurringPattern(
                    description=merchant,
                    category=group["category"].iloc[0],
                    occurrences=len(group),
                    average_amount=round(avg_amount, 2),
                    amount_variation=round(amount_variation, 2),
                    average_interval=round(avg_interval, 1),
                    frequency=frequency,
                    confidence=round(conf_score, 2),
                    last_payment=last_date.strftime("%Y-%m-%d"),
                    next_estimated_date=next_date.strftime("%Y-%m-%d"),
                    is_subscription=is_sub
                ))

        patterns.sort(key=lambda x: x.average_amount, reverse=True)
        return patterns