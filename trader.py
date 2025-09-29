import alpaca_trade_api as tradeapi
import time
import os

class AlpacaTrader:
    """
    The trading engine that connects to Alpaca, fetches data,
    and executes trades based on signals from a provided strategy.
    """
    def __init__(self, strategy, symbol='SPY', quantity=10, timeframe='15Min'):
        self.api = tradeapi.REST(
            key_id=os.environ['APCA_API_KEY_ID'],
            secret_key=os.environ['APCA_API_SECRET_KEY'],
            base_url=os.environ['APCA_API_BASE_URL'], # Use 'https://paper-api.alpaca.markets' for paper trading
            api_version='v2'
        )
        self.strategy = strategy
        self.symbol = symbol
        self.quantity = quantity
        self.timeframe = timeframe
        # Calculate sleep time in seconds (e.g., 15 minutes)
        self.sleep_interval = 15 * 60 

    def get_market_data(self):
        """Fetches historical bar data for the symbol."""
        # We need more data than the long_window to ensure SMA calculation is accurate
        limit = self.strategy.long_window + 5 
        bars = self.api.get_bars(
            self.symbol,
            self.timeframe,
            limit=limit
        ).df
        return bars

    def run(self):
        """The main loop to run the trading bot."""
        print(f"🤖 Starting trading bot for {self.symbol} with {self.strategy.__class__.__name__}...")
        while True:
            try:
                # 1. Fetch the latest market data
                market_data = self.get_market_data()

                # 2. Ask the strategy for a signal
                signal = self.strategy.generate_signal(market_data)
                print(f"[{time.ctime()}] Signal for {self.symbol}: {signal}")

                # 3. Execute trades based on the signal
                self.execute_trade(signal)
                
                # 4. Wait for the next candle
                print(f"Sleeping for {self.sleep_interval / 60} minutes...")
                time.sleep(self.sleep_interval)

            except Exception as e:
                print(f"An error occurred: {e}")
                time.sleep(self.sleep_interval) # Wait before retrying

    def execute_trade(self, signal):
        """Submits orders to Alpaca based on the trading signal."""
        try:
            position = self.api.get_position(self.symbol)
            has_position = True
        except tradeapi.rest.APIError:
            has_position = False

        if signal == 'BUY' and not has_position:
            print(f"Placing BUY order for {self.quantity} shares of {self.symbol}.")
            self.api.submit_order(
                symbol=self.symbol,
                qty=self.quantity,
                side='buy',
                type='market',
                time_in_force='day'
            )
        elif signal == 'SELL' and has_position:
            print(f"Placing SELL order for {self.quantity} shares of {self.symbol}.")
            self.api.submit_order(
                symbol=self.symbol,
                qty=self.quantity,
                side='sell',
                type='market',
                time_in_force='day'
            )