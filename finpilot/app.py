import os
import pandas as pd
import plotly.express as px
import streamlit as st

from agent.core import FinPilotAgent
from agent.state import AgentState
from tools.normalization import DataNormalizer
from tools.anomalies import AnomalyDetector
from tools.planning import BudgetAndGoalEngine

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="FinPilot | Personal Finance & Expense Intelligence",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- MODERN EXPENSE TRACKER DESIGN SYSTEM -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    }

    /* Virtual Glassmorphic Card */
    .virtual-card {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%) !important;
        border-radius: 20px;
        padding: 26px;
        color: #FFFFFF !important;
        box-shadow: 0 15px 35px -5px rgba(15, 23, 42, 0.4);
        position: relative;
        overflow: hidden;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .virtual-card * {
        color: #FFFFFF !important;
    }
    .card-chip {
        width: 44px;
        height: 32px;
        background: linear-gradient(135deg, #F59E0B, #D97706);
        border-radius: 6px;
        margin-bottom: 20px;
    }
    .card-number {
        font-size: 19px;
        letter-spacing: 3px;
        font-weight: 500;
        margin-bottom: 18px;
        color: rgba(255, 255, 255, 0.9) !important;
    }
    .card-footer {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
    }

    /* Modern Metric Cards */
    .metric-card {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }
    .metric-icon {
        width: 42px;
        height: 42px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        margin-bottom: 12px;
    }

    /* Universal Content Box with Enforced Dark Text */
    .content-box {
        background: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .content-box h4 {
        color: #0F172A !important;
        font-weight: 700 !important;
        margin: 0 0 16px 0 !important;
    }

    /* Feed Rows for Transactions with High Contrast */
    .tx-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        border-radius: 12px;
        background: #FFFFFF !important;
        margin-bottom: 8px;
        border: 1px solid #E2E8F0 !important;
        transition: transform 0.1s ease;
    }
    .tx-row:hover {
        transform: translateX(4px);
        background: #F1F5F9 !important;
    }
    .tx-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .tx-icon-box {
        width: 40px;
        height: 40px;
        border-radius: 10px;
        background: #F1F5F9 !important;
        border: 1px solid #E2E8F0 !important;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 18px;
    }
    .tx-desc {
        font-weight: 700 !important;
        color: #0F172A !important;
        font-size: 14px;
    }
    .tx-meta {
        font-size: 12px;
        color: #475569 !important;
        font-weight: 500;
    }
    .tx-amount-debit {
        font-weight: 800 !important;
        color: #DC2626 !important;
        font-size: 14px;
    }
    .tx-amount-credit {
        font-weight: 800 !important;
        color: #16A34A !important;
        font-size: 14px;
    }

    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
</style>
""", unsafe_allow_html=True)
# ----------------- TOP HEADER / HERO BANNER -----------------
st.markdown("""
<div style="
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #2563EB 100%);
    border-radius: 18px;
    padding: 28px 32px;
    margin-bottom: 24px;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25);
    display: flex;
    justify-content: space-between;
    align-items: center;
">
    <div>
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-size: 32px;">🧭</span>
            <span style="
                font-size: 34px;
                font-weight: 800;
                letter-spacing: -0.5px;
                color: #FFFFFF;
            ">FinPilot Agent</span>
            <span style="
                background: rgba(37, 99, 235, 0.35);
                border: 1px solid rgba(147, 197, 253, 0.4);
                color: #93C5FD;
                padding: 4px 12px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.5px;
            ">v2.4 ACTIVE</span>
        </div>
        <p style="
            font-size: 15px;
            color: #CBD5E1;
            margin: 0;
            max-width: 680px;
            line-height: 1.5;
        ">
            Autonomous Personal Finance Decision-Support Engine. Converts raw bank statements into verified spending analytics, subscription monitors, and goal projections.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ----------------- SESSION STATE -----------------
def init_session():
    if "agent_state" not in st.session_state:
        st.session_state.agent_state = AgentState()
    if "agent" not in st.session_state:
        st.session_state.agent = FinPilotAgent()
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "last_uploaded_filename" not in st.session_state:
        st.session_state.last_uploaded_filename = None

init_session()

# Category icon mapping helper
CATEGORY_ICONS = {
    "Food": "🍔",
    "Housing": "🏠",
    "Transport": "🚗",
    "Shopping": "🛍️",
    "Subscription": "📺",
    "Utilities": "⚡",
    "Healthcare": "💊",
    "Entertainment": "🍿",
    "Income": "💰",
    "Other": "💳"
}

