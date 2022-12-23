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
    fileinfo = "# Fit File details\n\n"
    for d in fit:
        match d:
            case fitdecode.records.FitHeader():
                fileinfo += f"### Header:\n"
                for k, v in slots2dict(d).items():
                    fileinfo += f"- {k}: {v}\n"
            case fitdecode.records.FitDataMessage():
                if d.name.lower() not in ['record', 'event', 'session', 'activity', 'lap']:
                    if show_unkown or "unknown_" not in d.name.lower():
                        fileinfo += f"\n### Data type: {d.name.upper()}\n"
                        for field in d.fields:
                            if show_unkown or "unknown_" not in field.name.lower():
                                fileinfo += f"- {field.name}: {field.value}\n"
    return fileinfo
