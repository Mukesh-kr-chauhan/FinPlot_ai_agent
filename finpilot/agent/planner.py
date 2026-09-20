from typing import List, Dict


class AgentPlanner:
    """Formulates a discrete, verifiable sequence of tool executions based on classified intent."""

    PLAN_TEMPLATES: Dict[str, List[str]] = {
        "CATEGORY_HIGHEST": [
            "retrieve_transactions",
            "filter_expenses",
            "calculate_category_totals",
            "identify_highest_category",
            "verify_category_math",
            "generate_response"
        ],
        "CATEGORY_SPECIFIC": [
            "retrieve_transactions",
            "filter_category_expenses",
            "calculate_category_metrics",
            "verify_category_math",
            "generate_response"
        ],
        "SUBSCRIPTION": [
            "retrieve_transactions",
            "detect_recurring_patterns",
            "filter_subscriptions",
            "verify_recurring_intervals",
            "generate_response"
        ],
        "BUDGET": [
            "retrieve_transactions",
            "calculate_monthly_expenses",
            "calculate_budget_status",
            "verify_budget_arithmetic",
            "generate_response"
        ],
        "GOAL": [
            "retrieve_transactions",
            "calculate_monthly_cash_flow",
            "calculate_goal_feasibility",
            "verify_goal_math",
            "generate_response"
        ],
        "MONTHLY_COMPARISON": [
            "retrieve_multi_month_records",
            "aggregate_monthly_categories",
            "calculate_mom_differences",
            "verify_comparison_math",
            "generate_response"
        ],
        "ANOMALY": [
            "retrieve_transactions",
            "calculate_category_baselines",
            "detect_statistical_anomalies",
            "verify_anomaly_thresholds",
            "generate_response"
        ],
        "INCOME": [
            "retrieve_transactions",
            "filter_income_records",
            "calculate_income_totals",
            "verify_income_math",
            "generate_response"
        ],
        "GENERAL_SUMMARY": [
            "retrieve_transactions",
            "calculate_monthly_summary",
            "detect_recurring_patterns",
            "detect_statistical_anomalies",
            "verify_cash_flow_integrity",
            "generate_response"
        ]
    }

    @classmethod
    def create_plan(cls, intent: str) -> List[str]:
        return cls.PLAN_TEMPLATES.get(intent, cls.PLAN_TEMPLATES["GENERAL_SUMMARY"]).copy()

    @classmethod
    def create_replan(cls, failed_check: str, current_plan: List[str], replan_count: int) -> List[str]:
        """Provides an alternate plan to reconcile discrepancies or degrade safely."""
        if replan_count >= 3:
            return ["fallback_safe_explanation"]
            
        if "category_reconciliation" in failed_check:
            return [
                "normalize_transactions_strict",
                "calculate_category_totals",
                "verify_category_math",
                "generate_response"
            ]
        elif "insufficient_data" in failed_check:
            return [
                "relax_statistical_thresholds",
                "detect_recurring_patterns",
                "generate_response"
            ]
        elif "budget_arithmetic" in failed_check:
            return [
                "recalculate_monthly_expenses",
                "calculate_budget_status",
                "verify_budget_arithmetic",
                "generate_response"
            ]
        
        # Default replan attempt
        return ["retrieve_transactions", "calculate_monthly_summary", "generate_response"]