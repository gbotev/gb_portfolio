import pandas as pd
import datetime as dt
import matplotlib.pyplot as plt
from gbportfolio.tools.utils import get_random_rgb
from gbportfolio.constants import *

def draw_graph(df, fr='30min', show_volume=True):
    df =df.set_index(['coin', 'date'])
    #convert index to datetime
    df.index = df.index.set_levels([df.index.levels[0], pd.to_datetime(df.index.levels[1], unit='s')])
    df = df.sort_index()
    coinlist = list(set(df.index.get_level_values(0)))
    #period = int((df.loc[coinlist[0]].index[1] -  df.loc[coinlist[0]].index[0]).total_seconds())
    #print("storage period is", period, "freq period is:", fr)
    #get the time of last open price for each index
    last_open_times = {c : df.loc[c].index.max() for c in coinlist}
    last_open_prices = {c : df.loc[(c, last_open_times[c])]['open'] for c in coinlist}
    first_open_times = {c : df.loc[c].index.min() for c in coinlist}
    first_open_prices = {c : df.loc[(c, first_open_times[c])]['open'] for c in coinlist}
    first_volume = {c : df.loc[(c, first_open_times[c]):(
                    c, first_open_times[c]+dt.timedelta(
                    seconds=12*60*60))]['volume'].mean() for c in coinlist}
    total_first_volume = 0
    counter = 0
    for v in first_volume.values():
        total_first_volume += v
        counter += 1
    mean_total_volume = total_first_volume/counter
    #TODO: convert all prints to logs
    print("mean volume is:", mean_total_volume)
    df2 = pd.DataFrame()

    df2['high'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).max()['high']
    df2['low'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).min()['low']
    df2['open'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).first()['open']
    df2['close'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).last()['close']
    df2['volume'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).sum()['volume']
   
    high = pd.DataFrame()
    low = pd.DataFrame()
    open = pd.DataFrame()
    close = pd.DataFrame()
    vol = pd.DataFrame()
    colormap = {}
    for c in coinlist:
        high[c] = df2.loc[c]['high'].div(first_open_prices[c], axis=0)
        low[c] = df2.loc[c]['low'].div(first_open_prices[c], axis=0)
        open[c] = df2.loc[c]['open'].div(first_open_prices[c], axis=0)
        close[c] = df2.loc[c]['close'].div(first_open_prices[c], axis=0)
        vol[c] = df2.loc[c]['volume'].div(mean_total_volume, axis=0)
        vol[c] = vol[c].rolling(12).mean()
        if c in COLORS.keys():
            colormap[c] = COLORS[c]
        else:
            colormap[c] = get_random_rgb()
    #data = {'ETH':'g', 'ZEC':'m', 'LTC':'y', 'XRP':'r', 'reversed_USDT':'b', 'BCHABC':'c'}
    for c in colormap.keys():
        if show_volume:
            plt.scatter(open.index, open[c], s=(2*(vol[c]+1)**2), c=colormap[c])
        plt.yscale('log')
        plt.plot(open.index, open[c], c=colormap[c])
        #plt.scatter(open.index, high[c], s=(vol[c]+1)**2, c=data[c])
        #plt.scatter(open.index, low[c], s=(vol[c]+1)**2, c=data[c])
    first_key = coinlist[0]
    plt.xlim(first_open_times[first_key], last_open_times[first_key])
    #plot horizontal line on y
    plt.axhline(y=1, color='k', linestyle='-')
    plt.legend(coinlist)
    plt.show()   
    
    
