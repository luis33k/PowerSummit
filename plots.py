import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

def plot_tss_tsb_over_time(df: pd.DataFrame) -> go.Figure:
    """
    Line plot for TSS & TSB over time.

    Args:
        df (pd.DataFrame): DataFrame with Date, Total TSS, TSB.

    Returns:
        go.Figure: Plotly figure.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Scatter(x=df['Date'], y=df['Total TSS (Bike + Run)'], name="Total TSS"), secondary_y=False)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['TSB (EWMA)'], name="TSB"), secondary_y=True)

    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="TSS", secondary_y=False)
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
    df['Week'] = df['Date'].dt.to_period('W').astype(str)
    weekly_tss = df.groupby('Week')['Total TSS (Bike + Run)'].sum().reset_index()

    fig = px.bar(weekly_tss, x='Week', y='Total TSS (Bike + Run)', title="Weekly TSS")
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
    if 'Carbs' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Carbs'], mode='lines'), row=2, col=1)
    if 'Salt' in df.columns:
        fig.add_trace(go.Scatter(x=df['Date'], y=df['Salt'], mode='lines'), row=3, col=1)

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
    if 'Carb Intake/hr' in df.columns and 'Total TSS (Bike + Run)' in df.columns:
        fig = px.scatter(df, x='Carb Intake/hr', y='Total TSS (Bike + Run)', title="Carbs/hr vs TSS")
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
