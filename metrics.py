import pandas as pd
import numpy as np
from scipy import stats

def calculate_if_cycling(avg_watt: float, ftp_used: float) -> float:
    """
    Calculate Intensity Factor (IF) for cycling.

    IF = Avg Watt / FTP_used

    Handles 0/NaN by returning NaN.

    Args:
        avg_watt (float): Average watts.
        ftp_used (float): FTP used.

    Returns:
        float: Intensity Factor.
    """
    if pd.isna(avg_watt) or pd.isna(ftp_used) or ftp_used == 0:
        return np.nan
    return avg_watt / ftp_used

def calculate_cycling_tss(duration_hr: float, intensity_factor: float) -> float:
    """
    Calculate Training Stress Score (TSS) for cycling.

    TSS = duration_hr * (IF**2) * 100

    Args:
        duration_hr (float): Duration in hours.
        intensity_factor (float): Intensity Factor.

    Returns:
        float: TSS.
    """
    if pd.isna(duration_hr) or pd.isna(intensity_factor):
        return np.nan
    return duration_hr * (intensity_factor ** 2) * 100

def calculate_run_tss(duration_min: float, rpe: float) -> float:
    """
    Calculate Training Stress Score (TSS) for running.

    TSS = (duration_min * RPE^2) / 30

    Args:
        duration_min (float): Duration in minutes.
        rpe (float): Rate of Perceived Exertion.

    Returns:
        float: TSS.
    """
    if pd.isna(duration_min) or pd.isna(rpe):
        return np.nan
    return (duration_min * (rpe ** 2)) / 30

