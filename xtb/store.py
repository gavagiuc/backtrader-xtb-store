import backtrader as bt
from datetime import datetime
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import with_metaclass
from .api import XTB

class MetaSingleton(MetaParams):
    '''Metaclass to make a metaclassed class a singleton'''

    def __init__(cls, name, bases, dct):
        super(MetaSingleton, cls).__init__(name, bases, dct)
        cls._singleton = None

    def __call__(cls, *args, **kwargs):
        if cls._singleton is None:
            cls._singleton = (
                super(MetaSingleton, cls).__call__(*args, **kwargs))

        return cls._singleton

class XTBStore(with_metaclass(MetaSingleton, object)):
    '''
    API provider for XTB feed and broker classes.
    '''

    # Supported granularities
    _GRANULARITIES = {
        (bt.TimeFrame.Minutes, 1): '1m',
        (bt.TimeFrame.Minutes, 3): '3m',
        (bt.TimeFrame.Minutes, 5): '5m',
        (bt.TimeFrame.Minutes, 15): '15m',
        (bt.TimeFrame.Minutes, 30): '30m',
        (bt.TimeFrame.Minutes, 60): '1h',
        (bt.TimeFrame.Minutes, 90): '90m',
        (bt.TimeFrame.Minutes, 120): '2h',
        (bt.TimeFrame.Minutes, 180): '3h',
        (bt.TimeFrame.Minutes, 240): '4h',
        (bt.TimeFrame.Minutes, 360): '6h',
        (bt.TimeFrame.Minutes, 480): '8h',
        (bt.TimeFrame.Minutes, 720): '12h',
        (bt.TimeFrame.Days, 1): '1d',
        (bt.TimeFrame.Days, 3): '3d',
        (bt.TimeFrame.Weeks, 1): '1w',
        (bt.TimeFrame.Weeks, 2): '2w',
        (bt.TimeFrame.Months, 1): '1M',
        (bt.TimeFrame.Months, 3): '3M',
        (bt.TimeFrame.Months, 6): '6M',
        (bt.TimeFrame.Years, 1): '1y',
    }

    BrokerCls = None  # broker class will auto register
    DataCls = None  # data class will auto register

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)


    def __init__(self, key_id, secret_key):
        self.xtbapi = XTB(key_id, secret_key)
        self.xtbapi.login()
        balance = self.xtbapi.get_Balance()
        self._cash = balance
        self._value = balance

    def fetch_ohlcv(self, symbol, timeframe, since, fromdate, todate, limit, params={}):
        # print since to tring date
        print('Fetching: {}, TF: {}, From: {}, To: {}'.format(symbol, timeframe, fromdate, todate))

        return self.xtbapi.fetch_ohlcv(symbol, 
                                       timeframe=timeframe, 
                                       since=since, 
                                       limit=limit,
                                       fromdate=fromdate,
                                       todate=todate, 
                                       params=params)

    def get_granularity(self, timeframe, compression):

        granularity = self._GRANULARITIES.get((timeframe, compression))
        
        return granularity

    def fetch_trades(self, symbol):
        return self.xtbapi.fetch_trades(symbol)
