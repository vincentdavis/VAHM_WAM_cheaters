import warnings
from datetime import datetime
from typing import Any

warnings.simplefilter(action='ignore', category=FutureWarning)

import fitdecode
import pandas as pd

pd.set_option('mode.chained_assignment', None)


def slots2dict(classobj: object) -> dict:
    "Convert a class object with slots to a dict"
    # {s: getattr(classobj, s, None) for s in classobj.__slots__}
    return {s: getattr(classobj, s, None) for s in classobj.__slots__ if 'unknown_' not in s}


def FieldDefinition2dict(frame: fitdecode.records.FitDefinitionMessage) -> dict:
    "Convert a FieldDefinition to dict"
    frame_dict = {}
    for d in frame.field_defs:
        if 'unknown_' in d.name.lower():
            continue
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
        if 'unknown_' in field.name.lower():
            continue
        try:
            frame_dict[field.name] = frame.get_value(field.name)
        except KeyError:
            frame_dict[field.name] = None
    return frame_dict


def fit2dict(fit_file: str | bytes, from_file=True) -> dict[str, None | dict | list[dict] | set[Any]]:
    """Load a fit file"""
    header = None
    definitions = []
    other_records = []
    events = []
    sessions = []
    activity = None
    records = []
    crcs = None
    other = []
    # def process(fit):
    fit = fitdecode.FitReader(fit_file)
    event = dict()
    columns = set()
    for i, frame in enumerate(fit):
        match frame:
            case fitdecode.records.FitHeader():
                header = (slots2dict(frame))
            case fitdecode.records.FitDefinitionMessage():
                definitions.append(FieldDefinition2dict(frame))
            case fitdecode.records.FitDataMessage():
                if 'unknown_' not in frame.name.lower():
                    match frame.name:
                        case 'event':
                            event = frame2dict(frame)
                            events.append(event)
                        case 'session':
                            sessions.append(frame2dict(frame))
                        case 'activity':
                            activity = frame2dict(frame)
                        case 'record':
                            rec = frame2dict(frame)
                            # rec.update(event)
                            columns.update(rec.keys())
                            records.append(rec)
                        case _:
                            other_records.append(frame2dict(frame))
            case fitdecode.records.FitCRC():
                crcs = slots2dict(frame)
            case _:
                other.append(slots2dict(frame))
    fit_dict = {'header': header, 'definitions': definitions, 'events': events, 'sessions': sessions,
                'activity': activity,
                'other_records': other_records, 'records': records, 'crcs': crcs, 'other': other, 'columns': columns}
    return fit_dict


def fit2df(fit_file: str) -> pd.DataFrame:
    """Load a fit file into a pandas dataframe"""
    fit_dict = fit2dict(fit_file)
    # df = pd.DataFrame(columns=list(fit_dict['columns']))
    df = pd.DataFrame.from_dict(fit_dict['records'])
    df.set_index('timestamp', inplace=True)
    df.dropna(how='all', axis='columns', inplace=True)
    df.dropna(how='all', axis='index', inplace=True)
    return df


def fit2csv(fitfile: str, outfile):
    df = fit2df(fitfile)
    # deal with timezone columns in FitDataMessages_df
    date_columns = df.select_dtypes(include=['datetime64[ns, UTC]']).columns
    for c in date_columns:
        try:
            df[c] = df[c].apply(
                lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S") if not pd.isnull(a) else '')
        except:
            raise
    df.to_csv(outfile)


def fit2excel(fitfile, outfile):
    df = fit2df(fitfile)
    date_columns = df.select_dtypes(include=['datetime64[ns, UTC]']).columns
    for c in date_columns:
        try:
            df[c] = df[c].apply(
                lambda a: datetime.strftime(a, "%Y-%m-%d %H:%M:%S") if not pd.isnull(a) else '')
        except:
            raise
    df.to_excel(outfile)
