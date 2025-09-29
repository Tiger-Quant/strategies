import pandas as pd

class SMACrossover:
    '''
    A simple moving average crossover strategy.
    Generates a 'BUY' signal when the short-term SMA crosses above the long-term SMA.
    Generates a 'SELL' signal when the short-term SMA crosses below the long-term SMA.
    '''

    def __init__(self, short_window=20, long_window=50):
        self.short_window = short_window
        self.long_window = long_window

    def generate_signal(self, data: pd.DataFrame) -> str:
        
        if len(data) < self.long_window:
            return 'HOLD'
        
        data['short_sma'] = data['Close'].rolling(window=self.short_window).mean()
        data['long_sma'] = data['Close'].rolling(window=self.long_window).mean()

        latest_short_sma = data['short_sma'].iloc[-1]
        prev_short_sma = data['short_sma'].iloc[-2]
        latest_long_sma = data['long_sma'].iloc[-1]
        prev_long_sma = data['long_sma'].iloc[-2]

        if prev_short_sma <= prev_long_sma and latest_short_sma > latest_long_sma:
            return 'BUY'
        elif prev_short_sma >= prev_long_sma and latest_short_sma < latest_long_sma:
            return 'SELL'
        else:
            return 'HOLD'