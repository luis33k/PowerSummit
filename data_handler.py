import pandas as pd
import os

def load_master_log(path: str) -> pd.DataFrame:
    """
    Load the master log Excel file into a pandas DataFrame.
    If the file does not exist, create a default empty DataFrame with all necessary columns.

    Args:
        path (str): Path to the Excel file.

    Returns:
        pd.DataFrame: Loaded and processed DataFrame with sanitized columns and sorted by Date.
    """
    if not os.path.exists(path):
        # Create default DataFrame with all necessary columns, no duplicates
        columns = [
            'Date', 'Activity Type', 'Cycling Duration', 'Cycling Distance', 'Avg Watt', 'Cycling Session Type',
            'Run Duration', 'Run Dist', 'Run RPE', 'Run Session Type', 'Calories In', 'Protein', 'Carbs', 'Fat',
            'Sugar', 'Sodium', 'Sleep', 'Weight', 'RHR', 'Mood', 'Energy', 'Dopamine Cravings', 'Carb Intra Fuel',
            'Carb Intake/hr', 'FTP_used', 'MET'
        ]
        df = pd.DataFrame(columns=columns)
        # Save the empty DataFrame to create the file
        df.to_excel(path, index=False)
    else:
        df = pd.read_excel(path)

    # Sanitize column names: strip spaces, remove parentheses content, make unique
    df.columns = df.columns.str.strip().str.replace(r'\([^)]*\)', '', regex=True).str.strip()
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

    # Parse Date column to datetime and sort
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.sort_values('Date').reset_index(drop=True)

    return df

def save_master_log(df: pd.DataFrame, path: str):
    """
    Save the master log DataFrame to an Excel file.
    Saves only the original input columns, excluding computed metrics to prevent duplicates.

    Args:
        df (pd.DataFrame): DataFrame to save.
        path (str): Path to the Excel file.
    """
    # List of original columns to keep
    original_columns = [
        'Date', 'Activity Type', 'Cycling Duration', 'Cycling Distance', 'Avg Watt', 'Cycling Session Type',
        'Run Duration', 'Run Dist', 'Run RPE', 'Run Session Type', 'Calories In', 'Protein', 'Carbs', 'Fat',
        'Sugar', 'Sodium', 'Sleep', 'Weight', 'RHR', 'Mood', 'Energy', 'Dopamine Cravings', 'Carb Intra Fuel',
        'Carb Intake/hr', 'FTP_used', 'MET'
    ]

    # Filter to keep only original columns
    df_to_save = df[[col for col in original_columns if col in df.columns]]

    df_to_save.to_excel(path, index=False)
