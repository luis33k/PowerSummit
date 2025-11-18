import pandas as pd
import numpy as np
import os
from logger import setup_logger

logger = setup_logger()
from gpx_parser import load_gpx_files

def load_master_log(path: str) -> pd.DataFrame:
    """
    Load the master log Excel file into a pandas DataFrame.
    Reads multiple sheets (Cycling, Running, Nutrition, Checkin), merges them by Date into one master DataFrame with all Daily Master Log columns.
    If the file does not exist, create a default empty DataFrame with all necessary columns.

    Args:
        path (str): Path to the Excel file.

    Returns:
        pd.DataFrame: Loaded and processed DataFrame with sanitized columns and sorted by Date.
    """
    # All required columns for Daily Master Log
    all_columns = [
        'Date', 'Phase', 'Sport', 'Location', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes',
        'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling TSS (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)',
        'Run Duration (hrs)', 'Run Dist (mi)', 'Run TSS (Est)', 'Run Session Type', 'Run RPE',
        'FTP_used',
        'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Sodium intra (g)', 'Carb Intake/hr',
        'Cycling Hydration Index', 'Watts/kg', 'kcal per Watt-hour',
        'Total Training Hr', 'Total Mileage (Bike + Run)', 'Total TSS (Bike + Run)', 'Total KJ', 'Calories Burned', 'Surplus/Deficit', 'Recovery Score',
        'Avg Watt (7d Avg)', 'TSS (7d Avg)', 'ATL (7d EWMA)', 'CTL (42d EWMA)', 'TSB (EWMA)', 'KJ (7d avg)', 'Sleep (7d Avg)', 'Carb Intake/hr (7d Avg)', 'Surplus/Deficit (7d Avg)',
        'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)'
    ]

    if not os.path.exists(path):
        # Create default DataFrame with all necessary columns
        df = pd.DataFrame(columns=all_columns)
        # Save the empty DataFrame to create the file with multiple sheets
        with pd.ExcelWriter(path) as writer:
            # Cycling sheet
            pd.DataFrame(columns=['Date', 'Phase', 'Sport', 'Location', 'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)', 'FTP_used', 'Carb Intake/hr', 'Sodium intra (g)', 'Cycling Hydration Index', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)']).to_excel(writer, sheet_name='Cycling', index=False)
            # Running sheet
            pd.DataFrame(columns=['Date', 'Phase', 'Sport', 'Location', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'Run Session Type', 'Carb Intake/hr', 'Sodium intra (g)']).to_excel(writer, sheet_name='Running', index=False)
            # Nutrition sheet
            pd.DataFrame(columns=['Date', 'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)']).to_excel(writer, sheet_name='Nutrition', index=False)
            # Checkin sheet
            pd.DataFrame(columns=['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes']).to_excel(writer, sheet_name='Checkin', index=False)
    else:
        # Read all sheets
        sheets = pd.read_excel(path, sheet_name=None)
        cycling_df = sheets.get('Cycling', pd.DataFrame())
        running_df = sheets.get('Running', pd.DataFrame())
        nutrition_df = sheets.get('Nutrition', pd.DataFrame())
        checkin_df = sheets.get('Checkin', pd.DataFrame())

        # Merge all into one df by Date
        df = pd.DataFrame()
        for merge_df in [cycling_df, running_df, nutrition_df, checkin_df]:
            if not merge_df.empty:
                if df.empty:
                    df = merge_df
                else:
                    df = df.merge(merge_df, on='Date', how='outer', suffixes=('', '_y'))

        # Combine duplicate columns from merge (e.g., Weight (lbs) and Weight (lbs)_y)
        cols_to_drop = []
        for col in df.columns:
            if col.endswith('_y'):
                base = col[:-2]
                if base in df.columns:
                    # Combine: prefer the original if not na, else the _y
                    df[base] = df[base].combine_first(df[col])
                    cols_to_drop.append(col)
        df.drop(cols_to_drop, axis=1, inplace=True)

    # Sanitize column names: strip spaces, make unique
    df.columns = df.columns.astype(str).str.strip()
    # Make column names unique by appending suffix if duplicates
    seen = set()
    new_cols = []
    for col in df.columns:
        if col in seen:
            suffix = 1
            new_col = f"{col}_{suffix}"
            while new_col in seen:
                suffix += 1
                new_col = f"{col}_{suffix}"
            new_cols.append(new_col)
            seen.add(new_col)
        else:
            new_cols.append(col)
            seen.add(col)
    df.columns = new_cols

    # Drop duplicate columns, keeping only the first occurrence
    df = df.loc[:, ~df.columns.duplicated()]

    # Convert numeric columns to appropriate types
    numeric_cols = ['Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling TSS (Est)', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)',
                    'Run Duration (hrs)', 'Run Dist (mi)', 'Run TSS (Est)', 'Run RPE', 'FTP_used', 'FTP_dynamic', 'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Sodium intra (g)', 'Carb Intake/hr', 'Cycling Hydration Index',
                    'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Ensure all required columns are present, fill missing with NaN
    for col in all_columns:
        if col not in df.columns:
            df[col] = pd.NA

    # Parse Date column to datetime and sort
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)

    return df

