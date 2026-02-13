import io
import os
import sys
import json
import tempfile
from pathlib import Path

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv()

# ================= DATA LOADER =================
def load_data(file_or_path):
    """
    CSV, Excel (xls, xlsx), aur JSON files ko load karta hai
    Multiple encodings support karta hai
    """
    if isinstance(file_or_path, (str, Path)):
        ext = Path(file_or_path).suffix.lower()
        
        # CSV file
        if ext == ".csv":
            for encoding in ['utf-8', 'latin-1', 'ISO-8859-1', 'cp1252']:
                try:
                    return pd.read_csv(file_or_path, encoding=encoding)
                except UnicodeDecodeError:
                    continue
            return pd.read_csv(file_or_path, encoding='utf-8', errors='ignore')
        
        # Excel files
        if ext in [".xls", ".xlsx"]:
            return pd.read_excel(file_or_path)
        
        # JSON file
        if ext == ".json":
            return pd.read_json(file_or_path)
    
    # Streamlit uploaded file ke liye
    try:
        raw = file_or_path.read()
        file_or_path.seek(0)  # Reset pointer for future reads
        
        # File extension check karo
        file_name = getattr(file_or_path, 'name', '')
        ext = Path(file_name).suffix.lower()
        
        # Excel file
        if ext in [".xls", ".xlsx"]:
            return pd.read_excel(io.BytesIO(raw))
        
        # JSON file
        if ext == ".json":
            return pd.read_json(io.BytesIO(raw))
        
        # CSV file (default)
        for encoding in ['utf-8', 'latin-1', 'ISO-8859-1', 'cp1252']:
            try:
                return pd.read_csv(io.BytesIO(raw), encoding=encoding)
            except (UnicodeDecodeError, Exception):
                continue
        
        # Last resort - errors ignore kar do
        return pd.read_csv(io.BytesIO(raw), encoding='utf-8', errors='ignore')
    
    except Exception as e:
        raise ValueError(f"File load nahi ho saki: {str(e)}")


# ================= SUGGESTION PROMPTS =================
def suggest_prompts(df: pd.DataFrame):
    """
    Advanced Business Intelligence Prompts
    """
    prompts = [
        # BASIC OVERVIEW
        "Show total revenue generated in the dataset.",
        "Show overall total quantity sold.",
        "Display dataset summary with business insights.",
        "Show first 10 rows of the dataset.",
        "Show column names and their data types.",
        "Display basic statistical summary of numerical columns.",

        # CATEGORY ANALYSIS
        "Show category-wise total revenue and percentage contribution.",
        "Create a pie chart of revenue distribution by category.",
        "Create a bar chart of category-wise total sales.",
        "Identify highest revenue generating category.",

        # PRODUCT PERFORMANCE
        "Show top 10 best selling products based on quantity.",
        "Show top 10 highest revenue generating products.",
        "Show bottom 5 least selling products.",
        "Identify slow moving products based on low sales volume.",

        # PROFIT ANALYSIS
        "Calculate total profit if cost price and selling price columns exist.",
        "Show profit percentage per product.",
        "Identify products with lowest profit margin.",
        "Find products generating highest profit margin.",

        # INVENTORY INSIGHTS
        "Identify low stock products that require restocking.",
        "Show products with high stock but low sales.",
        "Highlight dead stock items with zero sales.",

        # TREND ANALYSIS
        "Show monthly sales trend using a line chart.",
        "Identify seasonal sales pattern from date column if available.",
        "Create a line chart showing sales over time.",
        
        # DATA QUALITY
        "Show missing values count for each column.",
        "Display duplicate rows in the dataset.",
        "Show unique values count for each column.",
    ]
    
    return prompts


# ================= CODE EXECUTOR =================
def run_code(df, code):
    """
    Python code ko safely execute karta hai
    DataFrame, plots, aur text output handle karta hai
    """
    local_vars = {"df": df, "pd": pd, "np": np, "plt": plt}
    old_stdout = sys.stdout
    sys.stdout = buffer = io.StringIO()

    try:
        exec(code, {}, local_vars)

        # Agar plot bana hai toh image return karo
        if plt.get_fignums():
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as f:
                plt.savefig(f.name, bbox_inches="tight", dpi=100)
                plt.close("all")
                return {"type": "image", "path": f.name}

        # Agar result variable hai toh use return karo
        if "result" in local_vars:
            res = local_vars["result"]
            if isinstance(res, pd.DataFrame):
                return {"type": "dataframe", "df": res}
            return {"type": "text", "output": str(res)}

        # Console output return karo
        output_text = buffer.getvalue()
        if output_text.strip():
            return {"type": "text", "output": output_text}
        
        return {"type": "text", "output": "Code successfully executed!"}

    except Exception as e:
        return {"type": "text", "output": f"❌ Error: {str(e)}"}

    finally:
        sys.stdout = old_stdout


# ================= OPENROUTER API =================
def ask_llm(prompt: str):
    """
    LLM se Python code generate karta hai
    """
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        return "```python\n# Error: OPENROUTER_API_KEY missing in .env file\nprint('Please add OPENROUTER_API_KEY to .env file')\n```"

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "model": "stepfun/step-3.5-flash:free",
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a data analyst. "
                            "Return ONLY python code inside ```python``` blocks. "
                            "DataFrame name is 'df'. "
                            "Use pandas, numpy, and matplotlib for analysis. "
                            "For output, either print results or assign to 'result' variable. "
                            "For plots, use plt.show() at the end."
                        )
                    },
                    {"role": "user", "content": prompt}
                ]
            }),
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    except Exception as e:
        return f"```python\n# Error calling LLM: {str(e)}\nprint('LLM API Error')\n```"

