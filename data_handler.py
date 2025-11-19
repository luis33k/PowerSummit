import pandas as pd
import numpy as np
import os
from logger import setup_logger

logger = setup_logger()
logger.info("Data handler module initialized")
from gpx_parser import load_gpx_files

def load_master_log(path: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load the master log Excel file into separate DataFrames for training, nutrition, and checkin.
    Reads multiple sheets (Training, Nutrition, Checkin).
    If the file does not exist, create default empty DataFrames.

    Args:
        path (str): Path to the Excel file.

    Returns:
        tuple: (training_df, nutrition_df, checkin_df) - Separate DataFrames for each log type.
    """
    training_cols = ['Date', 'Phase', 'Sport', 'Location', 'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)', 'FTP_used', 'Carb Intake/hr', 'Sodium intra (g)', 'Cycling Hydration Index', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'Run Session Type', 'Cycling TSS (Est)', 'Run TSS (Est)', 'Cycling Intensity Factor (IF)', 'Run Intensity Factor (IF)', 'Total Training Hr', 'Total Mileage (Bike + Run)', 'Total TSS (Bike + Run)', 'Total KJ', 'Calories Burned']
    nutrition_cols = ['Date', 'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)', 'Surplus/Deficit']
    checkin_cols = ['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes', 'TSS (EWMA)', 'TSB (EWMA)', 'ATL (EWMA)', 'CTL (EWMA)']

    if not os.path.exists(path):
        logger.info(f"Master log file {path} does not exist. Creating default empty DataFrames.")
        # Create default empty DataFrames
        training_df = pd.DataFrame(columns=training_cols)
        nutrition_df = pd.DataFrame(columns=nutrition_cols)
        checkin_df = pd.DataFrame(columns=checkin_cols)
        # Save the empty DataFrames to create the file with multiple sheets
        with pd.ExcelWriter(path) as writer:
            training_df.to_excel(writer, sheet_name='Training', index=False)
            nutrition_df.to_excel(writer, sheet_name='Nutrition', index=False)
            checkin_df.to_excel(writer, sheet_name='Checkin', index=False)
        logger.info(f"Created master log file {path} with empty sheets.")
    else:
        logger.info(f"Loading master log from {path}.")
        try:
            sheets = pd.read_excel(path, sheet_name=None)
        except Exception as e:
            logger.warning(f"Failed to load master log from {path}: {e}. Recreating empty file.")
            training_df = pd.DataFrame(columns=training_cols)
            nutrition_df = pd.DataFrame(columns=nutrition_cols)
            checkin_df = pd.DataFrame(columns=checkin_cols)
            with pd.ExcelWriter(path) as writer:
                training_df.to_excel(writer, sheet_name='Training', index=False)
                nutrition_df.to_excel(writer, sheet_name='Nutrition', index=False)
                checkin_df.to_excel(writer, sheet_name='Checkin', index=False)
            logger.info(f"Recreated master log file {path} with empty sheets.")
            sheets = {}
        if 'Training' in sheets:
            training_df = sheets.get('Training', pd.DataFrame())
        else:
            # Backward compatibility: combine Cycling and Running sheets
            cycling_df = sheets.get('Cycling', pd.DataFrame())
            running_df = sheets.get('Running', pd.DataFrame())
            training_df = pd.concat([cycling_df, running_df], ignore_index=True)
        nutrition_df = sheets.get('Nutrition', pd.DataFrame())
        checkin_df = sheets.get('Checkin', pd.DataFrame())
        logger.info(f"Loaded sheets: Training ({len(training_df)} rows), Nutrition ({len(nutrition_df)} rows), Checkin ({len(checkin_df)} rows).")

        # Ensure all expected columns are present
        training_df = training_df.reindex(columns=training_cols, fill_value=np.nan)
        nutrition_df = nutrition_df.reindex(columns=nutrition_cols, fill_value=np.nan)
        checkin_df = checkin_df.reindex(columns=checkin_cols, fill_value=np.nan)

    # Sanitize and convert for each df
    for df_name, df in [('Training', training_df), ('Nutrition', nutrition_df), ('Checkin', checkin_df)]:
        df.columns = df.columns.astype(str).str.strip()
        df = df.loc[:, ~df.columns.duplicated()]
        numeric_cols = {
            'Training': ['Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'FTP_used', 'Carb Intake/hr', 'Sodium intra (g)', 'Cycling Hydration Index', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)', 'Cycling TSS (Est)', 'Run TSS (Est)', 'Cycling Intensity Factor (IF)', 'Run Intensity Factor (IF)', 'Total Training Hr', 'Total Mileage (Bike + Run)', 'Total TSS (Bike + Run)', 'Total KJ', 'Calories Burned'],
            'Nutrition': ['Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)', 'Surplus/Deficit'],
            'Checkin': ['Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'TSS (EWMA)', 'TSB (EWMA)', 'ATL (EWMA)', 'CTL (EWMA)']
        }
        for col in numeric_cols[df_name]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('float32')
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date').reset_index(drop=True)

    logger.info(f"Loaded master log with Training: {len(training_df)} rows, Nutrition: {len(nutrition_df)} rows, Checkin: {len(checkin_df)} rows.")
    return training_df, nutrition_df, checkin_df

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
    merged_count = 0
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
            merged_count += 1
    logger.info(f"Successfully merged {merged_count} new GPX rows, skipped {len(gpx_df) - merged_count} duplicates")
    return df

def save_master_log(df: pd.DataFrame, path: str):
    """
    Save the master log DataFrame to an Excel file with separate sheets for Training, Nutrition, Checkin.

    Args:
        df (pd.DataFrame): Combined DataFrame to split and save.
        path (str): Path to the Excel file.
    """
    # Split df into separate sheets
    # Training: rows with Sport or cycling/running columns filled
    training_cols = ['Date', 'Phase', 'Sport', 'Location', 'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Session Type', 'Position', 'Wind (mph)', 'Temp (°F)', 'Humidity (%)', 'FTP_used', 'Carb Intake/hr', 'Sodium intra (g)', 'Cycling Hydration Index', 'Max HR', 'Avg HR', 'Z1 Time (min)', 'Z2 Time (min)', 'Z3 Time (min)', 'Z4 Time (min)', 'Z5 Time (min)', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'Run Session Type', 'Cycling TSS (Est)', 'Run TSS (Est)', 'Cycling Intensity Factor (IF)', 'Run Intensity Factor (IF)', 'Total Training Hr', 'Total Mileage (Bike + Run)', 'Total TSS (Bike + Run)', 'Total KJ', 'Calories Burned']
    training_mask = df['Sport'].notna() | df[['Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Run Duration (hrs)', 'Run Dist (mi)']].notna().any(axis=1)
    training_df = df[training_mask][training_cols].dropna(how='all')

    # Nutrition: rows with nutrition columns filled
    nutrition_cols = ['Date', 'Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)']
    nutrition_df = df[nutrition_cols].dropna(how='all')

    # Checkin: rows with checkin columns filled
    checkin_cols = ['Date', 'Wake Time', 'Sleep (hrs)', 'RHR', 'Weight (lbs)', 'Mood (1-10)', 'Energy (1-10)', 'Hunger (1-10)', 'Dopamine Cravings (1-10)', 'Notes']
    checkin_df = df[checkin_cols].dropna(how='all')

    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        training_df.to_excel(writer, sheet_name='Training', index=False)
        nutrition_df.to_excel(writer, sheet_name='Nutrition', index=False)
        checkin_df.to_excel(writer, sheet_name='Checkin', index=False)
