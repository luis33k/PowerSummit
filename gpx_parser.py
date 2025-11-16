import gpxpy
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

def parse_gpx_file(file_content: str) -> dict:
    """
    Parse GPX content and extract workout metrics.

    Args:
        file_content (str): GPX file content as string.

    Returns:
        dict: Extracted metrics including Date, Duration (hrs), Distance (mi), Elevation Gain (ft),
              Avg HR, Max HR, Avg Power, Max Power, Avg Speed (mph).
    """
    gpx = gpxpy.parse(file_content)

    # Assume single track/segment
    track = gpx.tracks[0]
    segment = track.segments[0]

    # Date from first point
    start_time = segment.points[0].time
    date = start_time.date() if start_time else datetime.now().date()

    # Duration
    if start_time and segment.points[-1].time:
        duration_sec = (segment.points[-1].time - start_time).total_seconds()
        duration_hrs = duration_sec / 3600
    else:
        duration_hrs = np.nan

    # Distance in miles
    distance_mi = gpx.length_3d() / 1609.34 if gpx.length_3d() else np.nan

    # Elevation gain in feet
    elevation_gain_ft = 0
    prev_elev = None
    for point in segment.points:
        if point.elevation is not None:
            if prev_elev is not None and point.elevation > prev_elev:
                elevation_gain_ft += point.elevation - prev_elev
            prev_elev = point.elevation

    # HR, Power, Cadence (extensions)
    hrs = []
    powers = []
    cadences = []
    speeds = []
    for point in segment.points:
        if point.extensions:
            # Assuming Garmin/Strava extensions for HR, power, cadence
            # point.extensions is a list of elements, need to parse differently
            hr = None
            power = None
            cadence = None
            for ext in point.extensions:
                if hasattr(ext, 'tag'):
                    if 'hr' in ext.tag:
                        hr = ext.text
                    elif 'power' in ext.tag:
                        power = ext.text
                    elif 'cadence' in ext.tag or 'cad' in ext.tag:
                        cadence = ext.text
            if hr:
                hrs.append(float(hr))
            if power:
                powers.append(float(power))
            if cadence:
                cadences.append(float(cadence))
        # Speed from point.speed if available, else calculate
        if point.speed:
            speeds.append(point.speed * 2.23694)  # m/s to mph

    avg_hr = np.mean(hrs) if hrs else np.nan
    max_hr = np.max(hrs) if hrs else np.nan
    avg_power = np.mean(powers) if powers else np.nan
    max_power = np.max(powers) if powers else np.nan
    avg_cadence = np.mean(cadences) if cadences else np.nan
    avg_speed = np.mean(speeds) if speeds else np.nan

    return {
        'Date': date,
        'GPX Duration (hrs)': duration_hrs,
        'GPX Distance (mi)': distance_mi,
        'GPX Elevation Gain (ft)': elevation_gain_ft,
        'GPX Avg HR': avg_hr,
        'GPX Max HR': max_hr,
        'GPX Avg Power': avg_power,
        'GPX Max Power': max_power,
        'GPX Avg Speed (mph)': avg_speed,
        'GPX Avg Cadence': avg_cadence
    }

def compute_gpx_metrics(gpx_data: dict, ftp: float = None) -> dict:
    """
    Compute additional metrics from GPX data: IF, TSS, KJ, Watts/kg.

    Assumes cycling if power data present, running otherwise.

    Args:
        gpx_data (dict): GPX extracted data.
        ftp (float): FTP for IF calculation.

    Returns:
        dict: Computed metrics.
    """
    duration = gpx_data.get('GPX Duration (hrs)', np.nan)
    avg_power = gpx_data.get('GPX Avg Power', np.nan)
    weight_kg = 70  # Default, can be passed or from DF

    metrics = {}

    if not pd.isna(avg_power) and ftp:
        # Cycling
        if_ = avg_power / ftp
        tss = duration * (if_ ** 2) * 100 if not pd.isna(duration) else np.nan
        kj = duration * avg_power * 3600 / 1000 if not pd.isna(duration) else np.nan
        watts_kg = avg_power / weight_kg
        metrics.update({
            'GPX IF': if_,
            'GPX TSS': tss,
            'GPX KJ': kj,
            'GPX Watts/kg': watts_kg
        })
    else:
        # Running: estimate TSS from HR if available
        avg_hr = gpx_data.get('GPX Avg HR', np.nan)
        if not pd.isna(avg_hr) and not pd.isna(duration):
            # Rough estimate: assume max HR 200, zones
            max_hr = 200
            if avg_hr < 0.7 * max_hr:
                rpe = 3
            elif avg_hr < 0.8 * max_hr:
                rpe = 5
            elif avg_hr < 0.9 * max_hr:
                rpe = 7
            else:
                rpe = 9
            duration_min = duration * 60
            tss = (duration_min * (rpe ** 2)) / 30
            kj = duration * 10 * 4.184  # Rough kcal estimate * 4.184
            metrics.update({
                'GPX TSS': tss,
                'GPX KJ': kj
            })

    return metrics

def load_gpx_files(file_contents: list, ftp: float = None) -> pd.DataFrame:
    """
    Load multiple GPX file contents and return a DataFrame with extracted and computed metrics.

    Args:
        file_contents (list): List of GPX file contents as strings.
        ftp (float): FTP value for calculations.

    Returns:
        pd.DataFrame: DataFrame with GPX data.
    """
    data = []
    for content in file_contents:
        try:
            gpx_data = parse_gpx_file(content)
            computed = compute_gpx_metrics(gpx_data, ftp)
            gpx_data.update(computed)
            data.append(gpx_data)
        except Exception as e:
            print(f"Error parsing GPX content: {e}")
    return pd.DataFrame(data)
