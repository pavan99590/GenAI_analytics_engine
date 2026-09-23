# GenAI Analytics Engine: Text-to-SQL Pipeline

**Project:** Generative AI Analytics Engine    
**Database:** SQLite 3  
**LLM Providers:** Groq, Google Gemini, Ollama

---

## Project Overview

This project is an automated **Text-to-SQL Analytics Engine** that converts natural language questions into executable SQLite SQL queries.

It supports queries related to sales, regions, products, targets, revenue, and business analytics.

The system also validates generated SQL and automatically corrects SQL when execution errors occur.

---

## Architecture

```
Natural Language Query
        |
        v
LLM Client
(Groq / Gemini / Ollama)
        |
        v
JSON Response Parsing
        |
        v
Generated SQLite SQL
        |
        v
SQLite Execution
        |
        +---- Error ----> LLM Self-Correction
        |
        v
Final Result
        |
        v
output_results.json
```

---

## Key Features

- **Multi-LLM Support:** Groq, Gemini, and local Ollama
- **SQLite 3 Compatible:** Generates SQLite-specific SQL
- **Revenue Calculation:** `quantity * unit_price * (1.0 - discount)`
- **Date Handling:** Uses SQLite `strftime()`
- **Window Functions:** Supports `RANK()`, `LAG()`, and `SUM() OVER()`
- **Self-Correction:** Sends SQL errors back to the LLM for correction
- **Structured Output:** Saves results to `output_results.json`
- **Dynamic Model Selection:** Automatically detects available Groq models

---

## Project Structure

```
GenAI_analytics_engine/
├── engine/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── query_engine.py
│   └── schema.py
│
├── data/
│   └── sales.db
│
├── main.py
├── requirements.txt
├── output_results.json
└── README.md
```

---

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
```

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Linux/macOS:**

```bash
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure API Key

**Groq:**

```powershell
$env:GROQ_API_KEY="your_groq_api_key"
```

**Gemini:**

```powershell
$env:GEMINI_API_KEY="your_gemini_api_key"
```

### 4. Run

```bash
python main.py
```

---

## Example

### Input

```text
Total sales in India for March
```

### Generated SQL

```sql
SELECT
    SUM(quantity * unit_price * (1.0 - discount)) AS total_sales
FROM sales
WHERE country = 'India'
  AND strftime('%m', order_date) = '03';
```

### Output

```json
{
  "nl_query": "Total sales in India for March",
  "generated_logic": "SELECT SUM(quantity * unit_price * (1.0 - discount)) AS total_sales FROM sales WHERE country = 'India' AND strftime('%m', order_date) = '03';",
  "confidence": 0.97,
  "explanation": "Calculates total revenue for orders in India during March."
}
```

---

## Edge Cases Handled

- Dynamic LLM model availability
- SQL execution errors
- Division by zero using `NULLIF()`
- Correct revenue calculation
- SQLite-specific date handling
- SQL self-correction using database error feedback

---

## Technologies

**Python** • **SQLite 3** • **Groq** • **Google Gemini** • **Ollama** • **SQL** • **LLMs** • **JSON**