# GenAI Analytics Engine: Text-to-SQL Pipeline

**Project:** Generative AI Analytics Engine    
**Database:** SQLite 3  
**LLM Providers:** Groq, Google Gemini, Ollama

## Project Overview

This project is an automated Text-to-SQL Analytics Engine that converts natural language questions into executable SQLite SQL queries.

It supports queries related to sales, regions, products, targets, revenue, and business analytics.

The system also validates generated SQL and automatically corrects SQL when execution errors occur.

## Architecture

Natural Language Query  
↓  
LLM Client (Groq / Gemini / Ollama)  
↓  
JSON Response Parsing  
↓  
Generated SQLite SQL  
↓  
SQLite Execution  
↓  
Error → LLM Self-Correction  
↓  
Final Result  
↓  
output_results.json

## Key Features

- Multi-LLM support using Groq, Gemini, and Ollama
- SQLite 3 compatible SQL generation
- Revenue calculation using `quantity * unit_price * (1.0 - discount)`
- SQLite date handling using `strftime()`
- Window functions such as `RANK()`, `LAG()`, and `SUM() OVER()`
- Automatic SQL error correction
- Structured JSON output
- Dynamic Groq model selection
- Exponential backoff for Gemini rate limits

## Project Structure

GenAI_analytics_engine/
├── engine/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── query_engine.py
│   └── schema.py
├── data/
│   └── sales.db
├── main.py
├── requirements.txt
├── output_results.json
└── README.md

## Setup

### 1. Create Virtual Environment

    python -m venv venv

Windows PowerShell:

    .\venv\Scripts\Activate.ps1

Linux/macOS:

    source venv/bin/activate

### 2. Install Dependencies

    pip install -r requirements.txt

### 3. Configure API Key

For Groq:

    $env:GROQ_API_KEY="your_groq_api_key"

For Gemini:

    $env:GEMINI_API_KEY="your_gemini_api_key"

### 4. Run

    python main.py

## Example

Input:

    Total sales in India for March

Generated SQL:

    SELECT SUM(quantity * unit_price * (1.0 - discount)) AS total_sales
    FROM sales
    WHERE country = 'India'
      AND strftime('%m', order_date) = '03';

Output:

    {
      "nl_query": "Total sales in India for March",
      "generated_logic": "SELECT SUM(quantity * unit_price * (1.0 - discount)) AS total_sales FROM sales WHERE country = 'India' AND strftime('%m', order_date) = '03';",
      "confidence": 0.97,
      "explanation": "Calculates total revenue for orders in India during March."
    }

## Edge Cases Handled

- Dynamic LLM model availability
- SQL execution errors
- Division by zero using `NULLIF()`
- Correct revenue calculation
- SQLite-specific date handling
- SQL self-correction using database error feedback

## Technologies

Python • SQLite 3 • Groq • Google Gemini • Ollama • SQL • LLMs • JSON