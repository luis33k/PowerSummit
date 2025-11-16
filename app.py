import streamlit as st
import pandas as pd
from data_handler import load_master_log, merge_gpx_data
from metrics import compute_all_metrics
from plots import (
    plot_tss_tsb_over_time, plot_weekly_tss, plot_speed_vs_hr,
    plot_small_multiples_sleep_carbs_salt, plot_avg_watt_over_time,
    plot_carb_hr_vs_tss, plot_sleep_trend, plot_rhr_trend
)
from utils import save_processed_data, get_top_kpis, compute_recovery_score
from gpx_parser import load_gpx_files
import os

st.set_page_config(page_title="Training Dashboard", layout="wide")

# Sidebar
st.sidebar.title("Controls")
uploaded_gpx = st.sidebar.file_uploader("Upload GPX files", type="gpx", accept_multiple_files=True)
ftp_input = st.sidebar.number_input("FTP (for GPX calculations)", min_value=0, value=200)
gpx_sport = st.sidebar.selectbox("GPX Sport Detection", ["Auto", "Cycling", "Running"], help="Auto detects from data/track name, or override to Cycling/Running")
date_range = st.sidebar.date_input("Date Range", [])
show_series = st.sidebar.multiselect("Show Series", ["TSS", "TSB", "Sleep", "Carbs"], default=["TSS", "TSB"])

# Load data
default_path = "sample_data/master_log.xlsx"
os.makedirs("sample_data", exist_ok=True)
df = load_master_log(default_path)

# Process GPX files
if uploaded_gpx:
    current_files = [f.name for f in uploaded_gpx]
    if current_files != st.session_state.get('uploaded_files', []):
        gpx_contents = []
        for file in uploaded_gpx:
            try:
                content = file.read().decode('utf-8')
                gpx_contents.append(content)
            except UnicodeDecodeError:
                st.sidebar.error(f"Failed to decode {file.name}. Ensure it's a valid GPX file.")
                continue
        st.session_state['gpx_contents'] = gpx_contents
        st.session_state['uploaded_files'] = current_files
    gpx_contents = st.session_state.get('gpx_contents', [])
    if gpx_contents:
        sport_override = gpx_sport if gpx_sport != "Auto" else None
        gpx_df = load_gpx_files(gpx_contents, ftp=ftp_input, sport_override=sport_override)
        df = merge_gpx_data(df, gpx_df)
        # Save updated df to Excel
        from data_handler import save_master_log
        save_master_log(df, default_path)
        st.sidebar.success(f"Processed {len(gpx_contents)} GPX file(s) and saved to master log")

# Compute metrics
df = compute_all_metrics(df)

# Save processed data
os.makedirs("outputs", exist_ok=True)
save_processed_data(df, "outputs/processed_master.csv")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["Overview", "Cycling", "Running", "Nutrition", "Recovery", "Weekly Summary", "Data Entry", "GPX Phraser", "Data Editor"])

with tab1:
    st.header("Overview")
    kpis = get_top_kpis(df)
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("7d TSS", f"{kpis['7d TSS']:.1f}")
    col2.metric("CTL", f"{kpis['CTL']:.1f}")
    col3.metric("ATL", f"{kpis['ATL']:.1f}")
    col4.metric("Latest TSB", f"{kpis['Latest TSB']:.1f}")
    col5.metric("Avg Sleep 7d", f"{kpis['Avg Sleep 7d']:.1f}")

    # Small graphs
    st.subheader("TSS & TSB Over Time")
    fig1 = plot_tss_tsb_over_time(df)
    st.plotly_chart(fig1, width='stretch')

    st.subheader("Weekly TSS")
    fig2 = plot_weekly_tss(df)
    st.plotly_chart(fig2, width='stretch')

