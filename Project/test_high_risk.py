import json
import urllib.request
import time

time.sleep(1)

test_cases = [
    {
        'name': 'HIGH RISK: New customer, high charges, month-to-month',
        'data': {'customer_id': 'RISK-001', 'tenure': 1, 'monthly_charges': 95, 'contract_type': 'Month-to-month', 'service_count': 1}
    },
    {
        'name': 'HIGH RISK: Low tenure, high charges',
        'data': {'customer_id': 'RISK-002', 'tenure': 3, 'monthly_charges': 85, 'contract_type': 'Month-to-month', 'service_count': 2}
    },
    {
        'name': 'HIGH RISK: Month-to-month with minimal services',
        'data': {'customer_id': 'RISK-003', 'tenure': 2, 'monthly_charges': 75, 'contract_type': 'Month-to-month', 'service_count': 0}
    },
    {
        'name': 'MEDIUM RISK: 6 months tenure',
        'data': {'customer_id': 'MED-001', 'tenure': 6, 'monthly_charges': 70, 'contract_type': 'Month-to-month', 'service_count': 2}
    },
    {
        'name': 'LOW RISK: Long-term, one-year contract',
        'data': {'customer_id': 'LOW-001', 'tenure': 24, 'monthly_charges': 65, 'contract_type': 'One year', 'service_count': 4}
    },
    {
        'name': 'VERY LOW RISK: Two-year contract, high tenure',
        'data': {'customer_id': 'LOW-002', 'tenure': 60, 'monthly_charges': 50, 'contract_type': 'Two year', 'service_count': 5}
    },
]

print("=" * 80)
print("CHURN PREDICTION TEST SUITE")
print("=" * 80)
print()

for test in test_cases:
    data = json.dumps(test['data']).encode('utf-8')
    req = urllib.request.Request(
        'http://localhost:8000/predict-churn',
        data=data,
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': 'mysecret123'
        },
        method='POST'
    )
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        print(f"✓ {test['name']}")
        print(f"  Customer ID: {result['customer_id']}")
        print(f"  Tenure: {test['data']['tenure']} months")
        print(f"  Monthly Charges: ${test['data']['monthly_charges']}")
        print(f"  Contract: {test['data']['contract_type']}")
        print(f"  Services: {test['data']['service_count']}")
        print(f"  >>> Risk Score: {result['risk_score']}%")
        print(f"  >>> Prediction: {result['prediction']}")
        print(f"  >>> Confidence: {result['confidence']}%")
        print()
    except Exception as e:
        print(f"✗ Error testing {test['name']}: {e}")
        print()

print("=" * 80)
