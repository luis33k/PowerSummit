import streamlit as st
import pandas as pd
from data_handler import load_master_log
from metrics import compute_all_metrics
from plots import (
    plot_tss_tsb_over_time, plot_weekly_tss, plot_speed_vs_hr,
    plot_small_multiples_sleep_carbs_salt, plot_avg_watt_over_time,
    plot_carb_hr_vs_tss, plot_sleep_trend, plot_rhr_trend
)
from utils import save_processed_data, get_top_kpis, compute_recovery_score
import os

st.set_page_config(page_title="Training Dashboard", layout="wide")

# Sidebar
st.sidebar.title("Controls")
uploaded_file = st.sidebar.file_uploader("Upload master_log.xlsx", type="xlsx")
date_range = st.sidebar.date_input("Date Range", [])
show_series = st.sidebar.multiselect("Show Series", ["TSS", "TSB", "Sleep", "Carbs"], default=["TSS", "TSB"])

# Load data
if uploaded_file is not None:
    df = load_master_log(uploaded_file)
else:
    default_path = "sample_data/master_log.xlsx"
    os.makedirs("sample_data", exist_ok=True)
    df = load_master_log(default_path)

# Compute metrics
df = compute_all_metrics(df)

# Save processed data
os.makedirs("outputs", exist_ok=True)
save_processed_data(df, "outputs/processed_master.csv")

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["Overview", "Cycling", "Running", "Nutrition", "Recovery", "Data Entry", "Data Editor"])

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
    activity_type = df.get('Activity Type', pd.Series([''] * len(df))).astype(str)
    cycling_df = df[activity_type.str.lower() == 'cycling']
    cols = ['Date']
    if 'Duration' in cycling_df.columns and 'Duration' not in cols:
        cols.append('Duration')
    if 'Avg Watt' in cycling_df.columns and 'Avg Watt' not in cols:
        cols.append('Avg Watt')
    if 'IF' in cycling_df.columns and 'IF' not in cols:
        cols.append('IF')
    if 'Cycling TSS' in cycling_df.columns and 'Cycling TSS' not in cols:
        cols.append('Cycling TSS')
    cols = [col for col in cols if col in cycling_df.columns]
    st.dataframe(cycling_df[cols])

    # Filter by session type if column exists
    if 'Session Type' in df.columns:
        session_types = st.multiselect("Filter Session Type", cycling_df['Session Type'].unique())
        if session_types:
            cycling_df = cycling_df[cycling_df['Session Type'].isin(session_types)]

    st.subheader("Avg Watt Over Time")
    fig = plot_avg_watt_over_time(cycling_df)
    st.plotly_chart(fig, width='stretch')

with tab3:
    st.header("Running")
    activity_type = df.get('Activity Type', pd.Series([''] * len(df))).astype(str)
    running_df = df[activity_type.str.lower() == 'run']
    cols = ['Date']
    if 'Duration' in running_df.columns and 'Duration' not in cols:
        cols.append('Duration')
    if 'RPE' in running_df.columns and 'RPE' not in cols:
        cols.append('RPE')
    if 'Run TSS' in running_df.columns and 'Run TSS' not in cols:
        cols.append('Run TSS')
    st.dataframe(running_df[cols])

    # RPE filter
    if 'RPE' in running_df.columns:
        rpe_range = st.slider("RPE Range", min_value=1, max_value=10, value=(1,10))
        running_df = running_df[(running_df['RPE'] >= rpe_range[0]) & (running_df['RPE'] <= rpe_range[1])]

    st.dataframe(running_df[cols])

