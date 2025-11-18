import gpxpy
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from logger import setup_logger

logger = setup_logger()
logger.info("GPX parser module initialized")

def parse_gpx_file(file_content: str, sport_override: str = None) -> dict:
    """
    Parse GPX content and extract workout metrics.

    Args:
        file_content (str): GPX file content as string.

    Returns:
        dict: Extracted metrics including Date, Duration (hrs), Distance (mi), Elevation Gain (ft),
              Avg HR, Max HR, Avg Power, Max Power, Avg Speed (mph).
    """
    logger.info("Parsing GPX file")
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

    # Calculate zone times (assume max HR 200, zones: Z1 <70%, Z2 70-80%, Z3 80-90%, Z4 90-100%, Z5 >100%)
    max_hr_assumed = 200
    z1_threshold = 0.7 * max_hr_assumed
    z2_threshold = 0.8 * max_hr_assumed
    z3_threshold = 0.9 * max_hr_assumed
    z4_threshold = 1.0 * max_hr_assumed
    # Z5 >100%

    z1_time = 0
    z2_time = 0
    z3_time = 0
    z4_time = 0
    z5_time = 0

    if hrs:
        for hr in hrs:
            if hr < z1_threshold:
                z1_time += 1  # Assuming 1 second per point
            elif hr < z2_threshold:
                z2_time += 1
            elif hr < z3_threshold:
                z3_time += 1
            elif hr < z4_threshold:
                z4_time += 1
            else:
                z5_time += 1

        # Convert to minutes
        z1_time_min = z1_time / 60
        z2_time_min = z2_time / 60
        z3_time_min = z3_time / 60
        z4_time_min = z4_time / 60
        z5_time_min = z5_time / 60
    else:
        z1_time_min = z2_time_min = z3_time_min = z4_time_min = z5_time_min = np.nan

    # Detect sport
    if sport_override:
        sport = sport_override
    else:
        # Detect from track name first
        track_name = track.name.lower() if track.name else ''
        if 'bike' in track_name or 'cycle' in track_name or 'cycling' in track_name:
            sport = 'Cycling'
        elif 'run' in track_name or 'running' in track_name or 'jog' in track_name:
            sport = 'Running'
        else:
            # Fallback to data-based detection
            if not pd.isna(avg_power):
                sport = 'Cycling'
            elif not pd.isna(avg_speed) and avg_speed > 10:
                sport = 'Cycling'
            elif not pd.isna(elevation_gain_ft) and elevation_gain_ft > 500:
                sport = 'Cycling'
            else:
                sport = 'Running'

    return {
        'Date': date,
        'Sport': sport,
        'GPX Duration (hrs)': duration_hrs,
        'GPX Distance (mi)': distance_mi,
        'GPX Elevation Gain (ft)': elevation_gain_ft,
        'GPX Avg HR': avg_hr,
        'GPX Max HR': max_hr,
        'GPX Avg Power': avg_power,
        'GPX Max Power': max_power,
        'GPX Avg Speed (mph)': avg_speed,
        'GPX Avg Cadence': avg_cadence,
        'GPX Z1 Time (min)': z1_time_min,
        'GPX Z2 Time (min)': z2_time_min,
        'GPX Z3 Time (min)': z3_time_min,
        'GPX Z4 Time (min)': z4_time_min,
        'GPX Z5 Time (min)': z5_time_min
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
    logger.info(f"Computing GPX metrics for date {gpx_data.get('Date')}, sport {gpx_data.get('Sport')}")
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

def load_gpx_files(file_contents: list, ftp: float = None, sport_override: str = None) -> pd.DataFrame:
    """
    Load multiple GPX file contents and return a DataFrame with extracted and computed metrics.

    Args:
        file_contents (list): List of GPX file contents as strings.
        ftp (float): FTP value for calculations.
        sport_override (str): Override sport detection ('Cycling', 'Running', or None for auto).

    Returns:
        pd.DataFrame: DataFrame with GPX data.
    """
    data = []
    for content in file_contents:
        try:
            gpx_data = parse_gpx_file(content, sport_override)
            computed = compute_gpx_metrics(gpx_data, ftp)
            gpx_data.update(computed)
            data.append(gpx_data)
        except Exception as e:
            logger.error(f"Error parsing GPX content: {e}")
            continue
    return pd.DataFrame(data)
