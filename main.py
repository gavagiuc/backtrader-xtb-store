from API import XTB
from backtesting import Backtest
import pandas as pd
import os
import logging
import json
import yaml
from strategies import *

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

        df = pd.DataFrame.from_dict(candles, orient='columns')
        # set index for df to DateTime column
        df['DateTime'] = pd.to_datetime(df['DateTime'], infer_datetime_format=True)
        df.set_index('DateTime', inplace=True)

        bt = Backtest(df, RsiOscilator,
              cash=10000, commission=.002,
              exclusive_orders=True)
        stats = bt.optimize(
            uppper_bound=range(50, 85, 5),
            lower_bound=range(10, 45, 5),
            rsi_window=range(10, 30, 2),
            maximize = 'Sharpe Ratio'
        )
        print("=========================STATS===============================")
        print(stats)
        print("===============================================================")
        # output = bt.run()
        # print("=========================BACKTEST===============================")
        # print(output)
        # print("===============================================================")
        bt.plot(filename=f"backtest_{ticker}.html")

    # # save symbols to file as json
    # # Convert symbols to JSON
    # symbols_json = json.dumps(symbols["returnData"])
    # # Save symbols to file
    # with open('/home/cosmin/algotrading-bot/symbols.json', 'w') as file:
    #     file.write(symbols_json)

    

    API.logout()
    logging.info("Logged out")
