from datetime import datetime

def exp1():
    now = datetime.now()
    return now.strftime("%m/%d/%Y, %H:%M:%S")