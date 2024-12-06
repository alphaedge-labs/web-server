from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def get_current_time():
    return datetime.now(IST)

def get_current_time_str():
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")