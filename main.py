from API import XTB
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

if __name__ == "__main__":

    
    API = XTB(ID, PASSWORD)
    API.login()
    balance = API.get_Balance()
    logging.info(f"balance {balance}")       

    for ticker in config["tickers"]:
        print(ticker)
        candles = API.get_CandlesRange(period="H1", symbol=ticker, days=60)

        dataframe = pd.DataFrame.from_dict(candles)
        # set index for df to DateTime column
        dataframe['datetime'] = pd.to_datetime(dataframe['datetime'])
        dataframe['volume'] = dataframe['volume'].astype(int)
        dataframe.set_index('datetime', inplace=True)

        data = bt.feeds.PandasData(dataname=dataframe)
        
        cerebro = bt.Cerebro()
        cerebro.broker.setcash(balance)
        cerebro.adddata(data)
        cerebro.addstrategy(SmaCross)
        cerebro.run()
        cerebro.plot()

    

    API.logout()
    logging.info("Logged out")
