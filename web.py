import fitdecode


def slots2dict(classobj: object) -> dict:
    "Convert a class object with slots to a dict"
    {s: getattr(classobj, s, None) for s in classobj.__slots__}
    return {s: getattr(classobj, s, None) for s in classobj.__slots__}


def fitfileinfo(fit, show_unkown=False):
    "Creats a markdown text file object with information about the fit file"
    if fit.__class__ == fitdecode.reader.FitReader:
        pass
    else:
        fit = fitdecode.FitReader(fit)
    records = 0
    record_fields = []
    events = 0
    sessions = 0
    activitys = 0
    lapss = 0
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
                lapss += 1 if d.name == 'lap' else 0
                # if d.name == 'record':
                #     record_fields += [f for f in d.fields if f not in record_fields]

                if d.name.lower() not in ['record', 'event', 'session', 'activity', 'lap']:
                    if show_unkown or "unknown_" not in d.name.lower():
                        fileinfo += f"\n### Data type: {d.name.upper()}\n"
                        for field in d.fields:
                            if show_unkown or "unknown_" not in field.name.lower():
                                fileinfo += f"- {field.name}: {field.value}\n"

        fileinfo += f"### Data Records:\n" \
                    f"- records: {records}\n" \
                    f"- events: {events}\n" \
                    f"- sessions: {sessions}\n" \
                    f"- activitys: {activitys}\n" \
                    f"- laps: {lapss}\n"
        # fileinfo += f
    return fileinfo
