import os
import json
import time
import re
import warnings
import requests
from google import genai
from google.genai import types
from google.genai.errors import ClientError

# Import Groq SDK
try:
    from groq import Groq
except ImportError:
    Groq = None

warnings.filterwarnings("ignore", category=UserWarning)

class FreeLLMClient:
    def __init__(self, provider: str = "groq"):
        self.provider = provider.lower()
        
        if self.provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise ValueError("GROQ_API_KEY environment variable is missing.")
            if Groq is None:
                raise ImportError("groq package is not installed. Run `pip install groq`.")
            
            self.groq_client = Groq(api_key=api_key)
            
            # Check for custom model override or fallback to account auto-detection
            custom_model = os.getenv("GROQ_MODEL")
            if custom_model:
                self.model_name = custom_model
            else:
                self.model_name = self._get_active_groq_model()

        elif self.provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable is missing.")
            self.client = genai.Client(api_key=api_key)
            self.model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
            
        elif self.provider == "ollama":
            self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            self.model_name = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    def _get_active_groq_model(self) -> str:
        """Dynamically fetch the first available active chat model for the Groq API key."""
        try:
            models_data = self.groq_client.models.list().data
            available_ids = [m.id for m in models_data]
            
            # Priority order matching your available Groq models
            preferred_order = [
                "openai/gpt-oss-120b",
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b",
                "allam-2-7b"
            ]
            
            for pref in preferred_order:
                if pref in available_ids:
                    print(f"  [Groq Auto-Select] Using model: {pref}")
                    return pref
            
            # Exclude audio/guard models from fallbacks
            chat_models = [
                m for m in available_ids 
                if not any(x in m for x in ["whisper", "safeguard", "prompt-guard"])
            ]
            if chat_models:
                print(f"  [Groq Auto-Select] Using fallback model: {chat_models[0]}")
                return chat_models[0]
        except Exception as e:
            print(f"  [Warning] Could not list Groq models automatically: {e}")
            
        return "openai/gpt-oss-120b"

    def _call_groq(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls Groq API using JSON response format with rate-limit retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.groq_client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    response_format={"type": "json_object"}
                )
                return json.loads(response.choices[0].message.content)
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    print("  [Groq Rate Limit] Waiting 5s before retrying...")
                    time.sleep(5)
                else:
                    raise e

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls Gemini API using JSON response format with dynamic retry handling."""
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.0,
            response_mime_type="application/json"
        )
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=user_prompt,
                    config=config
                )
                return json.loads(response.text)
            except ClientError as e:
                if e.code == 429 and attempt < max_retries - 1:
                    match = re.search(r"retry in (\d+(\.\d+)?)s", str(e), re.IGNORECASE)
                    wait_time = float(match.group(1)) + 1.0 if match else (attempt + 1) * 10.0
                    print(f"  [Rate Limit] Waiting {wait_time:.1f}s before retrying...")
                    time.sleep(wait_time)
                else:
                    raise e

    def _call_ollama(self, system_prompt: str, user_prompt: str) -> dict:
        """Calls local Ollama API returning JSON."""
        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\nUser Question: {user_prompt}\nReturn JSON ONLY:",
            "stream": False,
            "format": "json"
        }
        res = requests.post(self.ollama_url, json=payload)
        res_json = res.json()
        return json.loads(res_json.get("response", "{}"))

    def generate_sql_and_explanation(self, nl_query: str, schema_info: str, feedback_history: str = "") -> dict:
        system_prompt = f"""
You are an expert Text-to-SQL AI Engine targeting SQLite 3.
Convert the natural language question into a valid, executable SQLite query.

Schema and Data Dictionary Context:
{schema_info}

Historical Feedback & Past Corrections:
{feedback_history}

Output Format Requirement:
Return ONLY a valid JSON object matching this schema:
{{
    "generated_logic": "",
    "explanation": "",
    "initial_confidence": 
}}

Strict SQLite Dialect Rules:
1. Always use exact column names as defined in the schema (all lowercase: region, country, city, product_category, order_date, etc.).
2. For dates, use `strftime('%Y', order_date)` or `strftime('%Y-%m', order_date)`. DO NOT use EXTRACT(YEAR FROM ...).
3. Derived revenue: `quantity * unit_price * (1.0 - discount)`.
4. Pre-calculated date columns available: `year` (e.g. '2024'), `month` (e.g. '2024-02').
5. Window functions like `RANK() OVER (PARTITION BY ... ORDER BY ...)` and `LAG()` are fully supported.
6. Do not wrap output in markdown codeblocks. Return pure JSON.
"""
        user_prompt = f"Natural Language Query: {nl_query}"

        if self.provider == "groq":
            return self._call_groq(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            return self._call_ollama(system_prompt, user_prompt)

    def self_correct_sql(self, nl_query: str, schema_info: str, failed_sql: str, error_msg: str) -> dict:
        system_prompt = f"""
You are a SQL debugging expert for SQLite 3. A generated SQL query failed during execution.

Schema Context:
{schema_info}

Original Query: {nl_query}
Failed SQL: {failed_sql}
Execution Error: {error_msg}

Correct the SQL query to valid SQLite 3 syntax and return pure JSON:
{{
    "generated_logic": "",
    "explanation": "",
    "initial_confidence": 
}}
"""
        user_prompt = "Fix the broken SQL execution error for SQLite 3."

        if self.provider == "groq":
            return self._call_groq(system_prompt, user_prompt)
        elif self.provider == "gemini":
            return self._call_gemini(system_prompt, user_prompt)
        else:
            return self._call_ollama(system_prompt, user_prompt)