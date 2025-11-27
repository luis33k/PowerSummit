import pandas as pd
import numpy as np
from scipy import stats
from logger import setup_logger

logger = setup_logger()
logger.info("Metrics module initialized")

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
    if_ = avg_watt / ftp_used
    logger.info(f"Calculating IF for cycling: avg_watt={avg_watt}, ftp_used={ftp_used} -> IF={if_}")
    return if_

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
    tss = (duration_min * (rpe ** 2)) / 30
    logger.info(f"Calculating TSS for running: duration_min={duration_min}, rpe={rpe} -> TSS={tss}")
    return tss

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
    Use adjust=False for exponential moving average.

    Args:
        total_tss (pd.Series): Total TSS series.
        span_atl (int): Span for ATL.
        span_ctl (int): Span for CTL.

    Returns:
        tuple: (ATL, CTL, TSB)
    """
    # Ensure total_tss is float
    total_tss = total_tss.astype(float)
    atl = total_tss.ewm(span=span_atl, adjust=False).mean()
    ctl = total_tss.ewm(span=span_ctl, adjust=False).mean()
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
    Now aggregates totals per date for overview and KPIs.

    Args:
        df (pd.DataFrame): Input DataFrame.

    Returns:
        pd.DataFrame: DataFrame with added metrics and aggregated columns.
    """
    df = df.copy()

    # Cycling Calculations (per session)
    if 'Cycling Duration (hrs)' in df.columns and 'Avg Watt (Est)' in df.columns:
        df['Cycling KJ'] = df['Cycling Duration (hrs)'] * df['Avg Watt (Est)'] * 3600 / 1000
        df['Cycling Calories Burned'] = df['Cycling KJ'] * 0.95

    if 'Avg Watt (Est)' in df.columns and 'FTP_used' in df.columns:
        df['Cycling Intensity Factor (IF)'] = df['Avg Watt (Est)'] / df['FTP_used']

    if 'Cycling Duration (hrs)' in df.columns and 'Cycling Intensity Factor (IF)' in df.columns:
        df['Cycling TSS (Est)'] = df['Cycling Duration (hrs)'] * (df['Cycling Intensity Factor (IF)'] ** 2) * 100

    # Use GPX-derived metrics if available
    if 'GPX IF' in df.columns:
        if 'Cycling Intensity Factor (IF)' not in df.columns:
            df['Cycling Intensity Factor (IF)'] = df['GPX IF']
        else:
            df['Cycling Intensity Factor (IF)'] = df['GPX IF'].fillna(df['Cycling Intensity Factor (IF)'])
    if 'GPX TSS' in df.columns:
        if 'Cycling TSS (Est)' not in df.columns:
            df['Cycling TSS (Est)'] = df['GPX TSS']
        else:
            df['Cycling TSS (Est)'] = df['GPX TSS'].fillna(df['Cycling TSS (Est)'])
    if 'GPX KJ' in df.columns:
        if 'Cycling KJ' not in df.columns:
            df['Cycling KJ'] = df['GPX KJ']
        else:
            df['Cycling KJ'] = df['GPX KJ'].fillna(df['Cycling KJ'])

    # Running Calculations (per session)
    if 'Run Duration (hrs)' in df.columns and 'Run RPE' in df.columns:
        duration_min = df['Run Duration (hrs)'] * 60
        df['Run TSS (Est)'] = (duration_min * (df['Run RPE'] ** 2)) / 30

    # Assume MET for running calories; if 'MET' column exists, use it, else assume 10
    if 'Run Duration (hrs)' in df.columns:
        met = df.get('MET', 10)  # Default MET 10
        weight_kg = df.get('Weight (lbs)', 70) * 0.453592  # Convert lbs to kg, default 70kg
        df['Run Calories Burned'] = met * weight_kg * df['Run Duration (hrs)']
        df['Run KJ'] = df['Run Calories Burned'] * 4.184

    # Ensure TSS columns exist before filling
    if 'Cycling TSS (Est)' not in df.columns:
        df['Cycling TSS (Est)'] = 0.0
    if 'Run TSS (Est)' not in df.columns:
        df['Run TSS (Est)'] = 0.0
    # Fill NaN TSS with 0 to ensure sums work and convert to float
    df['Cycling TSS (Est)'] = df['Cycling TSS (Est)'].fillna(0).astype(float)
    df['Run TSS (Est)'] = df['Run TSS (Est)'].fillna(0).astype(float)

    # Aggregate totals per date
    agg_df = df.groupby('Date').agg({
        'Cycling Duration (hrs)': 'sum',
        'Run Duration (hrs)': 'sum',
        'Cycling Distance (mi)': 'sum',
        'Run Dist (mi)': 'sum',
        'Cycling KJ': 'sum',
        'Run KJ': 'sum',
        'Cycling TSS (Est)': 'sum',
        'Run TSS (Est)': 'sum',
        'Cycling Calories Burned': 'sum',
        'Run Calories Burned': 'sum',
        'Calories In': 'first',  # Assume same per date
        'Sleep (hrs)': 'first',
        'RHR': 'first',
        'Weight (lbs)': 'first',
        'Mood (1-10)': 'first',
        'Carb Intake/hr': 'sum',  # Sum intra-session carbs
        'Phase': 'first',
        'Location': 'first'  # Take first location
    }).reset_index()

    # Rename aggregated columns for clarity
    agg_df.rename(columns={
        'Cycling Duration (hrs)': 'Total Cycling Hr',
        'Run Duration (hrs)': 'Total Run Hr',
        'Cycling Distance (mi)': 'Total Cycling Dist',
        'Run Dist (mi)': 'Total Run Dist',
        'Cycling KJ': 'Total Cycling KJ',
        'Run KJ': 'Total Run KJ',
        'Cycling TSS (Est)': 'Total Cycling TSS',
        'Run TSS (Est)': 'Total Run TSS',
        'Cycling Calories Burned': 'Total Cycling Calories',
        'Run Calories Burned': 'Total Run Calories'
    }, inplace=True)

    # Totals per date
    agg_df['Total Training Hr'] = agg_df['Total Cycling Hr'].fillna(0) + agg_df['Total Run Hr'].fillna(0)
    agg_df['Total Mileage (Bike + Run)'] = agg_df['Total Cycling Dist'].fillna(0) + agg_df['Total Run Dist'].fillna(0)
    agg_df['Total KJ'] = agg_df['Total Cycling KJ'].fillna(0) + agg_df['Total Run KJ'].fillna(0)
    agg_df['Total TSS (Bike + Run)'] = agg_df['Total Cycling TSS'].fillna(0) + agg_df['Total Run TSS'].fillna(0)
    agg_df['Calories Burned'] = agg_df['Total Cycling Calories'].fillna(0) + agg_df['Total Run Calories'].fillna(0)
    agg_df['Surplus/Deficit'] = agg_df['Calories In'].fillna(0) - agg_df['Calories Burned']

    # Watts/kg (use average watts per date if available, but since aggregated, skip or compute separately)
    # For simplicity, skip per-date watts/kg as it's per session

    # Recovery Score per date
    if 'RHR' in agg_df.columns:
        agg_df['RHR Variability'] = agg_df.set_index('Date')['RHR'].rolling(window=7).std().reset_index(drop=True)
    else:
        agg_df['RHR Variability'] = np.nan
    agg_df['Recovery Score'] = (agg_df.get('Sleep (hrs)', pd.Series([0]*len(agg_df))).fillna(0) * 0.4) + (agg_df.get('Mood (1-10)', pd.Series([0]*len(agg_df))).fillna(0) * 0.3) + (agg_df.get('RHR Variability', pd.Series([0]*len(agg_df))).fillna(0) * 0.3)

    # Rolling Metrics (7-day averages) on aggregated data
    rolling_cols = ['Total TSS (Bike + Run)', 'Sleep (hrs)', 'Carb Intake/hr', 'Surplus/Deficit', 'Total KJ']
    for col in rolling_cols:
        if col in agg_df.columns:
            agg_df[col] = pd.to_numeric(agg_df[col], errors='coerce')
            agg_df[f'{col} (7d Avg)'] = agg_df.set_index('Date')[col].rolling(window=7).mean().reset_index(drop=True)
            agg_df[f'{col} (7d Avg)'] = pd.to_numeric(agg_df[f'{col} (7d Avg)'], errors='coerce').ffill()

    # Reindex to daily for accurate EWMA and rolling
    agg_df = agg_df.sort_values('Date')
    date_min = agg_df['Date'].min()
    date_max = agg_df['Date'].max()
    date_range = pd.date_range(start=date_min, end=date_max, freq='D')

    # Fitness/Fatigue Formulas on aggregated TSS
    tss_series = agg_df.set_index('Date')['Total TSS (Bike + Run)'].reindex(date_range, fill_value=0)
    atl = tss_series.ewm(span=7, adjust=False).mean()
    ctl = tss_series.ewm(span=42, adjust=False).mean()
    tsb = ctl - atl
    agg_df['ATL (7d EWMA)'] = atl.loc[agg_df['Date']].values
    agg_df['CTL (42d EWMA)'] = ctl.loc[agg_df['Date']].values
    agg_df['TSB (EWMA)'] = tsb.loc[agg_df['Date']].values

    # Rolling Metrics (7-day averages) on aggregated data
    rolling_cols = ['Total TSS (Bike + Run)', 'Sleep (hrs)', 'Carb Intake/hr', 'Surplus/Deficit', 'Total KJ']
    for col in rolling_cols:
        if col in agg_df.columns:
            series = agg_df.set_index('Date')[col].reindex(date_range, fill_value=np.nan)
            agg_df[f'{col} (7d Avg)'] = series.rolling(window=7).mean().loc[agg_df['Date']].values
            agg_df[f'{col} (7d Avg)'] = pd.to_numeric(agg_df[f'{col} (7d Avg)'], errors='coerce').ffill()

    # Recovery Rate based on Phase
    phase_mapping = {'Build': 1.5, 'Peak': 1.5, 'Sustain': 2.0, 'Deload': 3.0}
    agg_df['recovery_rate'] = agg_df.get('Phase', '').map(phase_mapping)

    # Relative TSB Calculation
    agg_df['relative_tsb'] = np.nan
    if not agg_df.empty:
        agg_df.loc[0, 'relative_tsb'] = 0.0  # Initial value
        for i in range(1, len(agg_df)):
            prev_relative_tsb = agg_df.loc[i-1, 'relative_tsb']
            current_tss = agg_df.loc[i, 'Total TSS (Bike + Run)']
            recovery_rate = agg_df.loc[i, 'recovery_rate']
            atl = agg_df.loc[i, 'ATL (7d EWMA)']
            if pd.notna(current_tss) and pd.notna(recovery_rate) and pd.notna(atl):
                agg_df.loc[i, 'relative_tsb'] = prev_relative_tsb + (current_tss * recovery_rate) - (atl / 100)
            else:
                agg_df.loc[i, 'relative_tsb'] = prev_relative_tsb

    # Drop existing aggregated columns from df to avoid duplicates during merge
    aggregated_keys = [col for col in agg_df.columns if col != 'Date']
    cols_to_drop = [col for col in aggregated_keys if col in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Merge aggregated columns back to original df
    df = df.merge(agg_df[['Date'] + aggregated_keys], on='Date', how='left', suffixes=('', '_agg'))

    # Rename _agg columns to final names (though with drop, should not have _agg)
    for key in aggregated_keys:
        if f'{key}_agg' in df.columns:
            df.rename(columns={f'{key}_agg': key}, inplace=True)

    df = df.sort_values('Date').reset_index(drop=True)

    return df
