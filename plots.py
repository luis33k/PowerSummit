import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from logger import setup_logger

logger = setup_logger()
logger.info("Plots module initialized")

def plot_tss_tsb_over_time(df: pd.DataFrame, show_series: list = ["TSS", "TSB"]) -> go.Figure:
    """
    Line plot for TSS & TSB over time, conditionally based on show_series.

    Args:
        df (pd.DataFrame): DataFrame with Date, Total TSS, TSB.
        show_series (list): List of series to show, e.g., ["TSS", "TSB"].

    Returns:
        go.Figure: Plotly figure.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    has_primary = False
    has_secondary = False

    if "TSS" in show_series:
        # Select the first column if duplicates exist
        tss_col = [col for col in df.columns if 'Total TSS (Bike + Run)' in col and not col.endswith('(7d Avg)')][0]
        fig.add_trace(go.Scatter(x=df['Date'], y=df[tss_col], name="Total TSS"), secondary_y=False)
        has_primary = True

    if "TSB" in show_series:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['TSB (EWMA)'], name="TSB"), secondary_y=True)
        has_secondary = True

    fig.update_xaxes(title_text="Date")
    if has_primary:
        fig.update_yaxes(title_text="TSS", secondary_y=False)
    if has_secondary:
        fig.update_yaxes(title_text="TSB", secondary_y=True)

    return fig

def plot_weekly_tss(df: pd.DataFrame) -> go.Figure:
    """
    Bar chart for weekly TSS.

    Args:
        df (pd.DataFrame): DataFrame with Date, Total TSS.

    Returns:
        go.Figure: Plotly figure.
    """
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Week'] = df['Date'].dt.to_period('W').astype(str)
    # Select the first column if duplicates exist
    tss_col = [col for col in df.columns if 'Total TSS (Bike + Run)' in col and not col.endswith('(7d Avg)')][0]
    weekly_tss = df.groupby('Week')[tss_col].sum().reset_index()

    fig = px.bar(weekly_tss, x='Week', y=tss_col, title="Weekly TSS")
    return fig

def plot_speed_vs_hr(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot for speed vs HR or watts vs HR.

    Assumes 'Speed' and 'HR' columns; fallback to 'Avg Watt' and 'HR'.

    Args:
        df (pd.DataFrame): DataFrame with relevant columns.

    Returns:
        go.Figure: Plotly figure.
    """
    if 'Speed' in df.columns and 'HR' in df.columns:
        fig = px.scatter(df, x='Speed', y='HR', title="Speed vs HR")
    elif 'Avg Watt' in df.columns and 'HR' in df.columns:
        fig = px.scatter(df, x='Avg Watt', y='HR', title="Watts vs HR")
    else:
        fig = go.Figure()
        fig.add_annotation(text="No suitable columns for scatter plot", showarrow=False)
    return fig

def plot_small_multiples_sleep_carbs_salt(df: pd.DataFrame) -> go.Figure:
    """
    Small-multiples for sleep, carbs, salt.

    Args:
        df (pd.DataFrame): DataFrame with Date, Sleep, Carbs, Salt.

    Returns:
        go.Figure: Plotly figure.
    """
    fig = make_subplots(rows=3, cols=1, subplot_titles=("Sleep", "Carbs", "Salt"))

    if 'Sleep (hrs)' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Sleep (hrs)'], mode='lines'), row=1, col=1)
    if 'Carbs (g)' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Carbs (g)'], mode='lines'), row=2, col=1)
    if 'Sodium (g)' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Sodium (g)'], mode='lines'), row=3, col=1)

    fig.update_layout(height=600, title_text="Small Multiples: Sleep, Carbs, Salt")
    return fig

def plot_avg_watt_over_time(df: pd.DataFrame) -> go.Figure:
    """
    Plot avg watt over time.

    Args:
        df (pd.DataFrame): DataFrame with Date, Avg Watt.

    Returns:
        go.Figure: Plotly figure.
    """
    fig = px.line(df, x='Date', y='Avg Watt (Est)', title="Avg Watt Over Time")
    return fig

def plot_carb_hr_vs_tss(df: pd.DataFrame) -> go.Figure:
    """
    Scatter plot for carb/hr vs TSS.

    Args:
        df (pd.DataFrame): DataFrame with Carbs/hr, Total TSS.

    Returns:
        go.Figure: Plotly figure.
    """
    # Select the first column if duplicates exist
    carb_col = [col for col in df.columns if 'Carb Intake/hr' in col][0] if any('Carb Intake/hr' in col for col in df.columns) else None
    tss_col = [col for col in df.columns if 'Total TSS (Bike + Run)' in col and not col.endswith('(7d Avg)')][0] if any('Total TSS (Bike + Run)' in col for col in df.columns) else None
    if carb_col and tss_col:
        fig = px.scatter(df, x=carb_col, y=tss_col, title="Carbs/hr vs TSS")
    else:
        fig = go.Figure()
        fig.add_annotation(text="No Carbs/hr or TSS data", showarrow=False)
    return fig

def plot_sleep_trend(df: pd.DataFrame) -> go.Figure:
    """
    Sleep trend line plot.

    Args:
        df (pd.DataFrame): DataFrame with Date, Sleep.

    Returns:
        go.Figure: Plotly figure.
    """
    fig = px.line(df, x='Date', y='Sleep (hrs)', title="Sleep Trend")
    return fig

def plot_rhr_trend(df: pd.DataFrame) -> go.Figure:
    """
    RHR trend line plot.

    Args:
        df (pd.DataFrame): DataFrame with Date, RHR.

    Returns:
        go.Figure: Plotly figure.
    """
    if 'RHR' in df.columns:
        fig = px.line(df, x='Date', y='RHR', title="RHR Trend")
    else:
        fig = go.Figure()
        fig.add_annotation(text="No RHR data", showarrow=False)
    return fig
