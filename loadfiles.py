import os
from datetime import datetime, timedelta
from typing import Dict, Union, Optional

import fitdecode
import pandas as pd

pd.set_option('mode.chained_assignment', None)


def load_fit(fit_file: str) -> pd.DataFrame:
    """Load a fit file into a pandas dataframe"""
    conv = Converter()
    print(f"Loading: {fit_file}")
    df_lap, df = conv.fit_to_dataframes(fname=fit_file)
    return df


def slots2dict(classobj: object) -> dict:
    "Convert a class object with slots to a dict"
    {s: getattr(classobj, s, None) for s in classobj.__slots__}
    return {s: getattr(classobj, s, None) for s in classobj.__slots__}


def FieldDefinition2dict(frame: fitdecode.records.FitDefinitionMessage) -> dict:
    "Convert a FieldDefinition to dict"
    frame_dict = {}
    for d in frame.field_defs:
        frame_dict['name'] = d.name
        frame_dict['is_dev'] = d.is_dev
        frame_dict['type']: d.type.name
    return frame_dict

    # return {s: getattr(FieldDefinition, s, None) for s in FieldDefinition.__slots__}


def frame2dict(frame: fitdecode.records.FitDataMessage) -> dict:
    "Convert a fonvert frame fields to dict"
    frame_dict = {}
    for field in frame.fields:
        # print(f"Frame Field Name: {field.value}")
        try:
            frame_dict[field.name] = frame.get_value(field.name)
        except KeyError:
            frame_dict[field.name] = None
    return frame_dict


def fit2dicts(fit_file: str) -> tuple[
    list[dict, ...], list[dict, ...], list[dict, ...], list[dict, ...], list[dict, ...]]:
    """Load a fit file"""
    input_extension = os.path.splitext(fit_file)[1]
    if input_extension.lower() != '.fit':
        raise fitdecode.exceptions.FitHeaderError("Input file must be a .FIT file.")
    FitHeaders = []
    FitDefinitionMessages = []
    FitDataMessages = []
    FitCRCs = []
    fitother = []
    with open(fit_file, 'rb') as fitfile:
        fit = fitdecode.FitReader(fitfile)
        for i, frame in enumerate(fit):
            match frame:
                case fitdecode.records.FitHeader():
                    FitHeaders.append(slots2dict(frame))
                case fitdecode.records.FitDefinitionMessage():
                    FitDefinitionMessages.append(FieldDefinition2dict(frame))
                    # FitDefinitionMessages.append({i: slots2dict(frame)})
                case fitdecode.records.FitDataMessage():
                    FitDataMessages.append(frame2dict(frame))
                    # FitDataMessages.append({i: slots2dict(frame)})
                case fitdecode.records.FitCRC():
                    FitCRCs.append(slots2dict(frame))
                case _:
                    fitother.append(slots2dict(frame))
    return FitHeaders, FitDefinitionMessages, FitDataMessages, FitCRCs, fitother


def fit2df(fit_file: str) -> tuple[pd.DataFrame, ...]:
    """Load a fit file into a pandas dataframe"""
    FitHeaders, FitDefinitionMessages, FitDataMessages, FitCRCs, fitother = fit2dicts(fit_file)
    FitHeaders_df = pd.DataFrame(FitHeaders)
    FitDefinitionMessages_df = pd.DataFrame(FitDefinitionMessages)
    FitDataMessages_df = pd.DataFrame(FitDataMessages)
    FitDataMessages_df.dropna(how='all', axis='columns', inplace=True)
    Data = FitDataMessages_df[(FitDataMessages_df.event_type == 'marker') | (FitDataMessages_df.distance.notnull())]
    Data.dropna(how='all', axis='columns', inplace=True)
    file_data = FitDataMessages_df[
        (FitDataMessages_df['distance'].isnull()) & (FitDataMessages_df['event_type'] != 'marker')]
    file_data.dropna(how='all', axis='columns', inplace=True)
    file_data.dropna(how='all', axis='rows', inplace=True)
    FitCRCs_df = pd.DataFrame(FitCRCs)
    fitother_df = pd.DataFrame(fitother)
    return FitHeaders_df, FitDefinitionMessages_df, file_data, Data, FitCRCs_df, fitother_df


def fit2excel(fit_file: str, excel_file: str, remove_unknown=True) -> None:
    """Load a fit file into a pandas dataframe"""
    FitHeaders_df, FitDefinitionMessages_df, file_data, Data, FitCRCs_df, fitother_df = fit2df(fit_file)
    with pd.ExcelWriter(excel_file) as writer:
        FitHeaders_df.to_excel(writer, sheet_name='FitHeaders')
        FitDefinitionMessages_df.to_excel(writer, sheet_name='FitDefinitionMessages')
        if remove_unknown:
            file_data = file_data[[c for c in file_data if 'unknown' not in c]]
            Data = Data[[c for c in Data if 'unknown' not in c]]

        # deal with timezone columns in FitDataMessages_df
        for d in [file_data, Data]:
            date_columns = d.select_dtypes(include=['datetime64[ns, UTC]']).columns
            for c in date_columns:
                try:
                    d[c] = d[c].apply(
                        lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S") if not pd.isnull(a) else '')
                except:
                    raise
        file_data.to_excel(writer, sheet_name='file_data')
        Data.to_excel(writer, sheet_name='Data')

        FitCRCs_df.to_excel(writer, sheet_name='FitCRCs')
        fitother_df.to_excel(writer, sheet_name='fitother')


class Converter:
    """Main converter that holds the FIT > pd.DataFrame and pd.DataFrame"""

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

    def fit_to_dataframes(self, fname: str) -> tuple[pd.DataFrame, pd.DataFrame]:
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
