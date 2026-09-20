from agent.state import AgentState, VerificationResult


class DeterministicVerifier:
    """Ensures analytical, arithmetic, and categorical integrity before synthesizing responses."""

    @classmethod
    def verify(cls, state: AgentState) -> VerificationResult:
        checks: list[str] = []
        discrepancies: list[str] = []
        details: dict = {}

        # Check 1: Cash flow balance
        if state.monthly_summary:
            inc = state.monthly_summary.get("income", 0.0)
            exp = state.monthly_summary.get("expenses", 0.0)
            net = state.monthly_summary.get("net_cash_flow", 0.0)
            expected_net = round(inc - exp, 2)
            checks.append("net_cash_flow_reconciliation")
            if abs(net - expected_net) > 0.01:
                discrepancies.append(
                    f"Net cash flow mismatch: reported ₹{net}, calculated ₹{expected_net} (Income: ₹{inc} - Expenses: ₹{exp})"
                )
            details["cash_flow_check"] = {"reported": net, "expected": expected_net, "delta": abs(net - expected_net)}

        # Check 2: Category Summation Reconciles to Total Expenses
        if state.monthly_summary and state.monthly_summary.get("category_breakdown"):
            exp = state.monthly_summary.get("expenses", 0.0)
            cats = state.monthly_summary.get("category_breakdown", {})
            summed_cats = round(sum(cats.values()), 2)
            checks.append("category_reconciliation")
            if abs(exp - summed_cats) > 0.05:
                discrepancies.append(
                    f"Category breakdown sum (₹{summed_cats}) does not match recorded total expenses (₹{exp})"
                )
            details["category_sum_check"] = {"total_expenses": exp, "summed_categories": summed_cats}

        # Check 3: Budget Arithmetic Verification
        if state.budget_status and state.budget_status.get("configured"):
            b_total = state.budget_status.get("monthly_budget", 0.0)
            b_spent = state.budget_status.get("total_expenses", 0.0)
            b_rem = state.budget_status.get("remaining", 0.0)
            expected_rem = round(b_total - b_spent, 2)
            checks.append("budget_arithmetic")
            if abs(b_rem - expected_rem) > 0.01:
                discrepancies.append(
                    f"Budget remaining calculation error: reported ₹{b_rem}, expected ₹{expected_rem}"
                )
            details["budget_check"] = {"remaining_reported": b_rem, "remaining_expected": expected_rem}

        # Check 4: Goal Required Surplus Verification
        if state.goal_status and state.goal_status.get("configured"):
            tgt = state.goal_status.get("target_amount", 0.0)
            mths = state.goal_status.get("target_months", 1)
            req = state.goal_status.get("required_monthly_saving", 0.0)
            expected_req = round(tgt / mths, 2)
            checks.append("goal_arithmetic")
            if abs(req - expected_req) > 0.02:
                discrepancies.append(
                    f"Goal monthly savings rate error: reported ₹{req}, expected ₹{expected_req}"
                )
            details["goal_check"] = {"required_reported": req, "required_expected": expected_req}

        # Check 5: Recurring Frequency Validation
        if state.recurring_payments:
            checks.append("recurring_interval_integrity")
            for r in state.recurring_payments:
                if r.occurrences < 2:
                    discrepancies.append(f"Recurring entity {r.description} reported with fewer than 2 occurrences.")

        passed = len(discrepancies) == 0
        return VerificationResult(
            passed=passed,
            checks_performed=checks,
            discrepancies=discrepancies,
            reconciliation_details=details
        )