def calculate_total_tss(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Total TSS by combining bike and run TSS.

    Assumes columns: 'Cycling TSS', 'Run TSS'

    Args:
        df (pd.DataFrame): DataFrame with TSS columns.

    Returns:
        pd.Series: Total TSS.
    """
    cycling_tss = df.get('Cycling TSS', pd.Series([np.nan] * len(df)))
    run_tss = df.get('Run TSS', pd.Series([np.nan] * len(df)))
    return cycling_tss.fillna(0) + run_tss.fillna(0)

def calculate_atl_ctl_tsb(total_tss: pd.Series, span_atl: int = 7, span_ctl: int = 42) -> tuple:
    """
    Compute EWMA-based ATL (span=7 days) and CTL (span=42 days) on Total TSS, and TSB = CTL - ATL.

    Args:
        total_tss (pd.Series): Total TSS series.
        span_atl (int): Span for ATL.
        span_ctl (int): Span for CTL.

    Returns:
        tuple: (ATL, CTL, TSB)
    """
    atl = total_tss.ewm(span=span_atl).mean()
    ctl = total_tss.ewm(span=span_ctl).mean()
    tsb = ctl - atl
    return atl, ctl, tsb

def calculate_rolling_averages(df: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """
    Compute 7-day rolling averages for avg watt, sleep, carbs/hr, KJ.

    Args:
        df (pd.DataFrame): DataFrame with relevant columns.
        window (int): Rolling window in days.

    Returns:
        pd.DataFrame: DataFrame with rolling averages.
    """
    columns_to_roll = []
    if 'Avg Watt' in df.columns:
        columns_to_roll.append('Avg Watt')
    if 'Sleep' in df.columns:
        columns_to_roll.append('Sleep')
    if 'Carbs/hr' in df.columns:
        columns_to_roll.append('Carbs/hr')
    if 'KJ' in df.columns:
        columns_to_roll.append('KJ')
    if not columns_to_roll:
        return pd.DataFrame({'Date': df['Date']})
    rolling_df = df.set_index('Date')[columns_to_roll].rolling(window=window).mean().reset_index()
    # Rename columns to avoid duplicates during merge
    rolling_df.columns = [col + '_7d_avg' if col != 'Date' else col for col in rolling_df.columns]
    return rolling_df

def compute_all_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute all metrics for the DataFrame.

    Adds columns for cycling, running, totals, rolling averages, fitness/fatigue.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with added metrics.
    """
    df = df.copy()

    # Cycling Calculations
    if 'Cycling Duration (hrs)' in df.columns and 'Avg Watt (Est)' in df.columns:
        df['Cycling KJ'] = df['Cycling Duration (hrs)'] * df['Avg Watt (Est)'] * 3600 / 1000
        df['Cycling Calories Burned'] = df['Cycling KJ'] * 0.95

    if 'Avg Watt (Est)' in df.columns and 'FTP_used' in df.columns:
        df['Cycling Intensity Factor (IF)'] = df['Avg Watt (Est)'] / df['FTP_used']

    if 'Cycling Duration (hrs)' in df.columns and 'Cycling Intensity Factor (IF)' in df.columns:
        df['Cycling TSS (Est)'] = df['Cycling Duration (hrs)'] * (df['Cycling Intensity Factor (IF)'] ** 2) * 100

    # Running Calculations
    if 'Run Duration (hrs)' in df.columns and 'Run RPE' in df.columns:
        duration_min = df['Run Duration (hrs)'] * 60
        df['Run TSS (Est)'] = (duration_min * (df['Run RPE'] ** 2)) / 30

    # Assume MET for running calories; if 'MET' column exists, use it, else assume 10
    if 'Run Duration (hrs)' in df.columns:
        met = df.get('MET', 10)  # Default MET 10
        weight_kg = df.get('Weight (lbs)', 70) * 0.453592  # Convert lbs to kg, default 70kg
        df['Run Calories Burned'] = met * weight_kg * df['Run Duration (hrs)']
        df['Run KJ'] = df['Run Calories Burned'] * 4.184

    # Totals
    df['Total Training Hr'] = df.get('Cycling Duration (hrs)', pd.Series([0]*len(df))).fillna(0) + df.get('Run Duration (hrs)', pd.Series([0]*len(df))).fillna(0)
    df['Total Mileage (Bike + Run)'] = df.get('Cycling Distance (mi)', pd.Series([0]*len(df))).fillna(0) + df.get('Run Dist (mi)', pd.Series([0]*len(df))).fillna(0)
    df['Total KJ'] = df.get('Cycling KJ', pd.Series([0]*len(df))).fillna(0) + df.get('Run KJ', pd.Series([0]*len(df))).fillna(0)
    df['Total TSS (Bike + Run)'] = df.get('Cycling TSS (Est)', pd.Series([0]*len(df))).fillna(0) + df.get('Run TSS (Est)', pd.Series([0]*len(df))).fillna(0)

    # Surplus/Deficit
    calories_burned = df.get('Cycling Calories Burned', pd.Series([0]*len(df))).fillna(0) + df.get('Run Calories Burned', pd.Series([0]*len(df))).fillna(0)
    df['Calories Burned'] = calories_burned
    df['Surplus/Deficit'] = df.get('Calories In', pd.Series([0]*len(df))).fillna(0) - calories_burned

    # Watts/kg
    if 'Avg Watt (Est)' in df.columns and 'Weight (lbs)' in df.columns:
        weight_kg = df['Weight (lbs)'] * 0.453592
        df['Watts/kg'] = df['Avg Watt (Est)'] / weight_kg

    # kcal per Watt-hour
    if 'Calories Burned' in df.columns and 'Cycling Duration (hrs)' in df.columns:
        df['kcal per Watt-hour'] = df['Calories Burned'] / (df['Avg Watt (Est)'] * df['Cycling Duration (hrs)'])

    # Recovery Score: (Sleep × 0.4) + (Mood × 0.3) + (RHR variability × 0.3)
    # For RHR variability, use rolling std of RHR over 7 days
    if 'RHR' in df.columns:
        df['RHR Variability'] = df.set_index('Date')['RHR'].rolling(window=7).std().reset_index(drop=True)
    else:
        df['RHR Variability'] = np.nan
    df['Recovery Score'] = (df.get('Sleep (hrs)', pd.Series([0]*len(df))).fillna(0) * 0.4) + (df.get('Mood (1-10)', pd.Series([0]*len(df))).fillna(0) * 0.3) + (df.get('RHR Variability', pd.Series([0]*len(df))).fillna(0) * 0.3)

    # Rolling Metrics (7-day averages)
    rolling_cols = ['Avg Watt (Est)', 'Total TSS (Bike + Run)', 'Sleep (hrs)', 'Carb Intake/hr', 'Surplus/Deficit', 'Total KJ']
    for col in rolling_cols:
        if col in df.columns:
            # Convert to numeric first
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[f'{col} (7d Avg)'] = df.set_index('Date')[col].rolling(window=7).mean().reset_index(drop=True)
            df[f'{col} (7d Avg)'] = pd.to_numeric(df[f'{col} (7d Avg)'], errors='coerce')

    # Fitness/Fatigue Formulas
    atl, ctl, tsb = calculate_atl_ctl_tsb(df['Total TSS (Bike + Run)'])
    df['ATL (7d EWMA)'] = atl
    df['CTL (42d EWMA)'] = ctl
    df['TSB (EWMA)'] = tsb

    return df
