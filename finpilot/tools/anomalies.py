import numpy as np
import pandas as pd
from typing import List
from agent.state import Transaction, AnomalyRecord


class AnomalyDetector:
    """Robust statistical outlier detection using median baselines and adaptive deviation."""

    @classmethod
    def detect_anomalies(cls, transactions: List[Transaction]) -> List[AnomalyRecord]:
        expenses = [t for t in transactions if t.transaction_type == "debit"]
        if not expenses:
            return []

        df = pd.DataFrame([t.model_dump() for t in expenses])
        detected: dict[str, AnomalyRecord] = {}

        # 1. Category-Aware Detection using Median & Non-distorted baselines
        for category, cat_df in df.groupby("category"):
            amounts = cat_df["amount"].astype(float).values
            if len(amounts) >= 2:
                median_val = float(np.median(amounts))
                mean_val = float(np.mean(amounts))

                # If sample size is small, base normal spending on the lower 75%
                filtered = [x for x in amounts if x < max(amounts)] if len(amounts) >= 3 else amounts
                baseline_ref = float(np.mean(filtered)) if filtered else median_val
                std_ref = float(np.std(filtered)) if len(filtered) > 1 else (baseline_ref * 0.4)

                # Anomaly triggers if transaction is 2.5x the baseline or exceeds baseline + 2*std
                cat_threshold = max(baseline_ref + (2.0 * std_ref), baseline_ref * 2.2)

                for _, row in cat_df.iterrows():
                    amt = float(row["amount"])
                    if amt >= cat_threshold and amt >= 1500.0:
                        severity = "high" if amt >= (baseline_ref * 4) or amt >= 15000 else "medium"
                        rec = AnomalyRecord(
                            transaction_id=str(row["transaction_id"]),
                            date=str(row["date"]),
                            description=str(row["description"]),
                            amount=round(amt, 2),
                            category=category,
                            baseline_mean=round(baseline_ref, 2),
                            baseline_std=round(std_ref, 2),
                            threshold=round(cat_threshold, 2),
                            severity=severity,
                            reason=f"Recorded amount ₹{amt:,.2f} is significantly higher than {category} normal baseline (₹{baseline_ref:,.2f})",
                            confidence=0.92 if severity == "high" else 0.82
                        )
                        detected[rec.transaction_id] = rec

        # 2. Global Outlier Filter (Catches unclassified big-ticket spikes like Flight, Electronics, etc.)
        all_amounts = df["amount"].astype(float).values
        global_median = float(np.median(all_amounts))
        
        for _, row in df.iterrows():
            amt = float(row["amount"])
            tx_id = str(row["transaction_id"])
            
            # If transaction is > ₹9,000 and at least 5x the global median expense (~₹600-₹1,000)
            if tx_id not in detected and amt >= 9000.0 and amt > (global_median * 5):
                rec = AnomalyRecord(
                    transaction_id=tx_id,
                    date=str(row["date"]),
                    description=str(row["description"]),
                    amount=round(amt, 2),
                    category=str(row["category"]),
                    baseline_mean=round(global_median, 2),
                    baseline_std=round(global_median * 0.5, 2),
                    threshold=9000.0,
                    severity="high" if amt >= 20000 else "medium",
                    reason=f"High-value overall spending spike: ₹{amt:,.2f} is substantially higher than typical purchases (median ₹{global_median:,.2f})",
                    confidence=0.95
                )
                detected[tx_id] = rec

        results = list(detected.values())
        results.sort(key=lambda x: x.amount, reverse=True)
        return results