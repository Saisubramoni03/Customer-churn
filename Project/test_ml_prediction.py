import json
import urllib.request
import urllib.error

headers = {'X-API-Key': 'mysecret123', 'Content-Type': 'application/json'}

# Test 1: High risk customer
data1 = {
    'customer_id': 'TEST-HIGHRISK',
    'tenure': 2,  # Very new customer (high churn risk)
    'monthly_charges': 65.5,
    'contract_type': 'Month-to-month',  # Highest risk contract
    'service_count': 1  # Few services
}

# Test 2: Low risk customer
data2 = {
    'customer_id': 'TEST-LOWRISK',
    'tenure': 60,  # Long tenure (low churn risk)
    'monthly_charges': 90.0,
    'contract_type': 'Two year',  # Lowest risk contract
    'service_count': 6  # Many services
}

print("Testing Churn Prediction API\n")
print("=" * 60)

for test_name, test_data in [("High Risk", data1), ("Low Risk", data2)]:
    try:
        url = 'http://localhost:8000/predict-churn'
        body = json.dumps(test_data).encode('utf-8')
        request = urllib.request.Request(url, data=body, headers=headers, method='POST')
        
        with urllib.request.urlopen(request) as response:
            result = json.loads(response.read().decode('utf-8'))
            
            print(f"\n{test_name} Prediction:")
            print(f"  Customer ID: {result['customer_id']}")
            print(f"  Tenure: {test_data['tenure']} months")
            print(f"  Contract: {test_data['contract_type']}")
            print(f"  Risk Score: {result['risk_score']*100:.1f}%")
            print(f"  Prediction: {result['prediction']}")
            print(f"  Note: {result['note']}")
    except Exception as e:
        print(f"\n✗ {test_name} Error: {e}")

print("\n" + "=" * 60)
