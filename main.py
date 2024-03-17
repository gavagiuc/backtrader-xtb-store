from xtb.api import XTB
from xtb.store import XTBStore
import pandas as pd
import os
import logging
import json
import yaml
from strategies import *
import backtrader as bt

# load config.yaml file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)


ID = os.environ.get("XTB_USER")
PASSWORD = os.environ.get("XTB_PASSWORD")
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

    
    API = XTB(ID, PASSWORD)
    API.login()
    balance = API.get_Balance()
    logging.info(f"balance {balance}")       

    for symbol in config["tickers"]:
        print(symbol)
        # candles = API.get_CandlesRange(period="H1", symbol=ticker, days=60)

        # dataframe = pd.DataFrame.from_dict(candles)
        # # set index for df to DateTime column
        # dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
        # dataframe['volume'] = dataframe['volume'].astype(int)
        # dataframe.set_index('datetime', inplace=True)

        # data = bt.feeds.PandasData(dataname=dataframe)
        
        cerebro = bt.Cerebro()
        cerebro.addstrategy(SmaCross)
        cerebro.broker.setcash(balance)
        
        store = XTBStore(
            key_id=os.environ.get("XTB_USER"),
            secret_key=os.environ.get("XTB_PASSWORD")
        )

        DataFactory = store.getdata  # or use alpaca_backtrader_api.AlpacaData
        if IS_BACKTEST:
            data0 = DataFactory(dataname=symbol,
                                historical=True,
                                fromdate=datetime(2024, 1, 1),
                                todate=datetime(2024, 3, 14),
                                timeframe=bt.TimeFrame.Days,
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
    

    API.logout()
    logging.info("Logged out")
