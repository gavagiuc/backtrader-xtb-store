from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import collections
import json

from backtrader import BrokerBase, OrderBase, Order
from backtrader.position import Position
from backtrader.utils.py3 import queue, with_metaclass

from .store import XTBStore

class MetaXtbBroker(BrokerBase.__class__):
    def __init__(cls, name, bases, dct):
        '''Class has already been created ... register'''
        # Initialize the class
        super(MetaXtbBroker, cls).__init__(name, bases, dct)
        XTBStore.BrokerCls = cls

class XTBBroker(with_metaclass(MetaXtbBroker, BrokerBase)):

    # TODO: MAP TO XTB ORDER TYPES
    order_types = {Order.Market: 'market',
                  Order.Limit: 'limit',
                  Order.Stop: 'stop',
                  Order.StopLimit: 'stop limit'}


    def __init__(self, broker_mapping=None, debug=False, **kwargs):
        super(XTBBroker, self).__init__()
        if broker_mapping is not None:
            try:
                self.order_types = broker_mapping['order_types']
            except KeyError:  # Might not want to change the order types
                pass
            try:
                self.mappings = broker_mapping['mappings']
            except KeyError:  # might not want to change the mappings
                pass
            
        self.store = XTBStore(**kwargs)
        self.open_orders = list()
        self.startingcash = self.store._cash
        self.startingvalue = self.store._value
        self.use_order_params = True

        self.notifs = queue.Queue()  # holds orders which are notified

    def get_balance(self):
        # API = XTB(XTB_ID, XTB_PASSWORD)
        # API.login()
        # balance = API.get_Balance()
        # logging.info(f"balance {balance}")
        self.store.get_balance()
        self.cash = self.store._cash
        self.value = self.store._value
        return self.cash, self.value

    def getcash(self):
        # Get cash seems to always be called before get value
        # Therefore it makes sense to add getbalance here.
        # return self.store.getcash(self.currency)
        self.cash = self.store._cash
        return self.cash

    def getvalue(self, datas=None):
        # return self.store.getvalue(self.currency)
        self.value = self.store._value
        return self.value

    def get_notification(self):
        try:
            return self.notifs.get(False)
        except queue.Empty:
            return None

    def notify(self, order):
        self.notifs.put(order)


    def getposition(self, data, clone=True):
        # return self.o.getposition(data._dataname, clone=clone)
        pos = self.positions[data._dataname]
        if clone:
            pos = pos.clone()
        return pos

    def next(self):
        print('Broker next() called')
        for o_order in list(self.open_orders):
            oID = o_order.ccxt_order['id']
            # Print debug before fetching so we know which order is giving an
            # issue if it crashes
            if self.debug:
                print('Fetching Order ID: {}'.format(oID))
            # Get the order
            ccxt_order = self.store.fetch_order(oID, o_order.data.p.dataname)
            # Check for new fills
            if 'trades' in ccxt_order and ccxt_order['trades'] is not None:
                for fill in ccxt_order['trades']:
                    if fill not in o_order.executed_fills:
                        o_order.execute(fill['datetime'], fill['amount'], fill['price'],
                                        0, 0.0, 0.0,
                                        0, 0.0, 0.0,
                                        0.0, 0.0,
                                        0, 0.0)
                        o_order.executed_fills.append(fill['id'])
            if self.debug:
                print(json.dumps(ccxt_order, indent=self.indent))
            # Check if the order is closed
            if ccxt_order[self.mappings['closed_order']['key']] == self.mappings['closed_order']['value']:
                pos = self.getposition(o_order.data, clone=False)
                pos.update(o_order.size, o_order.price)
                o_order.completed()
                self.notify(o_order)
                self.open_orders.remove(o_order)
                self.get_balance()
            # Manage case when an order is being Canceled from the Exchange
            #  from https://github.com/juancols/bt-ccxt-store/
            if ccxt_order[self.mappings['canceled_order']['key']] == self.mappings['canceled_order']['value']:
                self.open_orders.remove(o_order)
                o_order.cancel()
                self.notify(o_order)