from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Transaction(BaseModel):
    transaction_id: str
    date: str
    description: str
    amount: float
    category: str
    account: str
    transaction_type: str  # "debit" (expense) or "credit" (income)


class RecurringPattern(BaseModel):
    description: str
    category: str
    occurrences: int
    average_amount: float
    amount_variation: float
    average_interval: float
    frequency: str  # weekly, monthly, quarterly
    confidence: float
    last_payment: str
    next_estimated_date: str
    is_subscription: bool


class AnomalyRecord(BaseModel):
    transaction_id: str
    date: str
    description: str
    amount: float
    category: str
    baseline_mean: float
    baseline_std: float
    threshold: float
    severity: str  # "low", "medium", "high"
    reason: str
    confidence: float


class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    step: str
    tool: str
    input_data: Dict[str, Any]
    output_summary: str
    status: str  # "success", "warning", "failed"
    duration_ms: float = 0.0


class VerificationResult(BaseModel):
    passed: bool
    checks_performed: List[str]
    discrepancies: List[str]
    reconciliation_details: Dict[str, Any]


class AgentState(BaseModel):
    user_goal: str = ""
    user_query: str = ""
    intent: str = ""
    
    # Raw & processed records
    raw_records_count: int = 0
    transactions: List[Transaction] = Field(default_factory=list)
    
    # Specialized analysis outputs
    selected_month: str = ""
    monthly_summary: Dict[str, Any] = Field(default_factory=dict)
    month_comparison: Dict[str, Any] = Field(default_factory=dict)
    recurring_payments: List[RecurringPattern] = Field(default_factory=list)
    subscriptions: List[RecurringPattern] = Field(default_factory=list)
    anomalies: List[AnomalyRecord] = Field(default_factory=list)
    budget_status: Dict[str, Any] = Field(default_factory=dict)
    goal_status: Dict[str, Any] = Field(default_factory=dict)
    
    # Agent execution tracking
    plan: List[str] = Field(default_factory=list)
    current_step_index: int = 0
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    audit_log: List[AuditEntry] = Field(default_factory=list)
    
    # Verification & Replanning
    verification: VerificationResult = Field(
        default_factory=lambda: VerificationResult(
            passed=False, checks_performed=[], discrepancies=[], reconciliation_details={}
        )
    )
    replan_count: int = 0
    max_replans: int = 3
    
    # Final outputs
    insights: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    answer: str = ""
    status: str = "initialized"