# Training Dashboard

A Streamlit web app for analyzing training data in a TrainingPeaks-style dashboard.

## Features

- Load master Excel file with training logs
- Calculate cycling and running TSS, IF, ATL, CTL, TSB
- Visualize trends with Plotly charts
- Modular code structure

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the app:
   ```bash
   streamlit run app.py
   ```

## File Structure

- `app.py`: Main Streamlit application
- `data_handler.py`: Data loading and preprocessing
- `metrics.py`: Calculation of training metrics
- `plots.py`: Plotly chart functions
- `utils.py`: Utility functions
- `sample_data/master_log.xlsx`: Sample data file

## Sample Data

The sample `master_log.xlsx` contains 14 rows of mixed cycling and running data with columns like Date, Activity Type, Duration, Avg Watt, FTP Used, RPE, Sleep, Carbs, etc.
