from datetime import datetime, timedelta
import os
from typing import Dict, Union, Optional, Tuple
import pandas as pd
import plotly.express as px
import fitdecode

def dataprep(afile):
    conv = Converter()
    print(afile)
    df_lap, df = conv.fit_to_dataframes(fname=afile)
    df['vam'] = df['altitude'].diff() / df['timestamp'].diff().dt.total_seconds() * 60 * 60
    df['vamh'] = df['vam'] / df['heart_rate']
    df['interval_time'] = df['timestamp'].diff().dt.total_seconds()
    df['total_time'] = df['timestamp'].diff().dt.total_seconds().cumsum()
    df['interval_distance'] = df['speed'] * df['interval_time']
    df['slope'] = df['altitude'].diff() / df['interval_distance']

    intervals = range(60, 1200, 60)
    for t in intervals:
        df[f'slope_{t}'] = df['slope'].rolling(t).mean() * 100
        df[f'vamh_{t}'] = df['vamh'].rolling(t).mean()
        df[f'vam_{t}'] = df['vam'].rolling(t).mean()
        df[f'hr_{t}'] = df['heart_rate'].rolling(t).mean()
    return df


def vamh_time(df):
    fig = px.scatter(df, x="total_time", y="vamh")
    fig.show()


def vamh_distance(df):
    fig = px.scatter(df, x="interval_distance", y="vamh")
    fig.show()


def plot_vam(df):
    intervals = range(60, 1200, 60)
    slopes = [f"slope_{s}-{s + 1}" for s in range(3, 10)]
    vam_curve = pd.DataFrame(columns=['interval'] + slopes)
    vamh_curve = pd.DataFrame(columns=['interval'] + slopes)
    for t in intervals:
        vam_row = [t]
        vamh_row = [t]
        for s in range(3, 10):
            vam = df[(s < df[f'slope_{t}']) & (df[f'slope_{t}'] < s + 1)][f'vam_{t}'].max()
            vamh = df[(s < df[f'slope_{t}']) & (df[f'slope_{t}'] < s + 1)][f'vamh_{t}'].max()
            if vam:
                vam_row.append(vam)
                vamh_row.append(vamh)
            else:
                vam_row.append(0)
                vamh_row.append(0)
        vam_curve.loc[len(vam_curve.index)] = vam_row
        vamh_curve.loc[len(vamh_curve.index)] = vamh_row

    fig = px.line(vam_curve, x="interval", y=slopes, title='Seconds VS VAM',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.update_xaxes(title_text='Seconds')
    fig.update_yaxes(title_text='VAM/hr')
    fig.update_layout(
        width=1000,
        height=800)
    fig.show()

    fig = px.line(vamh_curve, x="interval", y=slopes, title='Seconds VS VAM/hr',
                  color_discrete_sequence=px.colors.sequential.Blues)
    fig.update_xaxes(title_text='Seconds')
    fig.update_yaxes(title_text='VAM/hr')
    fig.update_layout(
        width=1000,
        height=800)
    fig.show()


class Converter:
    """Main converter that holds the FIT > pd.DataFrame and pd.DataFrame > GPX methods"""

    def __init__(self, status_msg: bool = False):
        """Main constructor for StravaConverter
        Parameters:
            status_msg (bool): Option to have the Converter print to console with status messages,
            such as number of files converted.
        """
        self.status_msg = status_msg
        # The names of the columns we will use in our points and laps DataFrame
        # (use the same name as the field names in FIT file to facilate parsing)
        self._colnames_points = [
            'latitude',
            'longitude',
            'lap',
            'altitude',
            'distance',
            'timestamp',
            'heart_rate',
            'cadence',
            'speed',
            'power'
        ]

        self._colnames_laps = [
            'number',
            'start_time',
            'total_distance',
            'total_elapsed_time',
            'max_speed',
            'max_heart_rate',
            'avg_heart_rate'
        ]

        # Note: get_fit_laps(), get_fit_points(), get_dataframes() are shamelessly copied (and adapted) from:
        # https://github.com/bunburya/fitness_tracker_data_parsing/blob/main/parse_fit.py

    def _get_fit_laps(self, frame: fitdecode.records.FitDataMessage) \
            -> Dict[str, Union[float, datetime, timedelta, int]]:
        """Extract some data from a FIT frame representing a lap and return it as a dict.
        """
        # Step 0: Initialise data output
        data: Dict[str, Union[float, datetime, timedelta, int]] = {}

        # Step 1: Extract all other fields
        #  (excluding 'number' (lap number) because we don't get that from the data but rather count it ourselves)
        for field in self._colnames_laps[1:]:
            if frame.has_field(field):
                data[field] = frame.get_value(field)

        return data

    def _get_fit_points(self, frame: fitdecode.records.FitDataMessage) \
            -> Optional[Dict[str, Union[float, int, str, datetime]]]:
        """Extract some data from an FIT frame representing a track point and return it as a dict.
        """
        # Step 0: Initialise data output
        data: Dict[str, Union[float, int, str, datetime]] = {}

        # Step 1: Obtain frame lat and long and convert it from integer to degree (if frame has lat and long data)
        if not (frame.has_field('position_lat') and frame.has_field('position_long')):
            # Frame does not have any latitude or longitude data. Ignore these frames in order to keep things simple
            return None
        elif frame.get_value('position_lat') is None and frame.get_value('position_long') is None:
            # Frame lat or long is None. Ignore frame
            return None
        else:
            data['latitude'] = frame.get_value('position_lat') / ((2 ** 32) / 360)
            data['longitude'] = frame.get_value('position_long') / ((2 ** 32) / 360)

        # Step 2: Extract all other fields
        for field in self._colnames_points[3:]:
            if frame.has_field(field):
                data[field] = frame.get_value(field)

        return data

    def fit_to_dataframes(self, fname: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Takes the path to a FIT file and returns two Pandas DataFrames for lap data and point data
        Parameters:
            fname (str): string representing file path of the FIT file
        Returns:
            dfs (tuple): df containing data about the laps , df containing data about the individual points.
        """
        # Check that this is a .FIT file
        input_extension = os.path.splitext(fname)[1]
        if input_extension.lower() != '.fit':
            raise fitdecode.exceptions.FitHeaderError("Input file must be a .FIT file.")

        data_points = []
        data_laps = []
        lap_no = 1
        with fitdecode.FitReader(fname) as fit_file:
            for frame in fit_file:
                if isinstance(frame, fitdecode.records.FitDataMessage):
                    # Determine if frame is a data point or a lap:
                    if frame.name == 'record':
                        single_point_data = self._get_fit_points(frame)
                        if single_point_data is not None:
                            single_point_data['lap'] = lap_no  # record lap number
                            data_points.append(single_point_data)

                    elif frame.name == 'lap':
                        single_lap_data = self._get_fit_laps(frame)
                        single_lap_data['number'] = lap_no
                        data_laps.append(single_lap_data)
                        lap_no += 1  # increase lap counter

        # Create DataFrames from the data we have collected.
        # (If any information is missing from a lap or track point, it will show up as a "NaN" in the DataFrame.)

        df_laps = pd.DataFrame(data_laps, columns=self._colnames_laps)
        df_laps.set_index('number', inplace=True)
        df_points = pd.DataFrame(data_points, columns=self._colnames_points)
        return df_laps, df_points