def merge_gpx_data(df: pd.DataFrame, gpx_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge GPX data into the master DataFrame by appending new rows for each session.

    For cycling GPX, map to cycling columns; for running, to run columns.
    Always append new rows, but check for exact duplicates based on Date, Sport, Duration, and Distance to avoid duplicates.

    Args:
        df (pd.DataFrame): Master DataFrame.
        gpx_df (pd.DataFrame): GPX DataFrame.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    logger.info(f"Merging {len(gpx_df)} GPX rows into master DataFrame")
    for _, row in gpx_df.iterrows():
        new_row = {'Date': row['Date']}
        if not pd.isna(row.get('GPX Avg Power', np.nan)):
            # Cycling
            new_row['Cycling Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
            new_row['Cycling Distance (mi)'] = row.get('GPX Distance (mi)', np.nan)
            new_row['Cycling Elevation (ft)'] = row.get('GPX Elevation Gain (ft)', np.nan)
            new_row['Avg Watt (Est)'] = float(row.get('GPX Avg Power', np.nan))
            new_row['Cycling Speed (mph)'] = row.get('GPX Avg Speed (mph)', np.nan)
            new_row['Sport'] = 'Cycling'
            new_row['Max HR'] = row.get('GPX Max HR', np.nan)
            new_row['Avg HR'] = row.get('GPX Avg HR', np.nan)
            new_row['Z1 Time (min)'] = row.get('GPX Z1 Time (min)', np.nan)
            new_row['Z2 Time (min)'] = row.get('GPX Z2 Time (min)', np.nan)
            new_row['Z3 Time (min)'] = row.get('GPX Z3 Time (min)', np.nan)
            new_row['Z4 Time (min)'] = row.get('GPX Z4 Time (min)', np.nan)
            new_row['Z5 Time (min)'] = row.get('GPX Z5 Time (min)', np.nan)
            # Check for duplicate: same Date, Sport, Duration, Distance
            duplicate_mask = (
                (df['Date'] == new_row['Date']) &
                (df['Sport'] == new_row['Sport']) &
                (df['Cycling Duration (hrs)'] == new_row['Cycling Duration (hrs)']) &
                (df['Cycling Distance (mi)'] == new_row['Cycling Distance (mi)'])
            )
        else:
            # Running
            new_row['Run Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
            new_row['Run Dist (mi)'] = row.get('GPX Distance (mi)', np.nan)
            new_row['Sport'] = 'Running'
            new_row['Max HR'] = row.get('GPX Max HR', np.nan)
            new_row['Avg HR'] = row.get('GPX Avg HR', np.nan)
            new_row['Z1 Time (min)'] = row.get('GPX Z1 Time (min)', np.nan)
            new_row['Z2 Time (min)'] = row.get('GPX Z2 Time (min)', np.nan)
            new_row['Z3 Time (min)'] = row.get('GPX Z3 Time (min)', np.nan)
            new_row['Z4 Time (min)'] = row.get('GPX Z4 Time (min)', np.nan)
            new_row['Z5 Time (min)'] = row.get('GPX Z5 Time (min)', np.nan)
            # Check for duplicate: same Date, Sport, Duration, Distance
            duplicate_mask = (
                (df['Date'] == new_row['Date']) &
                (df['Sport'] == new_row['Sport']) &
                (df['Run Duration (hrs)'] == new_row['Run Duration (hrs)']) &
                (df['Run Dist (mi)'] == new_row['Run Dist (mi)'])
            )

        if not duplicate_mask.any():
            # Append new row
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

def save_master_log(df: pd.DataFrame, path: str):
    """
    Save the master log DataFrame to an Excel file.
    Saves data to separate sheets: Cycling, Running, Nutrition, Checkin.

    Args:
        df (pd.DataFrame): DataFrame to save.
        path (str): Path to the Excel file.
    """
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        # Cycling sheet: filter rows where Sport is Cycling or cycling columns are filled
        cycling_cols = ['Date', 'Phase', 'Sport', 'Location', 'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)', 'FTP_used', 'Carb Intake/hr', 'Sodium intra (g)', 'Cycling Hydration Index', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)']
        cycling_df = df[df['Sport'].str.lower().isin(['cycling', 'bike']) | df['Cycling Duration (hrs)'].notna()]
        cycling_df = cycling_df[[col for col in cycling_cols if col in cycling_df.columns]].dropna(how='all')
        cycling_df.to_excel(writer, sheet_name='Cycling', index=False)

        # Running sheet: filter rows where Sport is Running or running columns are filled
        running_cols = ['Date', 'Phase', 'Sport', 'Location', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'Run Session Type', 'Carb Intake/hr', 'Sodium intra (g)', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)']
        running_df = df[df['Sport'].str.lower().isin(['running', 'run']) | (df.get('Run Duration (hrs)').notna() if 'Run Duration (hrs)' in df.columns else False)]
        running_df = running_df[[col for col in running_cols if col in running_df.columns]].dropna(how='all')
        running_df.to_excel(writer, sheet_name='Running', index=False)

        # Nutrition sheet: filter rows with nutrition data
        nutrition_cols = ['Date', 'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)']
        nutrition_df = df[[col for col in nutrition_cols if col in df.columns]].dropna(how='all')
        nutrition_df.to_excel(writer, sheet_name='Nutrition', index=False)

        # Checkin sheet: filter rows with checkin data
        checkin_cols = ['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes']
        checkin_df = df[[col for col in checkin_cols if col in df.columns]].dropna(how='all')
        checkin_df.to_excel(writer, sheet_name='Checkin', index=False)
