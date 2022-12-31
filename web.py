import fitdecode


def slots2dict(classobj: object) -> dict:
    "Convert a class object with slots to a dict"
    {s: getattr(classobj, s, None) for s in classobj.__slots__}
    return {s: getattr(classobj, s, None) for s in classobj.__slots__}

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


def fitfileinfo(fit, show_unkown=False):
    "Creats a markdown text file object with information about the fit file"
    if fit.__class__ == fitdecode.reader.FitReader:
        pass
    else:
        fit = fitdecode.FitReader(fit)
    records = 0
    record_fields = set()
    events = 0
    sessions = 0
    activitys = 0
    laps = 0
    fileinfo = "# Fit File details\n\n"
    for d in fit:
        match d:
            case fitdecode.records.FitHeader():
                fileinfo += f"### Header:\n"
                for k, v in slots2dict(d).items():
                    fileinfo += f"- {k}: {v}\n"
            case fitdecode.records.FitDataMessage():
                records += 1 if d.name == 'record' else 0
                events += 1 if d.name == 'event' else 0
                sessions += 1 if d.name == 'session' else 0
                activitys += 1 if d.name == 'activity' else 0
                laps += 1 if d.name == 'lap' else 0
                if d.name == 'record':
                    record_fields.update(frame2dict(d).keys())
                if d.name.lower() not in ['record', 'event', 'session', 'activity', 'lap']:
                    if show_unkown or "unknown_" not in d.name.lower():
                        fileinfo += f"\n### Data type: {d.name.upper()}\n"
                        for field in d.fields:
                            if show_unkown or "unknown_" not in field.name.lower():
                                fileinfo += f"- {field.name}: {field.value}\n"
                if d.name == 'activity':
                    fileinfo += f"\n### activity\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"
                if d.name == 'session':
                    fileinfo += f"\n### session\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"
                if d.name == 'lap':
                    fileinfo += f"\n### lap\n"
                    for k, v in frame2dict(d).items():
                        fileinfo += f"- {k}: {v}\n"

    fileinfo += f"\n### Data Records:\n" \
                f"- records: {records}\n" \
                f"- events: {events}\n" \
                f"- sessions: {sessions}\n" \
                f"- activitys: {activitys}\n" \
                f"- laps: {laps}\n"
    fileinfo += f"\n### Record Fields:\n"
    for field in record_fields:
        fileinfo += f"- {field}\n"
    return fileinfo
