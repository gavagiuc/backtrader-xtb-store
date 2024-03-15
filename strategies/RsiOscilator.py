from datetime import datetime
import backtrader as bt

class RsiOscilator(bt.Strategy):
    
    def __init__(self):
        self.uppper_bound = 70
        self.lower_bound = 30
        self.rsi_window = 14

        self.sma = bt.ind.SMA(self.datas[0].close, period=200)
        self.rsi = bt.ind.RSI(self.datas[0].close, period=self.rsi_window)

        self.close_crossover = bt.ind.CrossOver(self.rsi, self.uppper_bound)
        self.buy_signal = bt.ind.CrossOver(self.lower_bound, self.rsi)
    
    def next(self):
        if not self.position:  # not in the market
            if self.buy_signal > 0: 
                self.buy()

        elif  self.close_crossover < 0: 
            self.close()
         
