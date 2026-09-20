from typing import Dict, Any


class BudgetAndGoalEngine:
    """Deterministic validation and tracking of user-defined budgets and financial goals."""

    @staticmethod
    def calculate_budget(total_expenses: float, monthly_budget: float, category_breakdown: Dict[str, float] = None, category_budgets: Dict[str, float] = None) -> Dict[str, Any]:
        if monthly_budget <= 0:
            return {
                "configured": False,
                "monthly_budget": 0.0,
                "total_expenses": total_expenses,
                "remaining": 0.0,
                "percentage_used": 0.0,
                "status": "No active monthly budget set",
                "categories": []
            }

        remaining = round(monthly_budget - total_expenses, 2)
        pct_used = round((total_expenses / monthly_budget) * 100, 2)
        
        status = "Within Budget"
        if pct_used >= 100.0:
            status = "Budget Exceeded"
        elif pct_used >= 85.0:
            status = "Budget Critical Pressure"
        elif pct_used >= 70.0:
            status = "Moderate Utilization"

        # Evaluate category-specific budgets if present
        cat_analysis = []
        if category_breakdown and category_budgets:
            for cat, b_limit in category_budgets.items():
                spent = category_breakdown.get(cat, 0.0)
                cat_pct = round((spent / b_limit) * 100, 1) if b_limit > 0 else 0.0
                cat_analysis.append({
                    "category": cat,
                    "budget": b_limit,
                    "spent": spent,
                    "remaining": round(b_limit - spent, 2),
                    "percentage_used": cat_pct,
                    "status": "Exceeded" if spent > b_limit else "Healthy"
                })

        return {
            "configured": True,
            "monthly_budget": round(monthly_budget, 2),
            "total_expenses": round(total_expenses, 2),
            "remaining": remaining,
            "percentage_used": pct_used,
            "status": status,
            "categories": cat_analysis
        }

    @staticmethod
    def evaluate_goal(goal_name: str, target_amount: float, target_months: int, current_monthly_surplus: float) -> Dict[str, Any]:
        if target_amount <= 0 or target_months <= 0:
            return {
                "configured": False,
                "goal_name": goal_name or "Not Specified",
                "message": "Configure a valid positive target amount and target horizon."
            }

        required_monthly = round(target_amount / target_months, 2)
        monthly_gap = round(required_monthly - current_monthly_surplus, 2)
        
        # Determine alignment
        if current_monthly_surplus >= required_monthly:
            status = "On Track"
            timeline_estimate = round(target_amount / current_monthly_surplus, 1) if current_monthly_surplus > 0 else target_months
            feasibility = f"Mathematically feasible. Current monthly surplus covers the ₹{required_monthly:,.2f}/month requirement."
        else:
            status = "Deficit Gap"
            timeline_estimate = round(target_amount / current_monthly_surplus, 1) if current_monthly_surplus > 0 else 999.0
            feasibility = f"Surplus deficit of ₹{abs(monthly_gap):,.2f}/month. At current surplus rate, reaching the goal will take {timeline_estimate:.1f} months."

        return {
            "configured": True,
            "goal_name": goal_name,
            "target_amount": round(target_amount, 2),
            "target_months": target_months,
            "required_monthly_saving": required_monthly,
            "current_monthly_surplus": round(current_monthly_surplus, 2),
            "monthly_gap": monthly_gap,
            "status": status,
            "feasibility_note": feasibility,
            "estimated_months_at_current_rate": timeline_estimate
        }