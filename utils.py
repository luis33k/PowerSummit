import pandas as pd
import numpy as np
from logger import setup_logger

logger = setup_logger()
logger.info("Utils module initialized")

def compute_recovery_score_sleep_tsb(sleep: float, tsb: float) -> float:
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
        logger.info(f"Computing recovery score: sleep={sleep}, tsb={tsb} -> NaN (missing values)")
        return np.nan
    # Normalize sleep: assume 7-9 hours optimal
    norm_sleep = min(max((sleep - 7) / 2, 0), 1)
    # Negative TSB factor: higher TSB (more fatigue) lowers score
    tsb_factor = max(0, 1 - abs(tsb) / 50)  # Arbitrary scaling
    score = (norm_sleep + tsb_factor) / 2
    logger.info(f"Computing recovery score: sleep={sleep}, tsb={tsb} -> score={score}")
    return score

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
    Now aggregates by date for totals.

    Args:
        df (pd.DataFrame): DataFrame with metrics.

    Returns:
        dict: KPIs.
    """
    if df.empty:
        return {'7d TSS': 0.0, 'CTL': 0.0, 'ATL': 0.0, 'Latest TSB': 0.0, 'Avg Sleep 7d': 0.0}

    # Since data is already aggregated per date in metrics.py, just use the latest values
    if not df.empty:
        # Get the last row for latest values
        latest = df.iloc[-1]
        # Handle duplicate columns by selecting the first one, or None if not found
        tss_col = next((col for col in df.columns if 'Total TSS (Bike + Run)' in col), None)
        ctl_col = next((col for col in df.columns if 'CTL (EWMA)' in col), None)
        atl_col = next((col for col in df.columns if 'ATL (EWMA)' in col), None)
        tsb_col = next((col for col in df.columns if 'TSB (EWMA)' in col), None)
        sleep_col = next((col for col in df.columns if 'Sleep (hrs)' in col), None)

        kpis = {
            '7d TSS': df[tss_col].tail(7).sum() if tss_col else 0.0,
            'CTL': latest[ctl_col] if ctl_col else 0.0,
            'ATL': latest[atl_col] if atl_col else 0.0,
            'Latest TSB': latest[tsb_col] if tsb_col else 0.0,
            'Avg Sleep 7d': df[sleep_col].tail(7).mean() if sleep_col else 0.0
        }
        # Convert to float if needed
        for key in kpis:
            try:
                if hasattr(kpis[key], 'item') and kpis[key].size == 1:
                    kpis[key] = kpis[key].item()
                elif isinstance(kpis[key], (int, float)):
                    kpis[key] = float(kpis[key])
                else:
                    # For Series or other types, try to get a scalar
                    if hasattr(kpis[key], 'iloc'):
                        kpis[key] = float(kpis[key].iloc[0]) if not kpis[key].empty else 0.0
                    else:
                        kpis[key] = float(kpis[key]) if not pd.isna(kpis[key]) else 0.0
            except:
                kpis[key] = 0.0
    else:
        kpis = {'7d TSS': 0.0, 'CTL': 0.0, 'ATL': 0.0, 'Latest TSB': 0.0, 'Avg Sleep 7d': 0.0}
    return kpis
