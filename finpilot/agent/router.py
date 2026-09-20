import re
from typing import Dict, Any


class QueryRouter:
    """Classifies user queries into discrete operational intents without an LLM."""

    PATTERNS = {
        "SUBSCRIPTION": [
            r"subscription", r"recurring", r"memberships?", r"autopay", r"stream(ing)?"
        ],
        "ANOMALY": [
            r"unusual", r"anomaly", r"anomalies", r"spike", r"strange", r"unexpected", r"outlier"
        ],
        "BUDGET": [
            r"budget", r"committed", r"remaining", r"allowance", r"spending limit"
        ],
        "GOAL": [
            r"goal", r"target", r"save up", r"savings target", r"support my goal"
        ],
        "MONTHLY_COMPARISON": [
            r"compared? (to|with)? last month", r"month[- ]over[- ]month", r"mom",
            r"increase", r"decrease", r"changes? from last"
        ],
        "CATEGORY": [
            r"where did i spend", r"most (on|this)", r"highest (category|expense)",
            r"spending on (\w+)", r"food", r"housing", r"travel", r"groceries"
        ],
        "INCOME": [
            r"income", r"salary", r"earnings?", r"how much did i make", r"credits?"
        ],
        "GENERAL_SUMMARY": [
            r"summary", r"overview", r"how am i doing", r"report", r"cash flow", r"net"
        ]
    }

    @classmethod
    def route(cls, query: str) -> Dict[str, Any]:
        normalized = query.lower().strip()
        matched_intents = []

        for intent, patterns in cls.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, normalized):
                    matched_intents.append(intent)
                    break

        if "SUBSCRIPTION" in matched_intents:
            return {"intent": "SUBSCRIPTION", "target": "subscriptions"}
        if "ANOMALY" in matched_intents:
            return {"intent": "ANOMALY", "target": "unusual_spending"}
        if "MONTHLY_COMPARISON" in matched_intents:
            return {"intent": "MONTHLY_COMPARISON", "target": "mom_comparison"}
        if "BUDGET" in matched_intents:
            return {"intent": "BUDGET", "target": "budget_utilization"}
        if "GOAL" in matched_intents:
            return {"intent": "GOAL", "target": "goal_alignment"}
        if "CATEGORY" in matched_intents:
            # Check for specific category extraction
            for cat in ["food", "housing", "transport", "shopping", "utilities", "healthcare", "entertainment"]:
                if cat in normalized:
                    return {"intent": "CATEGORY_SPECIFIC", "target": cat.capitalize()}
            return {"intent": "CATEGORY_HIGHEST", "target": "highest_category"}
        if "INCOME" in matched_intents:
            return {"intent": "INCOME", "target": "income_summary"}
        if "GENERAL_SUMMARY" in matched_intents or not matched_intents:
            return {"intent": "GENERAL_SUMMARY", "target": "executive_summary"}

        return {"intent": "GENERAL_SUMMARY", "target": "general"}