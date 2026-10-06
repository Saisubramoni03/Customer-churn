import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database import engine
import pandas as pd

# Check the database table structure
query = '''
SELECT COLUMN_NAME, COLUMN_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'customer_retention'
AND TABLE_NAME = 'customer_ml_features'
ORDER BY COLUMN_NAME
'''

try:
    df = pd.read_sql(query, engine)
    print('Customer ML Features Table Schema:')
    print('=' * 60)
    print(df.to_string(index=False))
    print()
    print(f'Total columns: {len(df)}')
    print()
    
    # Get a sample row
    query2 = 'SELECT * FROM customer_ml_features LIMIT 1'
    sample = pd.read_sql(query2, engine)
    print('Sample Row Values:')
    print('=' * 60)
    for col in sample.columns:
        print(f'{col}: {sample[col].iloc[0]}')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
