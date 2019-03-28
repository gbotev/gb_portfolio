from __future__ import division,absolute_import,print_function
import numpy as np
import pandas as pd
import sqlite3
import logging
from datetime import datetime
import json

from gbportfolio.data.poloniex import Poloniex

    
class GlobalData:
    '''
    This class is used to handle the global database (sqlite3).
        - update_all_coins() is used to get data for coins specified in JSON for the dates specified there.
        - extract_pandas_dataframe() returns a dataframe snapshot of the database for the chosen period
    '''
    def __init__(self, db_path, start, end, base_currency, coinlist):
        self._initialize_db(db_path)
        self.db_path = db_path
        self.start = start
        self.end = end
        self.base_currency = base_currency
        self.coinlist = coinlist
        self.__storage_period = 1800
        #TODO: add possibility for trading API
        self.polo = Poloniex()
        self.db = pd.DataFrame()

    def _initialize_db(self, path):
        with sqlite3.connect(path) as connection:
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS History (date INTEGER,'
                           ' coin varchar(20), high FLOAT, low FLOAT,'
                           ' open FLOAT, close FLOAT, volume FLOAT, '
                           ' quoteVolume FLOAT, weightedAverage FLOAT,'
                           'PRIMARY KEY (date, coin));')
            connection.commit()
            
            
    def _get_chart_until_success(self, polo, pair, start, period, end):
        is_connect_success = False
        chart = {}
        while not is_connect_success:
            try:
                chart = polo.marketChart(pair=pair, start=int(start), period=int(period), end=int(end))
                is_connect_success = True
            except Exception as e:
                print(e)
        return chart
        
    # add new history data into the database
    def _update_data(self, coin):
        connection = sqlite3.connect(self.db_path)
        try:
            cursor = connection.cursor()
            min_date = cursor.execute('SELECT MIN(date) FROM History WHERE coin=?;', (coin,)).fetchall()[0][0]
            max_date = cursor.execute('SELECT MAX(date) FROM History WHERE coin=?;', (coin,)).fetchall()[0][0]

            if min_date==None or max_date==None:
                self.__fill_data(self.start, self.end, coin, cursor)
            else:
                #if max_date+10*self.__storage_period<self.end:
                if max_date+self.__storage_period<self.end:
                    self.__fill_data(max_date + self.__storage_period, self.end, coin, cursor)
                if min_date>self.start:
                    self.__fill_data(self.start, min_date - self.__storage_period - 1, coin, cursor)
            # if there is no data
        finally:
            connection.commit()
            connection.close()
            
    def update_all_coins(self):
        for coin in self.coinlist:
            self._update_data(coin)
            
    def __fill_data(self, start, end, coin, cursor):
        if 'reversed_' in coin.lower():
            pair = coin[len('reversed_'):] + "_" + self.base_currency
        else:
            pair = self.base_currency + "_" + coin
        chart = self._get_chart_until_success(
            self.polo,
            pair=pair,
            start=start,
            end=end,
            period=self.__storage_period)
        logging.info("fill %s data from %s to %s"%(coin, datetime.fromtimestamp(start).strftime('%Y-%m-%d %H:%M'),
                                            datetime.fromtimestamp(end).strftime('%Y-%m-%d %H:%M')))
        for c in chart:
            try: 
                c["date"] > 0
            except Exception as e:
                print("If not using USDT or USDC as base pair, please specify USDT as reversed_USDT")
            if c["date"] > 0:
                if c['weightedAverage'] == 0:
                    weightedAverage = c['close']
                else:
                    weightedAverage = c['weightedAverage']

                #NOTE here the USDT is in reversed order
                if 'reversed_' in coin.lower():
                    cursor.execute('INSERT INTO History VALUES (?,?,?,?,?,?,?,?,?)',
                        (c['date'],coin,1.0/c['low'],1.0/c['high'],1.0/c['open'],
                        1.0/c['close'],c['quoteVolume'],c['volume'],
                        1.0/weightedAverage))
                else:
                    cursor.execute('INSERT INTO History VALUES (?,?,?,?,?,?,?,?,?)',
                                   (c['date'],coin,c['high'],c['low'],c['open'],
                                    c['close'],c['volume'],c['quoteVolume'],
                                    weightedAverage))
                                    
    def get_graphs_data():
            df = self.get_db().copy()
            df = df.set_index(['coin', 'date'])
            #convert index to datetime
            df.index = df.index.set_levels([df.index.levels[0], pd.to_datetime(df.index.levels[1], unit='s')])
            df = df.sort_index()
            coinlist = list(set(df.index.get_level_values(0)))
            assert coinlist == self.coinlist
            last_open_times = {c : df.loc[c].index.max() for c in coinlist}
            assert last_open_times[c[0]] == self.end
            last_open_prices = {c : df.loc[(c, last_open_times[c])]['open'] for c in coinlist}
            first_open_times = {c : df.loc[c].index.min() for c in coinlist}
            assert first_open_times[c[0]] == self.start
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
            logging.log("Mean volume is {}".format(mean_total_volume))
            df2 = pd.DataFrame()

            df2['high'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).max()['high']
            df2['low'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).min()['low']
            df2['open'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).first()['open']
            df2['close'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).last()['close']
            df2['volume'] = df.groupby([df.index.get_level_values(0)] + [pd.Grouper(freq=fr, level=-1)]).sum()['volume']
           
            return df2
            
            #TODO:
            # high = pd.DataFrame()
            # low = pd.DataFrame()
            # open = pd.DataFrame()
            # close = pd.DataFrame()
            # vol = pd.DataFrame()
            # colormap = {}
            # for c in coinlist:
                # high[c] = df2.loc[c]['high'].div(first_open_prices[c], axis=0)
                # low[c] = df2.loc[c]['low'].div(first_open_prices[c], axis=0)
                # open[c] = df2.loc[c]['open'].div(first_open_prices[c], axis=0)
                # close[c] = df2.loc[c]['close'].div(first_open_prices[c], axis=0)
                # vol[c] = df2.loc[c]['volume'].div(mean_total_volume, axis=0)
                # vol[c] = vol[c].rolling(12).mean()
                # if c in COLORS.keys():
                    # colormap[c] = COLORS[c]
                # else:
                    # colormap[c] = get_random_rgb()
                    
                    
                    
                                    
    def extract_pandas_dataframe(self, coinlist=None, start=None, end=None):
        connection = sqlite3.connect(self.db_path)        
        if start == None:
            start = self.start
        if end == None:
            end = self.end
        if coinlist == None:
            return pd.read_sql_query("SELECT * FROM History WHERE date >= ? AND date <= ?;", 
                                    connection, params=[start, end])
        else:
            return pd.read_sql_query("SELECT * FROM History WHERE date >= ? AND date <= ? " +
                                    "AND coin IN ({seq})".format(seq=','.join(['?']*len(coinlist))),
                                    connection, params=[start, end] + coinlist)
    
    def get_db(self):
        self.db = self.extract_pandas_dataframe()
        return self.db
    
                                  
                                  
