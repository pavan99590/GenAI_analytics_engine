import sqlite3
import pandas as pd
import json
import io

class DatabaseManager:
    def __init__(self, sales_csv_path: str, targets_csv_path: str, data_dict_path: str):
        self.conn = sqlite3.connect(":memory:")
        self.data_dict = self._load_json(data_dict_path)
        self._setup_db(sales_csv_path, targets_csv_path)

    def _load_json(self, path: str):
        with open(path, 'r', encoding='utf-8-sig') as f:
            raw_str = f.read()
        
        cleaned_lines = []
        for line in raw_str.splitlines():
            l = line.strip()
            if l.startswith('"') and l.endswith('"') and len(l) > 1:
                l = l[1:-1]
            l = l.replace('""', '"')
            cleaned_lines.append(l)
        
        return json.loads("\n".join(cleaned_lines))

    def _read_cleaned_csv(self, csv_path: str) -> pd.DataFrame:
        """Strips surrounding outer quotes from CSV lines before reading into pandas."""
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            raw_str = f.read()
            
        cleaned_lines = []
        for line in raw_str.splitlines():
            l = line.strip()
            if l.startswith('"') and l.endswith('"') and len(l) > 1:
                l = l[1:-1]
            l = l.replace('""', '"')
            cleaned_lines.append(l)
            
        return pd.read_csv(io.StringIO("\n".join(cleaned_lines)))

    def _setup_db(self, sales_csv: str, targets_csv: str):
        sales_df = self._read_cleaned_csv(sales_csv)
        targets_df = self._read_cleaned_csv(targets_csv)

        # Calculate metric 'revenue' explicitly
        if all(col in sales_df.columns for col in ['quantity', 'unit_price', 'discount']):
            sales_df['revenue'] = sales_df['quantity'] * sales_df['unit_price'] * (1.0 - sales_df['discount'])

        # Create temporal helper columns
        if 'order_date' in sales_df.columns:
            sales_df['order_date'] = pd.to_datetime(sales_df['order_date'])
            sales_df['year'] = sales_df['order_date'].dt.year.astype(str)
            sales_df['month'] = sales_df['order_date'].dt.strftime('%Y-%m')
            sales_df['order_date'] = sales_df['order_date'].dt.strftime('%Y-%m-%d')

        sales_df.to_sql('sales', self.conn, index=False, if_exists='replace')
        targets_df.to_sql('targets', self.conn, index=False, if_exists='replace')

    def execute_query(self, sql_query: str):
        df = pd.read_sql_query(sql_query, self.conn)
        return df.to_dict(orient='records')

    def get_schema_info(self) -> str:
        sales_cols = pd.read_sql_query("PRAGMA table_info(sales);", self.conn)['name'].tolist()
        targets_cols = pd.read_sql_query("PRAGMA table_info(targets);", self.conn)['name'].tolist()

        return f"""
Database Schema:
Table 'sales' columns: {sales_cols}
Table 'targets' columns: {targets_cols}

Data Dictionary Metrics & Mapping Rules:
{json.dumps(self.data_dict, indent=2)}
"""