from typing import Dict, Any, List
from agent.state import AgentState, AuditEntry
from agent.router import QueryRouter
from agent.planner import AgentPlanner
from agent.verifier import DeterministicVerifier
from tools.registry import ToolRegistry


class FinPilotAgent:
    """The central agent orchestrator coordinating observation, planning, execution, and verification."""

    def __init__(self):
        self.tool_registry = ToolRegistry()

    def process_query(self, query: str, state: AgentState) -> AgentState:
        state.user_query = query
        state.user_goal = f"Respond accurately to user query: '{query}'"
        state.replan_count = 0
        state.status = "analyzing"

        # Step 1: Query Intent Routing
        routing = QueryRouter.route(query)
        state.intent = routing["intent"]
        
        state.audit_log.append(AuditEntry(
            step="intent_routing",
            tool="QueryRouter",
            input_data={"query": query},
            output_summary=f"Identified intent: {state.intent} (Target: {routing.get('target')})",
            status="success"
        ))

        # Step 2: Formulate Initial Plan
        state.plan = AgentPlanner.create_plan(state.intent)
        state.audit_log.append(AuditEntry(
            step="planning",
            tool="AgentPlanner",
            input_data={"intent": state.intent},
            output_summary=f"Formulated {len(state.plan)}-step sequence: {' -> '.join(state.plan)}",
            status="success"
        ))

        # Step 3: Execute Agent Loop with Verification and Replanning
        executed_successfully = self._run_execution_loop(state)

        if not executed_successfully:
            state.status = "completed_with_limitations"
            state.answer = (
                "FinPilot encountered analytical data discrepancies that could not be reconciled "
                "after automated replanning attempts. Showing verifiable partial figures only."
            )
            return state

        # Step 4: Final Response Synthesis
        self._synthesize_answer(state)
        state.status = "completed"
        return state

    def _run_execution_loop(self, state: AgentState) -> bool:
        while state.replan_count <= state.max_replans:
            # Execute tools in plan
            for step in state.plan:
                if step == "generate_response":
                    continue
                state = self.tool_registry.execute(step, state)

            # Verification Step
            verification = DeterministicVerifier.verify(state)
            state.verification = verification

            if verification.passed:
                state.audit_log.append(AuditEntry(
                    step="verification",
                    tool="DeterministicVerifier",
                    input_data={"checks": verification.checks_performed},
                    output_summary=f"All {len(verification.checks_performed)} verification checks passed.",
                    status="success"
                ))
                return True
            else:
                state.replan_count += 1
                failed_str = ", ".join(verification.discrepancies)
                state.audit_log.append(AuditEntry(
                    step="verification_failure",
                    tool="DeterministicVerifier",
                    input_data={"discrepancies": verification.discrepancies},
                    output_summary=f"Verification failed on attempt {state.replan_count}. Initiating replanning.",
                    status="warning"
                ))

                if state.replan_count > state.max_replans:
                    break

                # Replan
                state.plan = AgentPlanner.create_replan(failed_str, state.plan, state.replan_count)
                state.audit_log.append(AuditEntry(
                    step="replanning",
                    tool="AgentPlanner",
                    input_data={"attempt": state.replan_count},
                    output_summary=f"New plan created: {' -> '.join(state.plan)}",
                    status="success"
                ))

        return False

    def _synthesize_answer(self, state: AgentState):
        """Constructs an evidence-grounded response backed strictly by verified facts."""
        intent = state.intent
        summary = state.monthly_summary
        evidence: List[str] = []

        if intent in ["CATEGORY_HIGHEST", "CATEGORY_SPECIFIC"]:
            top = summary.get("largest_category", {})
            total_exp = summary.get("expenses", 0.0)
            state.answer = (
                f"Your largest recorded expense category for {summary.get('month', 'this period')} was "
                f"**{top.get('name')}**, totaling **₹{top.get('amount', 0):,.2f}** "
                f"({top.get('percentage', 0)}% of total monthly spending)."
            )
            evidence.append(f"{summary.get('transaction_count', 0)} transactions analyzed.")
            evidence.append(f"Total recorded expenses: ₹{total_exp:,.2f}.")
            for cat, amt in list(summary.get("category_breakdown", {}).items())[:4]:
                evidence.append(f"• {cat}: ₹{amt:,.2f}")

        elif intent == "SUBSCRIPTION":
            subs = state.subscriptions
            total_sub_cost = sum(s.average_amount for s in subs)
            if subs:
                sub_list = ", ".join([f"{s.description} (₹{s.average_amount:,.2f}/{s.frequency.lower()})" for s in subs])
                state.answer = (
                    f"FinPilot identified **{len(subs)} likely recurring subscriptions** totaling "
                    f"approximately **₹{total_sub_cost:,.2f}** in periodic commitments: {sub_list}."
                )
                for s in subs:
                    evidence.append(
                        f"• {s.description}: {s.occurrences} occurrences, ~{s.average_interval} days apart, "
                        f"variation {s.amount_variation}%, confidence: {int(s.confidence * 100)}%"
                    )
            else:
                state.answer = "No active recurring subscriptions detected based on historical transaction intervals."
                evidence.append("Analyzed recurring merchant intervals; found 0 periodic subscriptions.")

        elif intent == "BUDGET":
            b = state.budget_status
            if b.get("configured"):
                state.answer = (
                    f"You have committed **₹{b['total_expenses']:,.2f}** of your configured **₹{b['monthly_budget']:,.2f}** "
                    f"monthly budget (**{b['percentage_used']}% used**). "
                    f"Remaining allocation: **₹{b['remaining']:,.2f}** (Status: {b['status']})."
                )
                evidence.append(f"Configured budget limit: ₹{b['monthly_budget']:,.2f}")
                evidence.append(f"Total debit expenses verified: ₹{b['total_expenses']:,.2f}")
                evidence.append(f"Verification arithmetic check: Passed")
            else:
                state.answer = (
                    f"Total expenses for the period stand at **₹{summary.get('expenses', 0):,.2f}**. "
                    f"Set a target budget in the sidebar to view utilization metrics."
                )

        elif intent == "MONTHLY_COMPARISON":
            comp = state.month_comparison
            if "error" in comp:
                state.answer = comp["error"]
                evidence.append("Single-month dataset detected.")
            else:
                diff = comp["total_change"]
                dir_str = "an increase" if diff > 0 else "a decrease"
                state.answer = (
                    f"Total spending changed from **₹{comp['previous_expenses']:,.2f}** ({comp['previous_month']}) "
                    f"to **₹{comp['current_expenses']:,.2f}** ({comp['current_month']}), representing "
                    f"{dir_str} of **₹{abs(diff):,.2f}** ({comp['total_pct_change']}%)."
                )
                evidence.append(f"Base Month: {comp['previous_month']} | Target Month: {comp['current_month']}")
                for c in comp.get("categories", [])[:3]:
                    evidence.append(f"• {c['category']}: ₹{c['previous']} → ₹{c['current']} ({c['pct_change']}%)")

        elif intent == "ANOMALY":
            anoms = state.anomalies
            if anoms:
                state.answer = (
                    f"FinPilot detected **{len(anoms)} unusual transaction(s)** exceeding "
                    f"category statistical baselines (mean + 2σ)."
                )
                for a in anoms:
                    evidence.append(f"• {a.date}: {a.description} - ₹{a.amount:,.2f} ({a.reason})")
            else:
                state.answer = "No anomalous or statistical outlier spending detected in the analyzed dataset."
                evidence.append("All transactions fall within standard category variations.")

        elif intent == "GOAL":
            g = state.goal_status
            if g.get("configured"):
                state.answer = (
                    f"For your goal '**{g['goal_name']}**' (Target: ₹{g['target_amount']:,.2f} over {g['target_months']} months), "
                    f"a monthly saving of **₹{g['required_monthly_saving']:,.2f}** is required. "
                    f"Current net monthly surplus is **₹{g['current_monthly_surplus']:,.2f}**. Status: **{g['status']}**."
                )
                evidence.append(g["feasibility_note"])
            else:
                state.answer = "Configure your savings goal in the sidebar to run mathematical feasibility analysis."

        else:
            state.answer = (
                f"Financial Summary for {summary.get('month', 'current month')}: Total Income of "
                f"**₹{summary.get('income', 0):,.2f}**, Total Expenses of **₹{summary.get('expenses', 0):,.2f}**, "
                f"resulting in a Net Cash Flow of **₹{summary.get('net_cash_flow', 0):,.2f}** "
                f"(Savings Rate: {summary.get('savings_rate', 0)}%)."
            )
            evidence.append(f"Analyzed {summary.get('transaction_count', 0)} records.")
            evidence.append(f"Largest category: {summary.get('largest_category', {}).get('name', 'N/A')}")

        state.evidence = evidence