class LocalData(GlobalData):
    """
    This class is used for storing very short ticks (should be 5M or 15M) in ram instead in DB.
    Used for playing with recent data (horizon < 1W)
    """
    def __init__(self, start, end, period, base_currency, coinlist):
        assert period in [300, 900]
        self.db = pd.DataFrame()
        self.start = start
        self.end = end
        self.period = period
        self.base_currency = base_currency
        self.coinlist = coinlist
        
    def fill_db(self):
        polo = Poloniex()
        for c in self.coinlist:
            if 'reversed_' in c.lower():
                pair = c[9:] + "_" + self.base_currency
            else:
                pair = self.base_currency + "_" + c
            db = pd.DataFrame(self._get_chart_until_success(polo, pair, self.start, self.period, self.end))
            db['coin'] = c
            if 'reversed_' in c.lower():
                db['high'] = 1/db['low']
                db['low'] = 1/db['high']
                db['open'] = 1/db['open']
                db['close'] = 1/db['close']
                db['temp_volume'] = db['volume']
                db['volume'] = db['quoteVolume']
                db['quoteVolume'] = db['temp_volume']
                db.drop(['temp_volume'], axis=1, inplace=True)
            self.db = pd.concat([self.db, db])
        
                
    def get_db(self):
        return self.db
                                    
                                    
class CoinsDataframe:
    def __init__(self, df, start, end, period):
        self.df = df
        self.start = start
        self.end = end
        self.period = period
        self.coin_counts = self._get_unique_coin_records()
        
    def get_df(self):
        return self.df
        
    def get_coin_counts(self):
        return self.coin_counts
        
    def _get_unique_coin_records(self):
        '''
        returns the count of records for each coin in the database (if it is the same).
        logs if there is a value with different count
        '''
        coin_counts = self.df.groupby('coin')['date'].nunique()
        count = 0
        for i in range(len(coin_counts)):
            if count == 0:
                count = coin_counts[i]
            else:
                if count != coin_counts[i]:
                    logging.debug("Coins have different counts")
                    return coin_counts
        return coin_counts