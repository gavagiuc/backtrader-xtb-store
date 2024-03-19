import backtrader as bt
import backtrader.feed as feed

from .api import XTB 

class XTBData(feed.DataBase):
    params = (
        ('nullvalue', 0.0),
        ('dtformat', '%Y-%m-%d %H:%M:%S'),
        ('historical', False),  # only historical download
        ('backfill_start', True),  # do backfilling at the start
        ('backfill', True),  # do backfilling after the start
    )

    def start(self):
        super(XTBData, self).start()

        # Connect to XTB API and subscribe to data updates for self.p.dataname
        # self.connection = XTBConnection()
        # self.connection.subscribe(self.p.dataname)

    def stop(self):
        super(XTBData, self).stop()

        # Disconnect from XTB API
        # self.connection.unsubscribe(self.p.dataname)
        # self.connection.close()

    def _load(self):
        # This method should be implemented to load data from the XTB API
        # It should return a boolean indicating whether there is more data to load

        # Example:
        # data = self.connection.get_data(self.p.dataname)
        # if data is not None:
        #     self.lines.datetime[0] = date2num(data['datetime'])
        #     self.lines.open[0] = data['open']
        #     self.lines.high[0] = data['high']
        #     self.lines.low[0] = data['low']
        #     self.lines.close[0] = data['close']
        #     self.lines.volume[0] = data['volume']
        #     return True  # there is more data
        # else:
        #     return False  # no more data
