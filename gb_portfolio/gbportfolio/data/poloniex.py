import json
import time
import sys
from datetime import datetime
from gbportfolio.constants import *

if sys.version_info[0] == 3:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
else:
    from urllib2 import Request, urlopen
    from urllib import urlencode
    
from hashlib import sha512
from requests import post
from hmac import new as _new

# Possible Commands
PUBLIC_COMMANDS = ['returnTicker', 'return24hVolume', 'returnOrderBook', 'returnTradeHistory', 'returnChartData', 'returnCurrencies', 'returnLoanOrders']
TRADING_COMMANDS = ['returnBalances', 'returnCompleteBalances', 'returnOpenOrders', 'buy', 'sell', 'cancelOrder']

#code from:
#https://github.com/s4w3d0ff/python-poloniex/blob/e7898ae880df166b7dcb740ec57b80d1f164b441/poloniex/__init__.py
#https://github.com/miro-ka/mosquito
#https://github.com/ZhengyaoJiang/PGPortfolio/tree/master/pgportfolio
#https://poloniex.com/support/api/#rest_trading

class Poloniex:
    def __init__(self, APIKey='', Secret=''):
        #self.APIKey = APIKey.encode()
        #self.Secret = Secret.encode()
        self.key = APIKey
        self.secret = Secret
        self._nonce = int("{:.6f}".format(time.time()).replace('.', ''))
        # Conversions
        self.timestamp_str = lambda timestamp=time.time(), format="%Y-%m-%d %H:%M:%S": datetime.fromtimestamp(timestamp).strftime(format)
        self.str_timestamp = lambda datestr=self.timestamp_str(), format="%Y-%m-%d %H:%M:%S": int(time.mktime(time.strptime(datestr, format)))
        self.float_roundPercent = lambda floatN, decimalP=2: str(round(float(floatN) * 100, decimalP))+"%"

        # PUBLIC COMMANDS
        self.marketTicker = lambda x=0: self.api('returnTicker')
        self.marketVolume = lambda x=0: self.api('return24hVolume')
        self.marketStatus = lambda x=0: self.api('returnCurrencies')
        self.marketLoans = lambda coin: self.api('returnLoanOrders',{'currency':coin})
        self.marketOrders = lambda pair='all', depth=10:\
            self.api('returnOrderBook', {'currencyPair':pair, 'depth':depth})
        # !!! main history function:
        self.marketChart = lambda pair, period=DAY, start=time.time()-(WEEK*1), end=time.time(): self.api('returnChartData', {'currencyPair':pair, 'period':period, 'start':start, 'end':end})
        # ! not working
        self.marketTradeHist = lambda pair: self.api('returnTradeHistory',{'currencyPair':pair}) # NEEDS TO BE FIXED ON Poloniex

    # Main Api Function #
    def api(self, command, args={}):
        """
        returns 'False' if invalid command or if no APIKey or Secret is specified (if command is "private")
        returns {"error":"<error message>"} if API error
        """
        if command in PUBLIC_COMMANDS:
            url = 'https://poloniex.com/public?'
            args['command'] = command
            ret = urlopen(Request(url + urlencode(args)))
            return json.loads(ret.read().decode(encoding='UTF-8'))
        elif command in TRADING_COMMANDS:
            ####TODO: test if this works
            payload = {}
            payload['url'] = 'https://poloniex.com/tradingApi'
            args['command'] = command
            args['nonce'] = self.nonce
            # add args to payload
            payload['data'] = args
            
            # sign data with our Secret
            sign = _new(
                self.secret.encode('utf-8'),
                urlencode(args).encode('utf-8'),
                sha512)

            # add headers to payload
            payload['headers'] = {'Sign': sign.hexdigest(),
                                  'Key': self.key}
            print(payload)
            # send the call
            ret = post(**payload)
            print(ret)
            return json.loads(ret.read().decode(encoding='UTF-8'))
        else:
            return False

    @property
    def nonce(self):
        """ Increments the nonce"""
        self._nonce += 42
        return self._nonce