with tab4:
    st.header("Nutrition")
    # Daily calories, macros - assuming columns exist
    if 'Calories In' in df.columns and not df.empty:
        st.subheader("Calories In vs Calories Burned")
        available_cols = ['Calories In']
        if 'Cycling Calories Burned' in df.columns:
            available_cols.append('Cycling Calories Burned')
        if 'Run Calories Burned' in df.columns:
            available_cols.append('Run Calories Burned')
        if len(available_cols) > 1:
            fig = df.set_index('Date')[available_cols].fillna(0).plot(kind='bar', stacked=True)
            st.pyplot(fig.figure)

    # Macros bar chart
    macros = ['Protein (g)', 'Carbs (g)', 'Fat (g)', 'Sugar (g)', 'Sodium (g)']
    available_macros = [m for m in macros if m in df.columns]
    if available_macros and not df.empty:
        st.subheader("Daily Macros")
        fig = df.set_index('Date')[available_macros].fillna(0).plot(kind='bar', stacked=True)
        st.pyplot(fig.figure)

    st.subheader("Carbs/hr vs TSS")
    fig = plot_carb_hr_vs_tss(df)
    st.plotly_chart(fig, width='stretch')

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
        df['Recovery Score'] = df.apply(lambda row: compute_recovery_score(row['Sleep'], row['TSB (EWMA)']), axis=1)
        st.subheader("Recovery Score Over Time")
        st.line_chart(df.set_index('Date')['Recovery Score'])

