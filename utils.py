import pandas as pd
import numpy as np

def compute_recovery_score(sleep: float, tsb: float) -> float:
    """
    Compute Recovery Score = normalized sleep + negative TSB factor.

    Normalize sleep to 0-1, TSB negative impact.

    Args:
        sleep (float): Sleep hours.
        tsb (float): Training Stress Balance.

    Returns:
        float: Recovery Score.
    """
    if pd.isna(sleep) or pd.isna(tsb):
        return np.nan
    # Normalize sleep: assume 7-9 hours optimal
    norm_sleep = min(max((sleep - 7) / 2, 0), 1)
    # Negative TSB factor: higher TSB (more fatigue) lowers score
    tsb_factor = max(0, 1 - abs(tsb) / 50)  # Arbitrary scaling
    return (norm_sleep + tsb_factor) / 2

def save_processed_data(df: pd.DataFrame, path: str):
    """
    Save processed DataFrame to CSV.

    Args:
        df (pd.DataFrame): DataFrame to save.
        path (str): Output path.
    """
    df.to_csv(path, index=False)

def get_top_kpis(df: pd.DataFrame) -> dict:
    """
    Get top KPIs: 7d TSS, CTL, ATL, latest TSB, avg sleep 7d.

    Args:
        df (pd.DataFrame): DataFrame with metrics.

    Returns:
        dict: KPIs.
    """
    latest = df.iloc[-1] if not df.empty else {}
    kpis = {
        '7d TSS': float(df['Total TSS (Bike + Run)'].tail(7).sum()) if not df.empty else 0.0,
        'CTL': float(latest.get('CTL (42d EWMA)', np.nan)) if not pd.isna(latest.get('CTL (42d EWMA)', np.nan)) else 0.0,
        'ATL': float(latest.get('ATL (7d EWMA)', np.nan)) if not pd.isna(latest.get('ATL (7d EWMA)', np.nan)) else 0.0,
        'Latest TSB': float(latest.get('TSB (EWMA)', np.nan)) if not pd.isna(latest.get('TSB (EWMA)', np.nan)) else 0.0,
        'Avg Sleep 7d': float(df['Sleep'].tail(7).mean()) if not df.empty and not pd.isna(df['Sleep'].tail(7).mean()) else 0.0
    }
    return kpis
