from tools.normalization import DataNormalizer
from tools.recurring import RecurringEngine


def test_subscription_detection():
    csv_data = """date,description,amount,category,account,type
2026-07-05,Netflix Subscription,649.00,Subscription,Card,debit
2026-08-05,Netflix Subscription,649.00,Subscription,Card,debit
2026-09-05,Netflix Subscription,649.00,Subscription,Card,debit
"""
    txs, _ = DataNormalizer.parse_csv(csv_data)
    patterns = RecurringEngine.detect_recurring(txs)
    
    assert len(patterns) == 1
    netflix = patterns[0]
    assert netflix.description == "Netflix Subscription"
    assert netflix.frequency == "Monthly"
    assert netflix.is_subscription is True
    assert netflix.amount_variation == 0.0