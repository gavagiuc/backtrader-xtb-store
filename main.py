from xtb.api import XTB
from xtb.store import XTBStore
 
import pandas as pd
import os
import logging
import json
import yaml
from strategies import *
import backtrader as bt
from datetime import datetime, timedelta
from backtrader_plotting import Bokeh

import pandas as pd
import quantstats

# load config.yaml file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

XTB_ID = os.environ.get("XTB_USER")
XTB_PASSWORD = os.environ.get("XTB_PASSWORD")

# xtb = XTB(XTB_ID, XTB_PASSWORD)
# xtb.login()
# # writte symbols to config file
# symbols = xtb.get_AllSymbols()
# with open("symbols.yaml", "w") as file:
#     json.dumps(symbols, file)


logging.basicConfig(level=logging.INFO)

"""
You have 3 options:
 - backtest (IS_BACKTEST=True, IS_LIVE=False)
 - paper trade (IS_BACKTEST=False, IS_LIVE=False)
 - live trade (IS_BACKTEST=False, IS_LIVE=True)
"""
IS_BACKTEST = True
IS_LIVE = False

if __name__ == "__main__":

    for symbol in config["tickers"]:

        cerebro = bt.Cerebro()
        cerebro.addobserver(bt.observers.DrawDown)
        cerebro.addstrategy(SmaCross)        

        # INITIATE STORE
        store = XTBStore(
            key_id=XTB_ID,
            secret_key=XTB_PASSWORD
        )

        # INITIATE GETDATA
        DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
        if IS_BACKTEST:
            hist_start_date = datetime.now() - timedelta(days=30)

            data0 = DataFactory(dataname=symbol,
                                historical=True,
                                fromdate=datetime(2024, 2, 15, 0, 0),
                                todate=datetime(2024, 3, 15, 0, 0),
                                timeframe=bt.TimeFrame.Minutes,
                                compression=15,
                                data_feed='iex')
        else:
            data0 = DataFactory(dataname=symbol,
                                historical=False,
                                timeframe=bt.TimeFrame.Ticks,
                                backfill_start=False,
                                data_feed='iex'
                                )

            broker = store.getbroker()
            cerebro.setbroker(broker)

        cerebro.adddata(data0)

        cerebro.run()
        cerebro.plot(style='candle')