# ----------------- SIDEBAR -----------------
with st.sidebar:
    st.markdown("## 💳 FinPilot Agent")
    st.caption("AI-Powered Expense & Decision Support Engine")
    st.divider()

    st.markdown("### 1. Ingest Statements")
    if st.button("⚡ Load Demo Financial Records", use_container_width=True, type="primary"):
        demo_path = os.path.join(os.path.dirname(__file__), "data", "sample_transactions.csv")
        if os.path.exists(demo_path):
            with open(demo_path, "r", encoding="utf-8") as f:
                content = f.read()
            txs, errors = DataNormalizer.parse_csv(content)
            if not errors and len(txs) > 0:
                st.session_state.agent_state.transactions = txs
                st.session_state.agent_state.raw_records_count = len(txs)
                st.session_state.data_loaded = True
                
                # Baseline tool execution
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_monthly_summary", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("detect_recurring_patterns", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("detect_statistical_anomalies", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_mom_differences", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_budget_status", st.session_state.agent_state, {"budget": 40000.0})
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_goal_feasibility", st.session_state.agent_state, {
                    "goal_name": "Emergency Buffer",
                    "target_amount": 60000.0,
                    "target_months": 6
                })
                st.session_state.last_uploaded_filename = "demo"
                st.success(f"Loaded {len(txs)} verified records!")
                st.rerun()

    uploaded_file = st.file_uploader("Upload CSV Statement", type=["csv"])
    if uploaded_file is not None:
        file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.last_uploaded_filename != file_signature:
            content = uploaded_file.getvalue().decode("utf-8", errors="replace")
            txs, errors = DataNormalizer.parse_csv(content)
            if not errors and len(txs) > 0:
                st.session_state.agent_state.transactions = txs
                st.session_state.agent_state.raw_records_count = len(txs)
                st.session_state.data_loaded = True
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_monthly_summary", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("detect_recurring_patterns", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("detect_statistical_anomalies", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_mom_differences", st.session_state.agent_state)
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_budget_status", st.session_state.agent_state, {"budget": 40000.0})
                st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_goal_feasibility", st.session_state.agent_state, {
                    "goal_name": "Emergency Buffer",
                    "target_amount": 60000.0,
                    "target_months": 6
                })
                st.session_state.last_uploaded_filename = file_signature
                st.success("Uploaded and verified!")
                st.rerun()

    st.divider()
    st.markdown("### 2. Expense & Goal Config")
    budget_val = st.number_input("Monthly Budget (₹)", value=40000.0, step=2500.0)
    goal_name_val = st.text_input("Goal Name", value="Emergency Buffer")
    goal_tgt_val = st.number_input("Target Amount (₹)", value=60000.0, step=5000.0)
    goal_m_val = st.number_input("Months Horizon", value=6, step=1)

    if st.button("Update Parameters", use_container_width=True):
        if st.session_state.data_loaded:
            st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_budget_status", st.session_state.agent_state, {"budget": budget_val})
            st.session_state.agent_state = st.session_state.agent.tool_registry.execute("calculate_goal_feasibility", st.session_state.agent_state, {
                "goal_name": goal_name_val,
                "target_amount": goal_tgt_val,
                "target_months": goal_m_val
            })
            st.success("Updated!")
            st.rerun()

    st.divider()
    if st.button("Reset All", use_container_width=True):
        st.session_state.agent_state = AgentState()
        st.session_state.data_loaded = False
        st.session_state.chat_history = []
        st.session_state.last_uploaded_filename = None
        st.rerun()

# ----------------- MAIN TABS -----------------
nav = st.tabs([
    "💳 Wallet & Tracker",
    "🤖 Ask FinPilot Agent",
    "🔁 Subscriptions & Bills",
    "⚠️ Outlier Audit",
    "🎯 Budget & Goals",
    "📜 Agent Trace",
    "📑 Monthly Report",
    "📋 Raw Records"
])

state = st.session_state.agent_state

