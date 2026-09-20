import pandas as pd
from typing import List, Dict, Any
from agent.state import Transaction


class FinancialAnalytics:
    """Core deterministic arithmetic engine for aggregating transaction records."""

    @staticmethod
    def get_monthly_summary(transactions: List[Transaction], target_month: str = "") -> Dict[str, Any]:
        if not transactions:
            return {
                "month": target_month or "N/A",
                "income": 0.0,
                "expenses": 0.0,
                "net_cash_flow": 0.0,
                "savings_rate": 0.0,
                "transaction_count": 0,
                "category_breakdown": {},
                "largest_category": {"name": "None", "amount": 0.0, "percentage": 0.0}
            }

        df = pd.DataFrame([t.model_dump() for t in transactions])
        df["month"] = df["date"].str.slice(0, 7)

        if not target_month:
            target_month = df["month"].max()

        m_df = df[df["month"] == target_month]
        if m_df.empty:
            return {
                "month": target_month,
                "income": 0.0,
                "expenses": 0.0,
                "net_cash_flow": 0.0,
                "savings_rate": 0.0,
                "transaction_count": 0,
                "category_breakdown": {},
                "largest_category": {"name": "None", "amount": 0.0, "percentage": 0.0}
            }

        income = float(m_df[m_df["transaction_type"] == "credit"]["amount"].sum())
        expenses_df = m_df[m_df["transaction_type"] == "debit"]
        expenses = float(expenses_df["amount"].sum())
        net_cash_flow = round(income - expenses, 2)
        
        savings_rate = round((net_cash_flow / income) * 100, 2) if income > 0 else 0.0

        # Category Breakdown
        cat_group = expenses_df.groupby("category")["amount"].sum().to_dict()
        cat_breakdown = {k: round(float(v), 2) for k, v in sorted(cat_group.items(), key=lambda i: i[1], reverse=True)}

        largest_cat = {"name": "None", "amount": 0.0, "percentage": 0.0}
        if cat_breakdown and expenses > 0:
            top_name = next(iter(cat_breakdown))
            top_amt = cat_breakdown[top_name]
            largest_cat = {
                "name": top_name,
                "amount": top_amt,
                "percentage": round((top_amt / expenses) * 100, 1)
            }

        return {
            "month": target_month,
            "income": round(income, 2),
            "expenses": round(expenses, 2),
            "net_cash_flow": net_cash_flow,
            "savings_rate": savings_rate,
            "transaction_count": len(m_df),
            "category_breakdown": cat_breakdown,
            "largest_category": largest_cat
        }

    @staticmethod
    def compare_months(transactions: List[Transaction], current_month: str = "", previous_month: str = "") -> Dict[str, Any]:
        df = pd.DataFrame([t.model_dump() for t in transactions])
        df["month"] = df["date"].str.slice(0, 7)
        available_months = sorted(df["month"].unique())

        if len(available_months) < 2 and not (current_month and previous_month):
            return {"error": "Insufficient historical months to perform comparison. At least 2 months are required."}

        if not current_month:
            current_month = available_months[-1]
        if not previous_month:
            curr_idx = available_months.index(current_month) if current_month in available_months else len(available_months) - 1
            previous_month = available_months[curr_idx - 1] if curr_idx > 0 else available_months[0]

        curr_exp = df[(df["month"] == current_month) & (df["transaction_type"] == "debit")]
        prev_exp = df[(df["month"] == previous_month) & (df["transaction_type"] == "debit")]

        curr_tot = round(float(curr_exp["amount"].sum()), 2)
        prev_tot = round(float(prev_exp["amount"].sum()), 2)
        diff_tot = round(curr_tot - prev_tot, 2)
        pct_tot = round((diff_tot / prev_tot) * 100, 2) if prev_tot > 0 else 0.0

        curr_cats = curr_exp.groupby("category")["amount"].sum().to_dict()
        prev_cats = prev_exp.groupby("category")["amount"].sum().to_dict()
        all_cats = set(curr_cats.keys()).union(set(prev_cats.keys()))

        cat_comparisons = []
        for cat in all_cats:
            c_val = round(float(curr_cats.get(cat, 0.0)), 2)
            p_val = round(float(prev_cats.get(cat, 0.0)), 2)
            diff = round(c_val - p_val, 2)
            pct = round((diff / p_val) * 100, 2) if p_val > 0 else (100.0 if c_val > 0 else 0.0)
            cat_comparisons.append({
                "category": cat,
                "current": c_val,
                "previous": p_val,
                "absolute_diff": diff,
                "pct_change": pct,
                "status": "increased" if diff > 0 else ("decreased" if diff < 0 else "unchanged")
            })

        cat_comparisons.sort(key=lambda x: abs(x["absolute_diff"]), reverse=True)

        return {
            "current_month": current_month,
            "previous_month": previous_month,
            "current_expenses": curr_tot,
            "previous_expenses": prev_tot,
            "total_change": diff_tot,
            "total_pct_change": pct_tot,
            "categories": cat_comparisons
        }