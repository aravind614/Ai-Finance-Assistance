import sys
import io
import pandas as pd
from typing import Dict, List, Any

def calculate_growth(current: float, previous: float) -> float | None:
    if not previous:
        return None
    return ((current - previous) / previous) * 100

def calculate_cagr(start_value: float, end_value: float, periods: int) -> float | None:
    if start_value <= 0 or end_value <= 0 or periods <= 0:
        return None
    return ((end_value / start_value) ** (1 / periods) - 1) * 100

def calculate_roi(gain: float, cost: float) -> float | None:
    if not cost:
        return None
    return ((gain - cost) / cost) * 100

def generate_comparison_table(companies_data: List[Dict[str, Any]]) -> str:
    """
    Generate a markdown comparison table from a list of company data.
    """
    if not companies_data:
        return "No comparison data available."
    
    df = pd.DataFrame(companies_data)
    return df.to_markdown(index=False)

def run_calculation_code(code_str: str) -> str:
    """
    Executes financial calculation code in python and returns the printed output.
    """
    # Create local environment with helper functions pre-imported
    local_env = {
        "calculate_growth": calculate_growth,
        "calculate_cagr": calculate_cagr,
        "calculate_roi": calculate_roi,
        "generate_comparison_table": generate_comparison_table,
        "pd": pd
    }
    
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        # Exec code
        exec(code_str, {}, local_env)
        sys.stdout = old_stdout
        return redirected_output.getvalue().strip()
    except Exception as e:
        sys.stdout = old_stdout
        return f"Error executing calculation: {str(e)}"