with tab6:
    st.header("Data Entry")
    subtab1, subtab2, subtab3 = st.tabs(["Log Exercise", "Log Nutrition", "Log Daily Check In"])

    with subtab1:
        st.subheader("Log Exercise")
        activity_type = st.radio("Activity Type", ["Cycling", "Running"])
        date = st.date_input("Date")
        if activity_type == "Cycling":
            duration = st.number_input("Duration (hrs)", min_value=0.0, step=0.1)
            distance = st.number_input("Distance (mi)", min_value=0.0, step=0.1)
            avg_watt = st.number_input("Avg Watt", min_value=0, step=1)
            carb_intra_fuel = st.number_input("Carb Intra Fuel (g)", min_value=0.0, step=0.1)
            session_type = st.selectbox("Session Type", ["Recovery", "Tempo", "Threshold", "VO2 Max", "Sweet Spot", "Intervals"])
        else:  # Running
            duration = st.number_input("Duration (hrs)", min_value=0.0, step=0.1)
            distance = st.number_input("Distance (mi)", min_value=0.0, step=0.1)
            rpe = st.slider("RPE", min_value=1, max_value=10, value=5)
            carb_intra_fuel = st.number_input("Carb Intra Fuel (g)", min_value=0.0, step=0.1)
            session_type = st.selectbox("Session Type", ["Easy", "Tempo", "Intervals", "Long Run"])

        if st.button("Submit Exercise"):
            date_dt = pd.to_datetime(date)
            if date_dt in df['Date'].values:
                # Update existing row
                idx = df[df['Date'] == date_dt].index[0]
                df.at[idx, 'Activity Type'] = activity_type
                if activity_type == "Cycling":
                    df.at[idx, 'Cycling Duration'] = duration
                    df.at[idx, 'Cycling Distance'] = distance
                    df.at[idx, 'Avg Watt'] = avg_watt
                    df.at[idx, 'Carb Intra Fuel'] = carb_intra_fuel
                    df.at[idx, 'Cycling Session Type'] = session_type
                else:
                    df.at[idx, 'Run Duration'] = duration
                    df.at[idx, 'Run Dist'] = distance
                    df.at[idx, 'Run RPE'] = rpe
                    df.at[idx, 'Carb Intra Fuel'] = carb_intra_fuel
                    df.at[idx, 'Run Session Type'] = session_type
            else:
                # Append new row
                new_row = {'Date': date_dt}
                if activity_type == "Cycling":
                    new_row['Activity Type'] = 'Cycling'
                    new_row['Cycling Duration'] = duration
                    new_row['Cycling Distance'] = distance
                    new_row['Avg Watt'] = avg_watt
                    new_row['Carb Intra Fuel'] = carb_intra_fuel
                    new_row['Cycling Session Type'] = session_type
                else:
                    new_row['Activity Type'] = 'Run'
                    new_row['Run Duration'] = duration
                    new_row['Run Dist'] = distance
                    new_row['Run RPE'] = rpe
                    new_row['Carb Intra Fuel'] = carb_intra_fuel
                    new_row['Run Session Type'] = session_type
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            # Save to Excel
            from data_handler import save_master_log
            save_master_log(df, "sample_data/master_log.xlsx")
            st.success("Exercise logged successfully!")
            st.rerun()

    with subtab2:
        st.subheader("Log Nutrition")
        date = st.date_input("Date", key="nutrition_date")
        calories_in = st.number_input("Calories In", min_value=0, step=1)
        protein = st.number_input("Protein (g)", min_value=0.0, step=0.1)
        carbs = st.number_input("Carbs (g)", min_value=0.0, step=0.1)
        fat = st.number_input("Fat (g)", min_value=0.0, step=0.1)
        sugar = st.number_input("Sugar (g)", min_value=0.0, step=0.1)
        sodium = st.number_input("Sodium (g)", min_value=0.0, step=0.1)

        if st.button("Submit Nutrition"):
            date_dt = pd.to_datetime(date)
            if date_dt in df['Date'].values:
                # Update existing row
                idx = df[df['Date'] == date_dt].index[0]
                df.at[idx, 'Calories In'] = calories_in
                df.at[idx, 'Protein'] = protein
                df.at[idx, 'Carbs'] = carbs
                df.at[idx, 'Fat'] = fat
                df.at[idx, 'Sugar'] = sugar
                df.at[idx, 'Sodium'] = sodium
            else:
                # Append new row
                new_row = {'Date': date_dt, 'Calories In': calories_in, 'Protein': protein, 'Carbs': carbs, 'Fat': fat, 'Sugar': sugar, 'Sodium': sodium}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            from data_handler import save_master_log
            save_master_log(df, "sample_data/master_log.xlsx")
            st.success("Nutrition logged successfully!")
            st.rerun()

    with subtab3:
        st.subheader("Log Daily Check In")
        date = st.date_input("Date", key="checkin_date")
        sleep = st.number_input("Sleep (hrs)", min_value=0.0, step=0.1)
        weight = st.number_input("Weight (lbs)", min_value=0.0, step=0.1)
        rhr = st.number_input("RHR", min_value=0, step=1)
        mood = st.slider("Mood", min_value=1, max_value=10, value=5)
        energy = st.slider("Energy", min_value=1, max_value=10, value=5)
        dopamine_cravings = st.slider("Dopamine Cravings", min_value=1, max_value=10, value=5)

        if st.button("Submit Check In"):
            date_dt = pd.to_datetime(date)
            if date_dt in df['Date'].values:
                # Update existing row
                idx = df[df['Date'] == date_dt].index[0]
                df.at[idx, 'Sleep'] = sleep
                df.at[idx, 'Weight'] = weight
                df.at[idx, 'RHR'] = rhr
                df.at[idx, 'Mood'] = mood
                df.at[idx, 'Energy'] = energy
                df.at[idx, 'Dopamine Cravings'] = dopamine_cravings
            else:
                # Append new row
                new_row = {'Date': date_dt, 'Sleep': sleep, 'Weight': weight, 'RHR': rhr, 'Mood': mood, 'Energy': energy, 'Dopamine Cravings': dopamine_cravings}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            from data_handler import save_master_log
            save_master_log(df, "sample_data/master_log.xlsx")
            st.success("Daily check in logged successfully!")
            st.rerun()

with tab7:
    st.header("Data Editor")
    edited_df = st.data_editor(df, num_rows="dynamic")
    if st.button("Save Changes", key="save_editor"):
        from data_handler import save_master_log
        save_master_log(edited_df, "sample_data/master_log.xlsx")
        st.success("Changes saved to master_log.xlsx")

# Preview DataFrame
st.header("Data Preview")
st.dataframe(df.head())
