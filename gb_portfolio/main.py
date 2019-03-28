import os
import time
from argparse import ArgumentParser
from gbportfolio.tools.utils import create_timespan
import logging
import json
from gbportfolio.constants import *
import gbportfolio.tools.configprocess as conf
from gbportfolio.data.data import GlobalData
from gbportfolio.data.data import CoinsDataframe
from gbportfolio.data.data import LocalData
from gbportfolio.visual.graphs import draw_graph

def build_parser():
    parser = ArgumentParser(description="Default utility for price analysis created by GB."
                , epilog = ("example usage: (tensorflow_gpu) <<location of script>>"
                            + " python main.py --mode make_graph --coinlist"
                            + ' "reversed_USDT,LTC,ETH,XRP,STR,XMR,ZEC,BCHABC"'
                            + " --timespan 10D --period 300"))
    parser.add_argument("--mode",dest="mode",
                        help="prepare_data, make_graph",
                        metavar="MODE", default="train")
    parser.add_argument("--timespan", dest="timespan", 
                        help="Set the start date to current time - selected timespan. Can be 1M, 24H, 10D and others/",
                        type=str)
    parser.add_argument("--period", dest="period", help="override json perriod", default=None)
    parser.add_argument("--coinlist", dest="coinlist", 
                        help='Add the coins to be followed within double quotes, separated by commas. E.g. "BTC,ETH".' + 
                        " Note: If currency other than USDT is used as base currency, to display USDT ratio correctly" +
                        " reversed_USDT (reversed_<currency>) should be used to get the complementary to the base curremcy.",
                        default='', type=str)
    parser.add_argument("--device", dest="device", default="cpu",
                        help="device to be used to train")
    parser.add_argument("--no_volume", 
                    dest="show_volume",
                    action='store_false',
                    #default=False,
                    help="Do NOT show volume as size of points in scatterplots"                
                    )
    return parser
    
def main():
    parser = build_parser()
    options = parser.parse_args()    
    #For logging issues:
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    if not os.path.exists("./" + "train_package"):
        os.makedirs("./" + "train_package")
    if not os.path.exists("./" + "database"):
        os.makedirs("./" + "database")
        
    

    if options.mode == "prepare_data":
        # Check if data has to be downloaded and create pandas DataFrame
        logging.basicConfig(filename='download_data.log',level=logging.DEBUG)
        with open("./gbportfolio/config.json") as file:
            config = json.load(file)
        config = conf.preprocess_config(config)
        start = conf.parse_string_date(config["input"]["start_date"])
        end = conf.parse_string_date(config["input"]["end_date"])
        coinlist = config["input"]["coin_list"]
        base_currency = config["input"]["base_currency"]
        period = config["input"]["period"]
        db_path = os.path.join("./" + "database", base_currency + ".db")
        logging.info("Getting data from %i to %i. Coinlist: %s. Base currency: %s. Period %i"%(start, end, coinlist, base_currency, period))
        data = GlobalData(db_path, start, end, base_currency, coinlist)
        #add data to certain coins if missing
        data.update_all_coins()               
    elif options.mode == "make_graph":
        logging.basicConfig(filename='make_graph.log', level=logging.DEBUG)
        with open("./gbportfolio/config.json") as file:
            config = json.load(file)
        if options.timespan != None:
            start, end = create_timespan(options.timespan)
        else:
            start = conf.parse_string_date(config["input"]["start_date"])
            end = conf.parse_string_date(config["input"]["end_date"])
        if options.coinlist != '':
            coinlist = options.coinlist.upper().split(',')           
        else:
            coinlist = config["input"]["coin_list"]
        base_currency = config["input"]["base_currency"]
        if options.period != None:
            period = int(options.period)
        else:
            period = config["input"]["period"]
        db_path = os.path.join("./" + "database", base_currency + ".db")
        logging.info("Getting data from %i to %i. Coinlist: %s. Base currency: %s. Period %i"%(start, end, coinlist, base_currency, period))
        if period > 900:
            data = GlobalData(db_path, start, end, base_currency, coinlist)
            #add data to certain coins if missing
            data.update_all_coins()
            # Prepare pandas dataframe for learning
            data = CoinsDataframe(data.extract_pandas_dataframe(coinlist=coinlist), start, end, period)
            df = data.get_df()
        else:
            assert end - float(start) <= 2*WEEK
            data = LocalData(start, end, period, base_currency, coinlist)
            data.fill_db()
            df = data.get_db()
        fr = str(int(period/60)) + 'min'
        
        print(type(options.show_volume))
        draw_graph(df, fr, options.show_volume)
        
        
        
                     
if __name__ == "__main__":
    main()