import time
from datetime import datetime
from gbportfolio.constants import *
import random

def get_random_rgb():
    r = random.uniform(0.0, 1.0)
    g = random.uniform(0.0, 1.0)
    b = random.uniform(0.0, 1.0)
    if r + g + b > 1.5:
        (r, g, b) = get_random_rgb()
    return (r, g, b)

def create_timespan(timespan):
    end = time.time()
    try:
        if timespan[-1] == "H":
            start = end - int(timespan[:-1])*HOUR
        if timespan[-1] == "D":
            start = end - int(timespan[:-1])*DAY
        elif timespan[-1] == "W":
            start = end - int(timespan[:-1])*WEEK
        elif timespan[-1] == "M":
            start = end - int(timespan[:-1])*MONTH
        elif timespan[-1] == "Y":
            start = end - int(timespan[:-1])*YEAR
    except Exception as e:
        print(e)
        start = end - 10*DAY
    return start, end
    