with tab2:
    st.header("Cycling")
    sport = df.get('Sport', pd.Series([''] * len(df))).astype(str)
    cycling_df = df[sport.str.lower().isin(['cycling', 'bike'])]
    cols = ['Date', 'Cycling Duration (hrs)', 'Cycling Distance (mi)', 'Cycling Speed (mph)', 'Cycling Elevation (ft)', 'Avg Watt (Est)', 'Cycling Intensity Factor (IF)', 'Cycling TSS (Est)', 'Cycling Session Type']
    cols = [col for col in cols if col in cycling_df.columns]
    st.dataframe(cycling_df[cols])

    # Filter by session type if column exists
    if 'Cycling Session Type' in cycling_df.columns:
        session_types = st.multiselect("Filter Session Type", cycling_df['Cycling Session Type'].unique())
        if session_types:
            cycling_df = cycling_df[cycling_df['Cycling Session Type'].isin(session_types)]

    st.subheader("Avg Watt Over Time")
    fig = plot_avg_watt_over_time(cycling_df)
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("Running")
    sport = df.get('Sport', pd.Series([''] * len(df))).astype(str)
    running_df = df[sport.str.lower().isin(['running', 'run'])]
    cols = ['Date', 'Run Duration (hrs)', 'Run Dist (mi)', 'Run RPE', 'Run TSS (Est)', 'Run Session Type']
    cols = [col for col in cols if col in running_df.columns]

    # RPE filter
    if 'Run RPE' in running_df.columns:
        rpe_range = st.slider("RPE Range", min_value=1, max_value=10, value=(1,10))
        running_df = running_df[(running_df['Run RPE'] >= rpe_range[0]) & (running_df['Run RPE'] <= rpe_range[1])]

    st.dataframe(running_df[cols])

