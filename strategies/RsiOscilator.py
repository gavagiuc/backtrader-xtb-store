from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import talib

class RsiOscilator(Strategy):
    
    uppper_bound = 70
    lower_bound = 30
    rsi_window = 14

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, timeperiod=14)
    
    def next(self):

        if crossover(self.rsi, self.uppper_bound):
            self.position.close()
        
        elif crossover(self.lower_bound, self.rsi):
            self.buy()
