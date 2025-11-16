import pandas as pd
import numpy as np
import os
from gpx_parser import load_gpx_files

def load_master_log(path: str) -> pd.DataFrame:
    """
    Load the master log Excel file into a pandas DataFrame.
    Reads multiple sheets (Daily, Weekly, Training, TSB, Nutrition, Checkin), merges them by Date into one master DataFrame with all Daily Master Log columns.
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
        'FTP_used', 'FTP_dynamic',
        'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Sodium intra (g)', 'Carb Intake/hr',
        'Cycling Hydration Index', 'Watts/kg', 'kcal per Watt-hour',
        'Total Training Hr', 'Total Mileage (Bike + Run)', 'Total TSS (Bike + Run)', 'Total KJ', 'Calories Burned', 'Surplus/Deficit', 'Recovery Score',
        'Avg Watt (7d Avg)', 'TSS (7d Avg)', 'ATL (7d EWMA)', 'CTL (42d EWMA)', 'TSB (EWMA)', 'KJ (7d avg)', 'Sleep (7d Avg)', 'Carb Intake/hr (7d Avg)', 'Surplus/Deficit (7d Avg)'
    ]

    if not os.path.exists(path):
        # Create default DataFrame with all necessary columns
        df = pd.DataFrame(columns=all_columns)
        # Save the empty DataFrame to create the file with multiple sheets
        with pd.ExcelWriter(path) as writer:
            df.to_excel(writer, sheet_name='Daily', index=False)
            pd.DataFrame(columns=['Date', 'Phase', 'Location', 'Total Training Hours', 'Total Cycling (hrs)', 'Total Cycling Dist (mi)', 'Cycling Avg Speed (mph)', 'Total Running Dist (mi)', 'Total Running (hrs)', 'Total TSS', 'Est Avg Watts', 'Total KJ', 'Total Elevation (ft)', 'Avg RHR (bpm)', 'Avg HR (bpm)', 'Avg Burned Cal', 'Avg Cal', 'Total Burned Cal', 'Total Cal', 'Surplus/Deficit', 'Avg Protein (g)', 'Avg Carbs (g)', 'Avg Sugar (g)', 'Avg Fat (g)', 'Avg Weight', 'Avg Sleep', 'Total Burned BMR + NEAT', 'Notes', 'BMR', 'NEAT']).to_excel(writer, sheet_name='Weekly', index=False)
            pd.DataFrame(columns=['Date', 'Sport', 'Phase Block', 'Cycling Duration (hrs)', 'Avg Watt (Est)', 'RPE', 'Session Type', 'Bike TSS', 'Est. Cal Burn', 'Run (hr)', 'Run RPE', 'Run Type', 'Run TSS', 'Run Cals Burned', 'Total TSS (Bike + Run)', 'Total Cal Burn (Bike + Run)', 'Total Training Hrs', 'Run Distance (mi)', 'Cycling Distance (mi)', 'Intra Fuel Carb (g/h)', 'Sodium intra (g)', 'Position', 'Speed Avg (mph)', 'Elevation (ft)', 'Wind (mph)', 'Temp (F)', 'Humidity', 'HR-to-Speed Efficiency', 'HR Reserve %', 'RHR', 'Avg HR', 'Max HR', 'Z1-Z5 Time (min)', 'Work Cycling KJ', 'Work Run KJ', 'Total KJ', 'Watts_old_v2', 'Watts Adj_old', 'Watts Back up_old', 'Location', 'Notes']).to_excel(writer, sheet_name='Training', index=False)
            pd.DataFrame(columns=['Date', 'FTP Est', 'Avg Watt', '60m Effort Est', 'Cycling TSS', 'Run TSS', 'Total TSS', 'TSB', 'Notes', 'Recovery Rate', 'When to Use', 'Formula Value', 'Location', 'AVG FTP EST']).to_excel(writer, sheet_name='TSB', index=False)
            pd.DataFrame(columns=['Date', 'Total Calories', 'Protein (g)', 'Carbs (g)', 'Fiber (g)', 'Sugar (g)', 'Fat (g)', 'Sodium (mg)', 'Potassium (mg)', 'Weight (lbs)', 'Post Fuel Weight (lbs)', 'Notes']).to_excel(writer, sheet_name='Nutrition', index=False)
            pd.DataFrame(columns=['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes']).to_excel(writer, sheet_name='Checkin', index=False)
    else:
        # Read all sheets
        sheets = pd.read_excel(path, sheet_name=None)
        daily_df = sheets.get('Daily', pd.DataFrame())
        weekly_df = sheets.get('Weekly', pd.DataFrame())
        training_df = sheets.get('Training', pd.DataFrame())
        tsb_df = sheets.get('TSB', pd.DataFrame())
        nutrition_df = sheets.get('Nutrition', pd.DataFrame())
        checkin_df = sheets.get('Checkin', pd.DataFrame())

        # Merge all into daily_df by Date
        df = daily_df
        for merge_df in [weekly_df, training_df, tsb_df, nutrition_df, checkin_df]:
            if not merge_df.empty:
                df = df.merge(merge_df, on='Date', how='outer')

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
    Merge GPX data into the master DataFrame by Date.

    For cycling GPX, map to cycling columns; for running, to run columns.
    If date not present, append new row.

    Args:
        df (pd.DataFrame): Master DataFrame.
        gpx_df (pd.DataFrame): GPX DataFrame.

    Returns:
        pd.DataFrame: Merged DataFrame.
    """
    for _, row in gpx_df.iterrows():
        date = row['Date']
        existing = df['Date'] == date
        if existing.any():
            # Update existing row
            idx = df[existing].index[0]
            if not pd.isna(row.get('GPX Avg Power', np.nan)):
                # Cycling
                df.at[idx, 'Cycling Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
                df.at[idx, 'Cycling Distance (mi)'] = row.get('GPX Distance (mi)', np.nan)
                df.at[idx, 'Cycling Elevation (ft)'] = row.get('GPX Elevation Gain (ft)', np.nan)
                df.at[idx, 'Avg Watt (Est)'] = float(row.get('GPX Avg Power', np.nan))
                df.at[idx, 'Cycling Speed (mph)'] = row.get('GPX Avg Speed (mph)', np.nan)
                df.at[idx, 'Sport'] = 'Cycling'
            else:
                # Running
                df.at[idx, 'Run Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
                df.at[idx, 'Run Dist (mi)'] = row.get('GPX Distance (mi)', np.nan)
                df.at[idx, 'Sport'] = 'Running'
        else:
            # Append new row
            new_row = {'Date': date}
            if not pd.isna(row.get('GPX Avg Power', np.nan)):
                # Cycling
                new_row['Cycling Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
                new_row['Cycling Distance (mi)'] = row.get('GPX Distance (mi)', np.nan)
                new_row['Cycling Elevation (ft)'] = row.get('GPX Elevation Gain (ft)', np.nan)
                new_row['Avg Watt (Est)'] = float(row.get('GPX Avg Power', np.nan))
                new_row['Cycling Speed (mph)'] = row.get('GPX Avg Speed (mph)', np.nan)
                new_row['Sport'] = 'Cycling'
            else:
                # Running
                new_row['Run Duration (hrs)'] = row.get('GPX Duration (hrs)', np.nan)
                new_row['Run Dist (mi)'] = row.get('GPX Distance (mi)', np.nan)
                new_row['Sport'] = 'Running'
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    return df

def save_master_log(df: pd.DataFrame, path: str):
    """
    Save the master log DataFrame to an Excel file.
    Saves only the original input columns to the Daily sheet, excluding computed metrics to prevent duplicates.

    Args:
        df (pd.DataFrame): DataFrame to save.
        path (str): Path to the Excel file.
    """
    # List of original input columns (non-computed)
    original_columns = [
        'Date', 'Phase', 'Sport', 'Location', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes',
        'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)',
        'Run Duration (hrs)', 'Run Dist (mi)', 'Run Session Type', 'Run RPE',
        'FTP_used', 'FTP_dynamic',
        'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Sodium intra (g)', 'Carb Intake/hr',
        'Cycling Hydration Index'
    ]

    # Filter to keep only original columns
    df_to_save = df[[col for col in original_columns if col in df.columns]]

    # Save to Daily sheet, and create other sheets if needed (empty for now)
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df_to_save.to_excel(writer, sheet_name='Daily', index=False)
        # For other sheets, save empty DataFrames with their columns
        pd.DataFrame(columns=['Date', 'Phase', 'Location', 'Total Training Hours', 'Total Cycling (hrs)', 'Total Cycling Dist (mi)', 'Cycling Avg Speed (mph)', 'Total Running Dist (mi)', 'Total Running (hrs)', 'Total TSS', 'Est Avg Watts', 'Total KJ', 'Total Elevation (ft)', 'Avg RHR (bpm)', 'Avg HR (bpm)', 'Avg Burned Cal', 'Avg Cal', 'Total Burned Cal', 'Total Cal', 'Surplus/Deficit', 'Avg Protein (g)', 'Avg Carbs (g)', 'Avg Sugar (g)', 'Avg Fat (g)', 'Avg Weight', 'Avg Sleep', 'Total Burned BMR + NEAT', 'Notes', 'BMR', 'NEAT']).to_excel(writer, sheet_name='Weekly', index=False)
        pd.DataFrame(columns=['Date', 'Sport', 'Phase Block', 'Cycling Duration (hrs)', 'Avg Watt (Est)', 'RPE', 'Session Type', 'Bike TSS', 'Est. Cal Burn', 'Run (hr)', 'Run RPE', 'Run Type', 'Run TSS', 'Run Cals Burned', 'Total TSS (Bike + Run)', 'Total Cal Burn (Bike + Run)', 'Total Training Hrs', 'Run Distance (mi)', 'Cycling Distance (mi)', 'Intra Fuel Carb (g/h)', 'Sodium intra (g)', 'Position', 'Speed Avg (mph)', 'Elevation (ft)', 'Wind (mph)', 'Temp (F)', 'Humidity', 'HR-to-Speed Efficiency', 'HR Reserve %', 'RHR', 'Avg HR', 'Max HR', 'Z1-Z5 Time (min)', 'Work Cycling KJ', 'Work Run KJ', 'Total KJ', 'Watts_old_v2', 'Watts Adj_old', 'Watts Back up_old', 'Location', 'Notes']).to_excel(writer, sheet_name='Training', index=False)
        pd.DataFrame(columns=['Date', 'FTP Est', 'Avg Watt', '60m Effort Est', 'Cycling TSS', 'Run TSS', 'Total TSS', 'TSB', 'Notes', 'Recovery Rate', 'When to Use', 'Formula Value', 'Location', 'AVG FTP EST']).to_excel(writer, sheet_name='TSB', index=False)
        pd.DataFrame(columns=['Date', 'Total Calories', 'Protein (g)', 'Carbs (g)', 'Fiber (g)', 'Sugar (g)', 'Fat (g)', 'Sodium (mg)', 'Potassium (mg)', 'Weight (lbs)', 'Post Fuel Weight (lbs)', 'Notes']).to_excel(writer, sheet_name='Nutrition', index=False)
        pd.DataFrame(columns=['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes']).to_excel(writer, sheet_name='Checkin', index=False)
