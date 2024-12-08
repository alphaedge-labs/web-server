from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.timezone('UTC')

def get_current_time():
    return datetime.now(UTC).replace(tzinfo=None)

def get_current_time_str():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")