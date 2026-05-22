import subprocess
subprocess.run(['pip', 'install', 'pandas'], check=True)

import pandas as pd
from src.db import execute_query

tables = [
    ('gold_top_insiders', 'SELECT * FROM gold_top_insiders'),
    ('gold_monthly_trends', 'SELECT * FROM gold_monthly_trends'),
    ('gold_sector_patterns', 'SELECT * FROM gold_sector_patterns'),
    ('silver_insider_trades', 'SELECT * FROM silver_insider_trades WHERE pct_change_30d IS NOT NULL'),
]

for name, query in tables:
    r = execute_query(query, fetch=True)
    df = pd.DataFrame(r)
    df.to_csv(f'{name}.csv', index=False)
    print(f'Exported {name}: {len(df)} rows')