# ----------------- TAB 1: WALLET & EXPENSE TRACKER -----------------
with nav[0]:
    if not st.session_state.data_loaded:
        st.info("👈 Please load the demo data or upload a transaction CSV from the sidebar to activate the wallet view.")
    else:
        summary = state.monthly_summary
        inc = summary.get("income", 0.0)
        exp = summary.get("expenses", 0.0)
        net = summary.get("net_cash_flow", 0.0)
        
        # Upper Layout: Virtual Card on Left, KPI Cards on Right
        col_card, col_kpi = st.columns([1.1, 1.9])
        
        with col_card:
            st.markdown(f"""
            <div class="virtual-card">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 700; font-size: 16px; letter-spacing: 1px;">FINPILOT BLACK</span>
                    <span style="font-size: 13px; opacity: 0.8;">HDFC Platinum</span>
                </div>
                <div class="card-chip"></div>
                <div style="font-size: 12px; opacity: 0.7; text-transform: uppercase;">Net Monthly Surplus</div>
                <div style="font-size: 26px; font-weight: 800; margin-bottom: 12px;">₹{net:,.2f}</div>
                <div class="card-number">•••• •••• •••• 4092</div>
                <div class="card-footer">
                    <div>
                        <div style="font-size: 10px; opacity: 0.7; text-transform: uppercase;">Cardholder</div>
                        <div style="font-weight: 600; font-size: 13px;">CHAUHAN M.</div>
                    </div>
                    <div>
                        <div style="font-size: 10px; opacity: 0.7; text-transform: uppercase;">Expires</div>
                        <div style="font-weight: 600; font-size: 13px;">09/28</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kpi:
            k1, k2 = st.columns(2)
            with k1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: #ECFDF5; color: #059669;">💰</div>
                    <div style="color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;">Monthly Income</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0F172A; margin: 4px 0;">₹{inc:,.2f}</div>
                    <div style="font-size: 12px; color: #059669; font-weight: 600;">Active Period: {summary.get('month', '2026-09')}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Active recurring commitments count
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: #EEF2FF; color: #4F46E5;">🔁</div>
                    <div style="color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;">Active Subscriptions</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0F172A; margin: 4px 0;">{len(state.subscriptions)} Services</div>
                    <div style="font-size: 12px; color: #4F46E5; font-weight: 600;">Autopay Monitored</div>
                </div>
                """, unsafe_allow_html=True)

            with k2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: #FEF2F2; color: #DC2626;">📉</div>
                    <div style="color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;">Total Expenses</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0F172A; margin: 4px 0;">₹{exp:,.2f}</div>
                    <div style="font-size: 12px; color: #DC2626; font-weight: 600;">Savings Rate: {summary.get('savings_rate', 0)}%</div>
                </div>
                """, unsafe_allow_html=True)

                # Flagged anomalies count
                anom_count = len(state.anomalies)
                anom_bg = "#FEF2F2" if anom_count > 0 else "#ECFDF5"
                anom_color = "#DC2626" if anom_count > 0 else "#059669"
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon" style="background: {anom_bg}; color: {anom_color};">⚠️</div>
                    <div style="color: #64748B; font-size: 12px; font-weight: 600; text-transform: uppercase;">Spending Outliers</div>
                    <div style="font-size: 24px; font-weight: 800; color: #0F172A; margin: 4px 0;">{anom_count} Detected</div>
                    <div style="font-size: 12px; color: {anom_color}; font-weight: 600;">Exceeds Normal Baselines</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        # Middle Layout: Interactive Chart on Left, Recent Activity Feed on Right
        col_chart, col_feed = st.columns([1.3, 1.2])

        with col_chart:
            st.markdown('<div class="content-box"><h4>Expenditure by Category</h4>', unsafe_allow_html=True)
            cats = summary.get("category_breakdown", {})
            if cats:
                df_cat = pd.DataFrame(list(cats.items()), columns=["Category", "Amount"])
                fig = px.pie(
                    df_cat,
                    values="Amount",
                    names="Category",
                    hole=0.6,
                    color_discrete_sequence=["#2563EB", "#0891B2", "#D97706", "#059669", "#DB2777", "#7C3AED"]
                )
                fig.update_layout(
                    margin=dict(t=10, b=10, l=10, r=10),
                    height=320,
                    showlegend=True,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    legend=dict(font=dict(color="#0F172A", size=11))
                )
                st.plotly_chart(fig, width="stretch")
            else:
                st.markdown("<p style='color:#475569;'>No expense records for this period.</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_feed:
            st.markdown('<div class="content-box"><h4>Recent Transactions Feed</h4>', unsafe_allow_html=True)
            recent_txs = list(reversed(state.transactions))[:6]
            if recent_txs:
                for tx in recent_txs:
                    icon = CATEGORY_ICONS.get(tx.category, "💳")
                    is_credit = tx.transaction_type == "credit"
                    amt_class = "tx-amount-credit" if is_credit else "tx-amount-debit"
                    prefix = "+" if is_credit else "-"
                    
                    st.markdown(f"""
                    <div class="tx-row">
                        <div class="tx-left">
                            <div class="tx-icon-box">{icon}</div>
                            <div>
                                <div class="tx-desc">{tx.description}</div>
                                <div class="tx-meta">{tx.date} • {tx.category}</div>
                            </div>
                        </div>
                        <div class="{amt_class}">{prefix}₹{tx.amount:,.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<p style='color:#475569;'>No transactions available.</p>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_feed:
            st.markdown('<div class="content-box"><h4 style="margin: 0 0 16px 0;">Recent Transactions Feed</h4>', unsafe_allow_html=True)
            recent_txs = list(reversed(state.transactions))[:6]
            for tx in recent_txs:
                icon = CATEGORY_ICONS.get(tx.category, "💳")
                is_credit = tx.transaction_type == "credit"
                amt_class = "tx-amount-credit" if is_credit else "tx-amount-debit"
                prefix = "+" if is_credit else "-"
                
                st.markdown(f"""
                <div class="tx-row">
                    <div class="tx-left">
                        <div class="tx-icon-box">{icon}</div>
                        <div>
                            <div class="tx-desc">{tx.description}</div>
                            <div class="tx-meta">{tx.date} • {tx.category}</div>
                        </div>
                    </div>
                    <div class="{amt_class}">{prefix}₹{tx.amount:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 2: ASK FINPILOT AGENT -----------------
with nav[1]:
    st.subheader("💬 Ask FinPilot: Real-time Decision Agent")
    st.caption("Answers are verified using deterministic tools (sum checks, interval standard deviations, and budget reconciliations).")

    st.markdown("**Quick Prompts:**")
    q1, q2, q3 = st.columns(3)
    b1 = q1.button("Where did I spend the most this month?", use_container_width=True)
    b2 = q2.button("Which subscriptions am I paying for?", use_container_width=True)
    b3 = q3.button("How much of my budget is already committed?", use_container_width=True)

    q4, q5, q6 = st.columns(3)
    b4 = q4.button("What expenses increased compared with last month?", use_container_width=True)
    b5 = q5.button("Did I have any unusual spending?", use_container_width=True)
    b6 = q6.button("Can my current spending support my savings goal?", use_container_width=True)

    chosen = None
    for b, query_text in [(b1, "Where did I spend the most this month?"),
                          (b2, "Which subscriptions am I paying for?"),
                          (b3, "How much of my budget is already committed?"),
                          (b4, "What expenses increased compared with last month?"),
                          (b5, "Did I have any unusual spending?"),
                          (b6, "Can my current spending support my savings goal?")]:
        if b:
            chosen = query_text

    user_input = st.chat_input("Ask a question about your financial records...")
    query_to_run = chosen if chosen else user_input

    if query_to_run:
        if not st.session_state.data_loaded:
            st.warning("Please load or upload transactions first.")
        else:
            with st.spinner("FinPilot Agent running: Plan → Tool Execution → Verification..."):
                res_state = st.session_state.agent.process_query(query_to_run, st.session_state.agent_state)
                st.session_state.agent_state = res_state
                st.session_state.chat_history.append({
                    "query": query_to_run,
                    "answer": res_state.answer,
                    "evidence": res_state.evidence,
                    "plan": res_state.plan,
                    "intent": res_state.intent,
                    "verification": res_state.verification
                })

    for chat in reversed(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(chat["query"])
        with st.chat_message("assistant"):
            st.markdown(chat["answer"])
            with st.expander("🔍 View Verifiable Agent Evidence & Decision Trace"):
                st.markdown(f"**Identified Intent:** `{chat['intent']}`")
                st.markdown(f"**Execution Sequence:** {' ➔ '.join(chat['plan'])}")
                st.markdown("**Empirical Evidence:**")
                for e in chat["evidence"]:
                    st.write(f"- {e}")
                if chat["verification"].passed:
                    st.success("✅ Deterministic Verification Passed")
                else:
                    st.warning("⚠️ Discrepancy reconciled via replanner")

# ----------------- TAB 3: RECURRING & SUBSCRIPTIONS -----------------
with nav[2]:
    st.subheader("Recurring Obligations & Periodic Outflows")
    if not st.session_state.data_loaded:
        st.info("👈 Load data to audit periodic obligations.")
    else:
        subs = state.subscriptions
        st.markdown(f"#### Identified Active Subscriptions ({len(subs)})")
        if subs:
            sub_cards = []
            for s in subs:
                sub_cards.append({
                    "Platform": s.description,
                    "Category": s.category,
                    "Cadence": s.frequency,
                    "Mean Cost": f"₹{s.average_amount:,.2f}",
                    "Variance": f"{s.amount_variation}%",
                    "Occurrences": s.occurrences,
                    "Next Estimated Bill": s.next_estimated_date,
                    "Confidence": f"{int(s.confidence * 100)}%"
                })
            st.dataframe(pd.DataFrame(sub_cards), use_container_width=True, hide_index=True)
        else:
            st.write("No active subscriptions detected.")

        st.markdown("#### Projected Recurring Obligations")
        st.caption("Estimated from periodic cadence intervals; not an invoice guarantee.")
        recs = state.recurring_payments
        if recs:
            rec_data = []
            for r in recs:
                rec_data.append({
                    "Payee": r.description,
                    "Category": r.category,
                    "Frequency": r.frequency,
                    "Amount": f"₹{r.average_amount:,.2f}",
                    "Interval (Days)": r.average_interval,
                    "Last Recorded": r.last_payment,
                    "Next Projected": r.next_estimated_date,
                    "Classification": "Subscription" if r.is_subscription else "Fixed Bill"
                })
            st.dataframe(pd.DataFrame(rec_data), use_container_width=True, hide_index=True)

# ----------------- TAB 4: OUTLIER AUDITS -----------------
with nav[3]:
    st.subheader("Statistical Outlier & Spending Anomaly Audits")
    if not st.session_state.data_loaded:
        st.info("👈 Ingest data to run anomaly audits.")
    else:
        anoms = AnomalyDetector.detect_anomalies(state.transactions)
        state.anomalies = anoms
        if anoms:
            st.warning(f"⚠️ Flagged **{len(anoms)} unusual transaction(s)** exceeding normal baselines.")
            a_data = []
            for a in anoms:
                a_data.append({
                    "Date": a.date,
                    "Merchant": a.description,
                    "Amount": f"₹{a.amount:,.2f}",
                    "Category": a.category,
                    "Baseline Normal": f"₹{a.baseline_mean:,.2f}",
                    "Threshold": f"₹{a.threshold:,.2f}",
                    "Severity": a.severity.upper(),
                    "Reason": a.reason,
                    "Confidence": f"{int(a.confidence * 100)}%"
                })
            st.dataframe(pd.DataFrame(a_data), use_container_width=True, hide_index=True)
        else:
            st.success("✅ All transactions fall within normal baseline limits.")

# ----------------- TAB 5: BUDGETS & GOALS -----------------
with nav[4]:
    st.subheader("Budget Allocation & Savings Goal Tracking")
    if not st.session_state.data_loaded:
        st.info("👈 Load statements to assess budget and goal alignments.")
    else:
        b = state.budget_status
        g = state.goal_status
        summary = state.monthly_summary

        if not b or not b.get("configured"):
            b = BudgetAndGoalEngine.calculate_budget(summary.get("expenses", 0.0), 40000.0, summary.get("category_breakdown", {}))
            state.budget_status = b

        if not g or not g.get("configured"):
            g = BudgetAndGoalEngine.evaluate_goal("Emergency Buffer", 60000.0, 6, summary.get("net_cash_flow", 0.0))
            state.goal_status = g

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown('<h4>Monthly Spending Budget</h4>', unsafe_allow_html=True)
            st.metric("Total Budget", f"₹{b['monthly_budget']:,.2f}")
            st.metric("Expenses Incurred", f"₹{b['total_expenses']:,.2f}", delta=f"{b['percentage_used']}% Utilized", delta_color="inverse")
            st.metric("Remaining Balance", f"₹{b['remaining']:,.2f}")
            
            pct = min(1.0, max(0.0, b["percentage_used"] / 100.0))
            st.progress(pct)
            if b["percentage_used"] > 100:
                st.error("⚠️ Budget exceeded for the period!")
            elif b["percentage_used"] >= 85:
                st.warning("⚠️ Critical spending pressure (>85% limit).")
            else:
                st.success("✅ Spending is within configured limits.")
            st.markdown('</div>', unsafe_allow_html=True)

        with col_b2:
            st.markdown('<div class="content-box">', unsafe_allow_html=True)
            st.markdown(f'<h4>Goal: {g.get("goal_name")}</h4>', unsafe_allow_html=True)
            st.metric("Target Goal", f"₹{g.get('target_amount', 0):,.2f} over {g.get('target_months', 6)} Mo")
            st.metric("Required Monthly Savings", f"₹{g.get('required_monthly_saving', 0):,.2f}")
            gap = g.get('monthly_gap', 0.0)
            st.metric("Current Monthly Cash Surplus", f"₹{g.get('current_monthly_surplus', 0):,.2f}", 
                      delta=f"-₹{gap:,.2f} deficit" if gap > 0 else "Surplus Met", delta_color="normal" if gap <= 0 else "inverse")
            
            if g.get("status") == "On Track":
                st.success(f"✅ {g.get('feasibility_note')}")
            else:
                st.warning(f"⚠️ {g.get('feasibility_note')}")
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------- TAB 6: AGENT EXECUTION TRACE -----------------
with nav[5]:
    st.subheader("Agent Execution Timeline & Audit Trace")
    if not state.audit_log:
        st.info("No active execution traces recorded.")
    else:
        for idx, entry in enumerate(reversed(state.audit_log)):
            icon = "🟢" if entry.status == "success" else "🟡"
            st.markdown(f"**{icon} Step {len(state.audit_log) - idx}: `{entry.step}`** via `{entry.tool}`")
            col_t1, col_t2 = st.columns([3, 1])
            col_t1.write(f"Summary: {entry.output_summary}")
            col_t2.write(f"Duration: `{entry.duration_ms:.2f} ms` | Time: `{entry.timestamp[11:19]}`")
            if entry.input_data:
                with st.expander("Show Step Inputs"):
                    st.json(entry.input_data)
            st.divider()

# ----------------- TAB 7: MONTHLY REPORT -----------------
with nav[6]:
    st.subheader("Monthly Financial Decision Report")
    if not st.session_state.data_loaded:
        st.info("👈 Ingest statement data to compile the monthly report.")
    else:
        sum_m = state.monthly_summary
        st.markdown(f"### Performance Report — {sum_m.get('month', 'Active Month')}")
        st.caption("Generated deterministically by FinPilot decision-support pipeline.")
        
        st.markdown("#### 1. Cash Flow Summary")
        st.write(
            f"- **Recorded Income**: ₹{sum_m.get('income', 0):,.2f}\n"
            f"- **Recorded Outflows**: ₹{sum_m.get('expenses', 0):,.2f}\n"
            f"- **Net Operational Cash Flow**: ₹{sum_m.get('net_cash_flow', 0):,.2f}\n"
            f"- **Observed Savings Rate**: {sum_m.get('savings_rate', 0)}%"
        )

        st.markdown("#### 2. Categorical Concentration")
        top = sum_m.get("largest_category", {})
        st.write(f"- Largest expense concentration: **{top.get('name')}** at ₹{top.get('amount', 0):,.2f} ({top.get('percentage')}% of spending).")

        st.markdown("#### 3. Actionable Next Steps (Data-Backed)")
        st.write(
            "1. **Audit Outlier Expenditures**: Review identified statistical spikes to confirm billing authenticity.\n"
            "2. **Subscription Audit**: Cancel unused subscriptions to restore monthly cash surplus.\n"
            "3. **Target Savings Allocation**: Maintain discretionary spending below limits to meet savings goals."
        )

# ----------------- TAB 8: NORMALIZED RECORDS -----------------
with nav[7]:
    st.subheader("Verified Normalized Transactions")
    if not st.session_state.data_loaded:
        st.info("👈 No transactions ingested.")
    else:
        df_disp = pd.DataFrame([t.model_dump() for t in state.transactions])
        st.dataframe(df_disp, use_container_width=True, hide_index=True)

# ----------------- FOOTER NOTICE -----------------
st.markdown("""
<div style="text-align: center; margin-top: 40px; padding: 20px; color: #94A3B8; font-size: 12px; border-top: 1px solid #E2E8F0;">
    🛡️ FinPilot provides deterministic financial data analysis and decision support only. 
    It does not provide investment, lending, tax, insurance, or financial advice. Demo data is synthetic and deidentified.
</div>
""", unsafe_allow_html=True)