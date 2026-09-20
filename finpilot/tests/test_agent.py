from agent.core import FinPilotAgent
from agent.state import AgentState
from tools.normalization import DataNormalizer


def test_agent_end_to_end_category_query():
    csv_data = """date,description,amount,category,account,type
2026-09-01,Salary,50000,Income,Bank,credit
2026-09-02,Apartment Rent,18000,Housing,Bank,debit
2026-09-03,Dining,2000,Food,Bank,debit
"""
    txs, _ = DataNormalizer.parse_csv(csv_data)
    state = AgentState(transactions=txs, raw_records_count=len(txs))
    
    agent = FinPilotAgent()
    res = agent.process_query("Where did I spend the most this month?", state)
    
    assert res.status == "completed"
    assert res.verification.passed is True
    assert "Housing" in res.answer
    assert "18,000" in res.answer
    assert len(res.audit_log) > 0