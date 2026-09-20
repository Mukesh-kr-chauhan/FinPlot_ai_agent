from tools.normalization import DataNormalizer
from tools.anomalies import AnomalyDetector


def test_category_aware_anomaly():
    # 5 standard food expenses and 1 massive outlier
    csv_data = """date,description,amount,category,account,type
2026-09-01,Lunch,300,Food,Bank,debit
2026-09-02,Dinner,350,Food,Bank,debit
2026-09-03,Snacks,280,Food,Bank,debit
2026-09-04,Lunch,320,Food,Bank,debit
2026-09-05,Dinner,310,Food,Bank,debit
2026-09-06,Ultra Luxury Caviar Feast,15000,Food,Bank,debit
"""
    txs, _ = DataNormalizer.parse_csv(csv_data)
    anomalies = AnomalyDetector.detect_anomalies(txs)
    
    assert len(anomalies) == 1
    assert anomalies[0].amount == 15000.0
    assert anomalies[0].category == "Food"