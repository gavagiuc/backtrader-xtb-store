from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import os
import collections
import time
from enum import Enum
import traceback

from datetime import datetime, timedelta, time as dtime
from dateutil.parser import parse as date_parse
import time as _time
#import exchange_calendars
import threading
import asyncio

from .api import XTB as API
import pytz
#import requests
import pandas as pd

import backtrader as bt
from backtrader.metabase import MetaParams
from backtrader.utils.py3 import queue, with_metaclass


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
    '''Singleton class wrapping to control the connections to XTB.

    Params:

      - ``key_id`` (default:``None``): Alpaca API key id

      - ``secret_key`` (default: ``None``): Alpaca API secret key

      - ``paper`` (default: ``False``): use the paper trading environment

      - ``account_tmout`` (default: ``10.0``): refresh period for account
        value/cash refresh
    '''

    BrokerCls = None  # broker class will autoregister
    DataCls = None  # data class will auto register

    params = (
        ('key_id', ''),
        ('secret_key', ''),
        ('paper', False),
        ('account_tmout', 10.0),  # account balance refresh timeout
        ('api_version', None)
    )

    _DTEPOCH = datetime(1970, 1, 1)
    _ENVPRACTICE = 'paper'
    _ENVLIVE = 'live'
    _ENV_PRACTICE_URL = 'wss://ws.xtb.com/demo'
    _ENV_LIVE_URL = 'wss://ws.xtb.com/demo'

    @classmethod
    def getdata(cls, *args, **kwargs):
        '''Returns ``DataCls`` with args, kwargs'''
        return cls.DataCls(*args, **kwargs)

    @classmethod
    def getbroker(cls, *args, **kwargs):
        '''Returns broker with *args, **kwargs from registered ``BrokerCls``'''
        return cls.BrokerCls(*args, **kwargs)

    def __init__(self):
        super(XTBStore, self).__init__()

        self.notifs = collections.deque()  # store notifications for cerebro

        self._env = None  # reference to cerebro for general notifications
        self.broker = None  # broker instance
        self.datas = list()  # datas that have registered over start

        self._orders = collections.OrderedDict()  # map order.ref to oid
        self._ordersrev = collections.OrderedDict()  # map oid to order.ref
        self._transpend = collections.defaultdict(collections.deque)

        if self.p.paper:
            self._oenv = self._ENVPRACTICE
            self.p.base_url = self._ENV_PRACTICE_URL
        else:
            self._oenv = self._ENVLIVE
            self.p.base_url = self._ENV_LIVE_URL
        self.oapi = API(self.p.key_id,
                        self.p.secret_key)

        self._cash = 0.0
        self._value = 0.0
        self._evt_acct = threading.Event()

