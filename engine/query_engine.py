import os
import pandas as pd
from engine.db_loader import DatabaseManager
from engine.llm_client import FreeLLMClient

class QueryEngine:
    def __init__(self, sales_csv: str, targets_csv: str, data_dict: str, feedback_csv: str = None, provider: str = "gemini"):
        self.db = DatabaseManager(sales_csv, targets_csv, data_dict)
        self.llm = FreeLLMClient(provider=provider)
        self.feedback_csv = feedback_csv
        self.feedback_history = self._load_feedback()

    def _load_feedback(self) -> str:
        if self.feedback_csv and os.path.exists(self.feedback_csv):
            try:
                df = pd.read_csv(self.feedback_csv)
                return df.to_string()
            except Exception:
                return ""
        return ""

    def process_query(self, nl_query: str) -> dict:
        schema_info = self.db.get_schema_info()
        
        # Step 1: Text-to-SQL translation
        llm_res = self.llm.generate_sql_and_explanation(nl_query, schema_info, self.feedback_history)
        
        sql_logic = llm_res.get("generated_logic", "")
        explanation = llm_res.get("explanation", "")
        confidence = float(llm_res.get("initial_confidence", 0.95))

        # Step 2: Execution + Dynamic Error Self-Correction Loop
        max_retries = 2
        result = None
        execution_error = None

        for _ in range(max_retries):
            try:
                result = self.db.execute_query(sql_logic)
                execution_error = None
                break
            except Exception as e:
                execution_error = str(e)
                confidence *= 0.5  # Apply penalty on error
                corrected = self.llm.self_correct_sql(nl_query, schema_info, sql_logic, execution_error)
                sql_logic = corrected.get("generated_logic", sql_logic)
                explanation = f"[Auto-Corrected] {corrected.get('explanation', '')}"

        # Step 3: Confidence Adjustment
        if execution_error:
            confidence = 0.0
            result = f"Execution error: {execution_error}"
        elif result is None or len(result) == 0:
            confidence = round(max(0.2, confidence * 0.7), 2)

        return {
            "query": nl_query,
            "generated_logic": sql_logic,
            "result": result,
            "confidence_score": round(confidence, 2),
            "explanation": explanation
        }