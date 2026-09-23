import json
import os
import time
from engine.query_engine import QueryEngine

def load_clean_json(path: str):
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

def main():
    PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    
    sales_csv = "data/sales_data.csv"
    targets_csv = "data/targets.csv"
    data_dict = "data/data_dictionary.json"
    nl_queries_file = "data/nl_queries.json"
    feedback_csv = "data/feedback_log.csv"

    print(f" Initializing Engine with Free Provider: [{PROVIDER.upper()}]...")
    engine = QueryEngine(sales_csv, targets_csv, data_dict, feedback_csv, provider=PROVIDER)

    queries_data = load_clean_json(nl_queries_file)

    outputs = []
    print(" Processing Natural Language Queries...\n")

    for idx, item in enumerate(queries_data):
        nl_query = item.get("query") if isinstance(item, dict) else item
        
        # Pause briefly between requests to prevent 429 quota exhaustion
        if idx > 0 and PROVIDER == "gemini":
            time.sleep(5)

        response = engine.process_query(nl_query)
        outputs.append(response)
        
        print(f"Query: {response['query']}")
        print(f"Logic: {response['generated_logic']}")
        print(f"Confidence: {response['confidence_score']}")
        print(f"Explanation: {response['explanation']}")
        print("=" * 60)

    output_path = "output_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2)

    print(f"\n Output saved successfully to {output_path}")

if __name__ == "__main__":
    main()