with tab4:
    st.header("Nutrition")
    view_type = st.radio("View Type", ["Daily", "Weekly"], horizontal=True)

    if view_type == "Daily":
        selected_date = st.date_input("Select Date", value=pd.to_datetime('today'))
        filtered_df = df[df['Date'] == pd.to_datetime(selected_date)]
        if not filtered_df.empty:
            # Aggregate nutrition for the day (sum if multiple entries, but typically one)
            nutrition_agg = filtered_df[['Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)']].sum()
            st.subheader(f"Daily Summary for {selected_date.strftime('%Y-%m-%d')}")
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            col1.metric("Calories", f"{nutrition_agg.get('Calories In', 0):.0f}" if pd.notna(nutrition_agg.get('Calories In')) else 'N/A')
            col2.metric("Protein", f"{nutrition_agg.get('Protein (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Protein (g)')) else 'N/A')
            col3.metric("Carbs", f"{nutrition_agg.get('Carbs (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Carbs (g)')) else 'N/A')
            col4.metric("Fat", f"{nutrition_agg.get('Fat (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Fat (g)')) else 'N/A')
            col5.metric("Sodium", f"{nutrition_agg.get('Sodium (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Sodium (g)')) else 'N/A')
            col6.metric("Potassium", f"{nutrition_agg.get('Potassium (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Potassium (g)')) else 'N/A')
            col7.metric("Weight", f"{nutrition_agg.get('Weight (lbs)', 0):.1f} lbs" if pd.notna(nutrition_agg.get('Weight (lbs)')) else 'N/A')
        else:
            st.write("No data for selected date.")

    else:  # Weekly
        selected_week = st.date_input("Select Week Starting", value=pd.to_datetime('today') - pd.Timedelta(days=pd.to_datetime('today').weekday()))
        week_start = pd.to_datetime(selected_week)
        week_end = week_start + pd.Timedelta(days=6)
        filtered_df = df[(df['Date'] >= week_start) & (df['Date'] <= week_end)]
        if not filtered_df.empty:
            # Aggregate nutrition for the week (average)
            nutrition_agg = filtered_df[['Calories In', 'Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sodium (g)', 'Potassium (g)', 'Weight (lbs)']].mean()
            st.subheader(f"Weekly Average for {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}")
            col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
            col1.metric("Calories", f"{nutrition_agg.get('Calories In', 0):.0f}" if pd.notna(nutrition_agg.get('Calories In')) else 'N/A')
            col2.metric("Protein", f"{nutrition_agg.get('Protein (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Protein (g)')) else 'N/A')
            col3.metric("Carbs", f"{nutrition_agg.get('Carbs (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Carbs (g)')) else 'N/A')
            col4.metric("Fat", f"{nutrition_agg.get('Fat (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Fat (g)')) else 'N/A')
            col5.metric("Sodium", f"{nutrition_agg.get('Sodium (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Sodium (g)')) else 'N/A')
            col6.metric("Potassium", f"{nutrition_agg.get('Potassium (g)', 0):.1f}g" if pd.notna(nutrition_agg.get('Potassium (g)')) else 'N/A')
            col7.metric("Weight", f"{nutrition_agg.get('Weight (lbs)', 0):.1f} lbs" if pd.notna(nutrition_agg.get('Weight (lbs)')) else 'N/A')
        else:
            st.write("No data for selected week.")

with tab5:
    st.header("Recovery")
    st.subheader("Sleep Trend")
    fig1 = plot_sleep_trend(df)
    st.plotly_chart(fig1, width='stretch')

    st.subheader("RHR Trend")
    fig2 = plot_rhr_trend(df)
    st.plotly_chart(fig2, width='stretch')

    # Recovery Score
    if 'TSB (EWMA)' in df.columns:
        df['Recovery Score'] = df.apply(lambda row: compute_recovery_score(row['Sleep (hrs)'], row['TSB (EWMA)']), axis=1)
        st.subheader("Recovery Score Over Time")
        st.line_chart(df.set_index('Date')['Recovery Score'])

with tab6:
    st.header("Weekly Summary")
    # Resample to weekly using aggregated columns
    weekly_df = df.set_index('Date').resample('W').agg({
        'Total Training Hr': 'sum',
        'Cycling Duration (hrs)': 'sum',
        'Cycling Distance (mi)': 'sum',
        'Cycling Speed (mph)': lambda x: x.mean(),
        'Run Dist (mi)': 'sum',
        'Run Duration (hrs)': 'sum',
        'Total TSS (Bike + Run)': 'sum',
        'Avg Watt (Est)': 'mean',
        'Total KJ': 'sum',
        'Cycling Elevation (ft)': 'sum',
        'RHR': 'mean',
        'Calories Burned': 'sum',
        'Calories In': 'sum',
        'Surplus/Deficit': 'sum',
        'Protein (g)': 'mean',
        'Carbs (g)': 'mean',
        'Sugar (g)': 'mean',
        'Fat (g)': 'mean',
        'Weight (lbs)': 'mean',
        'Sleep (hrs)': 'mean'
    }).reset_index()
    weekly_df['Date/Week'] = weekly_df['Date']
    st.dataframe(weekly_df)

with tab7:
    st.header("Data Entry")
    subtab1, subtab2, subtab3 = st.tabs(["Log Exercise", "Log Nutrition", "Log Daily Check In"])

    with subtab1:
        st.subheader("Log Exercise")
        activity_type = st.radio("Activity Type", ["Cycling", "Running"])
        date = st.date_input("Date")
        phase = st.selectbox("Phase", ["Build", "Peak", "Sustain", "Deload"])
        location = st.text_input("Location")
        if activity_type == "Cycling":
            duration = st.number_input("Duration (hrs)", min_value=0.0, step=0.1, key="cycling_duration")
            distance = st.number_input("Distance (mi)", min_value=0.0, step=0.1, key="cycling_distance")
            speed = st.number_input("Speed (mph)", min_value=0.0, step=0.1, key="cycling_speed")
            elevation = st.number_input("Elevation (ft)", min_value=0.0, step=0.1, key="cycling_elevation")
            avg_watt = st.number_input("Avg Watt (Est)", min_value=0, step=1, key="cycling_avg_watt")
            max_hr = st.number_input("Max HR", min_value=0, step=1, key="cycling_max_hr")
            avg_hr = st.number_input("Avg HR", min_value=0, step=1, key="cycling_avg_hr")
            z1_time = st.number_input("Z1 Time (min)", min_value=0.0, step=0.1, key="cycling_z1_time")
            z2_time = st.number_input("Z2 Time (min)", min_value=0.0, step=0.1, key="cycling_z2_time")
            z3_time = st.number_input("Z3 Time (min)", min_value=0.0, step=0.1, key="cycling_z3_time")
            z4_time = st.number_input("Z4 Time (min)", min_value=0.0, step=0.1, key="cycling_z4_time")
            z5_time = st.number_input("Z5 Time (min)", min_value=0.0, step=0.1, key="cycling_z5_time")
            session_type = st.selectbox("Session Type", ["Recovery", "Zone 1", "Zone 2", "Zone 3", "Tempo", "Threshold", "VO2 Max", "Sweet Spot", "Intervals"])
            position = st.text_input("Position")
            wind = st.number_input("Wind (mph)", min_value=0.0, step=0.1, key="cycling_wind")
            temp = st.number_input("Temp (°F)", min_value=-50.0, max_value=120.0, step=0.1, key="cycling_temp")
            humidity = st.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=0.1, key="cycling_humidity")
            ftp_used = st.number_input("FTP_used", min_value=0, step=1, key="cycling_ftp_used")
            carb_intake_hr = st.number_input("Carb Intake/hr", min_value=0.0, step=0.1, key="cycling_carb_intake_hr")
            sodium_intra = st.number_input("Sodium intra (g)", min_value=0.0, step=0.1, key="cycling_sodium_intra")
        else:  # Running
            duration = st.number_input("Duration (hrs)", min_value=0.0, step=0.1, key="running_duration")
            distance = st.number_input("Distance (mi)", min_value=0.0, step=0.1, key="running_distance")
            rpe = st.slider("RPE", min_value=1, max_value=10, value=5)
            session_type = st.selectbox("Session Type", ["Easy", "Zone 1", "Zone 2", "Zone 3", "Tempo", "Intervals", "Long Run"])
            carb_intake_hr = st.number_input("Carb Intake/hr", min_value=0.0, step=0.1, key="running_carb_intake_hr")
            sodium_intra = st.number_input("Sodium intra (g)", min_value=0.0, step=0.1, key="running_sodium_intra")
            max_hr = st.number_input("Max HR", min_value=0, step=1, key="running_max_hr")
            avg_hr = st.number_input("Avg HR", min_value=0, step=1, key="running_avg_hr")
            z1_time = st.number_input("Z1 Time (min)", min_value=0.0, step=0.1, key="running_z1_time")
            z2_time = st.number_input("Z2 Time (min)", min_value=0.0, step=0.1, key="running_z2_time")
            z3_time = st.number_input("Z3 Time (min)", min_value=0.0, step=0.1, key="running_z3_time")
            z4_time = st.number_input("Z4 Time (min)", min_value=0.0, step=0.1, key="running_z4_time")
            z5_time = st.number_input("Z5 Time (min)", min_value=0.0, step=0.1, key="running_z5_time")

        if st.button("Submit Exercise"):
            date_dt = pd.to_datetime(date)
            new_row = {'Date': date_dt, 'Phase': phase, 'Location': location}
            if activity_type == "Cycling":
                new_row['Sport'] = 'Cycling'
                new_row['Cycling Duration (hrs)'] = duration
                new_row['Cycling Distance (mi)'] = distance
                new_row['Cycling Speed (mph)'] = speed
                new_row['Cycling Elevation (ft)'] = elevation
                new_row['Avg Watt (Est)'] = avg_watt
                new_row['Max HR'] = max_hr
                new_row['Avg HR'] = avg_hr
                new_row['Z1 Time (min)'] = z1_time
                new_row['Z2 Time (min)'] = z2_time
                new_row['Z3 Time (min)'] = z3_time
                new_row['Z4 Time (min)'] = z4_time
                new_row['Z5 Time (min)'] = z5_time
                new_row['Cycling Session Type'] = session_type
                new_row['Position'] = position
                new_row['Wind (mph)'] = wind
                new_row['Temp (°F)'] = temp
                new_row['Humidity (%)'] = humidity
                new_row['FTP_used'] = ftp_used
                new_row['Carb Intake/hr'] = carb_intake_hr
                new_row['Sodium intra (g)'] = sodium_intra
                new_row['Cycling Hydration Index'] = sodium_intra / duration if duration > 0 else 0
                # Check for duplicate: same Date, Sport, Duration, Distance
                duplicate_mask = (
                    (df['Date'] == new_row['Date']) &
                    (df['Sport'] == new_row['Sport']) &
                    (df['Cycling Duration (hrs)'] == new_row['Cycling Duration (hrs)']) &
                    (df['Cycling Distance (mi)'] == new_row['Cycling Distance (mi)'])
                )
            else:
                new_row['Sport'] = 'Running'
                new_row['Run Duration (hrs)'] = duration
                new_row['Run Dist (mi)'] = distance
                new_row['Run RPE'] = rpe
                new_row['Run Session Type'] = session_type
                new_row['Carb Intake/hr'] = carb_intake_hr
                new_row['Sodium intra (g)'] = sodium_intra
                new_row['Max HR'] = max_hr
                new_row['Avg HR'] = avg_hr
                new_row['Z1 Time (min)'] = z1_time
                new_row['Z2 Time (min)'] = z2_time
                new_row['Z3 Time (min)'] = z3_time
                new_row['Z4 Time (min)'] = z4_time
                new_row['Z5 Time (min)'] = z5_time
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
                # Save to Excel
                from data_handler import save_master_log
                save_master_log(df, "sample_data/master_log.xlsx")
                st.success("Exercise logged successfully!")
                st.rerun()
            else:
                st.error("Duplicate session detected. Please check your inputs.")

    with subtab2:
        st.subheader("Log Nutrition")
        date = st.date_input("Date", key="nutrition_date")
        calories_in = st.number_input("Calories In", min_value=0, step=1)
        protein = st.number_input("Protein (g)", min_value=0.0, step=0.1)
        carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.1)
        fat = st.number_input("Fat (g)", min_value=0.0, step=0.1)
        sugar = st.number_input("Sugar (g)", min_value=0.0, step=0.1)
        sodium = st.number_input("Sodium (g)", min_value=0.0, step=0.1)
        potassium = st.number_input("Potassium (g)", min_value=0.0, step=0.1)

        if st.button("Submit Nutrition"):
            date_dt = pd.to_datetime(date)
            if date_dt in df['Date'].values:
                # Update existing row
                idx = df[df['Date'] == date_dt].index[0]
                df.at[idx, 'Calories In'] = calories_in
                df.at[idx, 'Protein (g)'] = protein
                df.at[idx, 'Carbs (g)'] = carbs
                df.at[idx, 'Fat (g)'] = fat
                df.at[idx, 'Sugar (g)'] = sugar
                df.at[idx, 'Sodium (g)'] = sodium
                df.at[idx, 'Potassium (g)'] = potassium
            else:
                # Append new row
                new_row = {'Date': date_dt, 'Calories In': calories_in, 'Protein (g)': protein, 'Carbs (g)': carbs, 'Fat (g)': fat, 'Sugar (g)': sugar, 'Sodium (g)': sodium, 'Potassium (g)': potassium}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            from data_handler import save_master_log
            save_master_log(df, "sample_data/master_log.xlsx")
            st.success("Nutrition logged successfully!")
            st.rerun()

    with subtab3:
        st.subheader("Log Daily Check In")
        date = st.date_input("Date", key="checkin_date")
        wake_time = st.time_input("Wake Time")
        sleep = st.number_input("Sleep (hrs)", min_value=0.0, step=0.1)
        rhr = st.number_input("RHR", min_value=0, step=1)
        weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1)
        mood = st.slider("Mood (1-10)", min_value=1, max_value=10, value=5)
        energy = st.slider("Energy (1-10)", min_value=1, max_value=10, value=5)
        hunger = st.slider("Hunger (1-10)", min_value=1, max_value=10, value=5)
        dopamine_cravings = st.slider("Dopamine Cravings (1-10)", min_value=1, max_value=10, value=5)
        notes = st.text_area("Notes")

        if st.button("Submit Check In"):
            date_dt = pd.to_datetime(date)
            if date_dt in df['Date'].values:
                # Update existing row
                idx = df[df['Date'] == date_dt].index[0]
                df.at[idx, 'Wake Time'] = wake_time
                df.at[idx, 'Sleep (hrs)'] = sleep
                df.at[idx, 'RHR'] = rhr
                df.at[idx, 'Weight (lbs)'] = weight
                df.at[idx, 'Mood (1-10)'] = mood
                df.at[idx, 'Energy (1-10)'] = energy
                df.at[idx, 'Hunger (1-10)'] = hunger
                df.at[idx, 'Dopamine Cravings (1-10)'] = dopamine_cravings
                df.at[idx, 'Notes'] = notes
            else:
                # Append new row
                new_row = {'Date': date_dt, 'Wake Time': wake_time, 'Sleep (hrs)': sleep, 'RHR': rhr, 'Weight (lbs)': weight, 'Mood (1-10)': mood, 'Energy (1-10)': energy, 'Hunger (1-10)': hunger, 'Dopamine Cravings (1-10)': dopamine_cravings, 'Notes': notes}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            from data_handler import save_master_log
            save_master_log(df, "sample_data/master_log.xlsx")
            st.success("Daily check in logged successfully!")
            st.rerun()

with tab8:
    st.header("Test")
    if 'gpx_contents' in st.session_state and st.session_state['gpx_contents']:
        st.subheader("GPX Data Preview")
        gpx_df = load_gpx_files(st.session_state['gpx_contents'], ftp=ftp_input)
        st.dataframe(gpx_df)
    else:
        st.write("Upload GPX files in the sidebar to test parsing.")

with tab9:
    st.header("Data Editor")
    edited_df = st.data_editor(df, num_rows="dynamic")
    if st.button("Save Changes", key="save_editor"):
        from data_handler import save_master_log
        save_master_log(edited_df, "sample_data/master_log.xlsx")
        st.success("Changes saved to master_log.xlsx")

# Preview DataFrame
st.header("Data Preview")
st.dataframe(df.head())
