import time
from typing import Dict, Any, Callable
from agent.state import AgentState, AuditEntry
from tools.analytics import FinancialAnalytics
from tools.recurring import RecurringEngine
from tools.anomalies import AnomalyDetector
from tools.planning import BudgetAndGoalEngine


class ToolRegistry:
    """Central registry executing atomic domain tasks and recording structured audit traces."""

    def __init__(self):
        self._tools: Dict[str, Callable[[AgentState, Dict[str, Any]], AgentState]] = {
            "calculate_monthly_summary": self._exec_monthly_summary,
            "detect_recurring_patterns": self._exec_recurring,
            "detect_statistical_anomalies": self._exec_anomalies,
            "calculate_budget_status": self._exec_budget,
            "calculate_goal_feasibility": self._exec_goal,
            "calculate_mom_differences": self._exec_mom_comparison,
        }

    def execute(self, tool_name: str, state: AgentState, params: Dict[str, Any] = None) -> AgentState:
        if params is None:
            params = {}

        start_time = time.perf_counter()
        if tool_name not in self._tools:
            # Handle passthrough/retrieval steps
            entry = AuditEntry(
                step=tool_name,
                tool=tool_name,
                input_data=params,
                output_summary=f"Processed step: {tool_name}",
                status="success",
                duration_ms=round((time.perf_counter() - start_time) * 1000, 2)
            )
            state.audit_log.append(entry)
            return state

        try:
            state = self._tools[tool_name](state, params)
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            entry = AuditEntry(
                step=tool_name,
                tool=tool_name,
                input_data=params,
                output_summary="Execution completed successfully",
                status="success",
                duration_ms=duration
            )
            state.audit_log.append(entry)
        except Exception as e:
            duration = round((time.perf_counter() - start_time) * 1000, 2)
            entry = AuditEntry(
                step=tool_name,
                tool=tool_name,
                input_data=params,
                output_summary=f"Tool failure: {str(e)}",
                status="failed",
                duration_ms=duration
            )
            state.audit_log.append(entry)

        return state

    def _exec_monthly_summary(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        month = params.get("month", state.selected_month)
        summary = FinancialAnalytics.get_monthly_summary(state.transactions, month)
        state.monthly_summary = summary
        state.selected_month = summary["month"]
        return state

    def _exec_recurring(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        patterns = RecurringEngine.detect_recurring(state.transactions)
        state.recurring_payments = patterns
        state.subscriptions = [p for p in patterns if p.is_subscription]
        return state

    def _exec_anomalies(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        anomalies = AnomalyDetector.detect_anomalies(state.transactions)
        state.anomalies = anomalies
        return state

    def _exec_budget(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        monthly_budget = params.get("budget", state.budget_status.get("monthly_budget", 0.0))
        expenses = state.monthly_summary.get("expenses", 0.0)
        breakdown = state.monthly_summary.get("category_breakdown", {})
        status = BudgetAndGoalEngine.calculate_budget(expenses, monthly_budget, breakdown)
        state.budget_status = status
        return state

    def _exec_goal(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        name = params.get("goal_name", state.goal_status.get("goal_name", "Savings Goal"))
        target = params.get("target_amount", state.goal_status.get("target_amount", 0.0))
        months = params.get("target_months", state.goal_status.get("target_months", 6))
        surplus = state.monthly_summary.get("net_cash_flow", 0.0)
        goal_res = BudgetAndGoalEngine.evaluate_goal(name, target, months, surplus)
        state.goal_status = goal_res
        return state

    def _exec_mom_comparison(self, state: AgentState, params: Dict[str, Any]) -> AgentState:
        res = FinancialAnalytics.compare_months(state.transactions)
        state.month_comparison = res
        return state