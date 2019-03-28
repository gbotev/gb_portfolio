import sys
import time
from datetime import datetime

try:
    unicode        # Python 2
except NameError:
    unicode = str  # Python 3

def preprocess_config(config):
    #fill_default(config)
    if sys.version_info[0] == 2:
        return byteify(config)
    else:
        return config


def fill_default(config):
    set_missing(config, "random_seed", 0)
    #fill_layers_default(config["layers"])
    fill_input_default(config["input"])
    #fill_train_config(config["training"])
    
def fill_input_default(input_config):
    set_missing(input_config, "start", time.time() - 60*60*24)
    set_missing(input_config, "end", time.time())
    set_missing(input_config, "portion_reversed", False)
    set_missing(input_config, "market", "poloniex")

    
def set_missing(config, name, value):
    if name not in config:
        config[name] = value


def byteify(input):
    if isinstance(input, dict):
        return {byteify(key): byteify(value)
                for key, value in input.iteritems()}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif isinstance(input, unicode):
        return str(input)
    else:
        return input    
        
def parse_string_date(date_string):
    return time.mktime(datetime.strptime(date_string, "%Y/%m/%d").timetuple())
    
def parse_posix_time(time_linux):
    return datetime.fromtimestamp(time_linux).strftime("%Y/%m/%d %H:%M:%S")