from strategy import SmaCrossover
from trader import AlpacaTrader

if __name__ == "__main__":
    # --- Configuration ---
    # Set your Alpaca API credentials as environment variables
    # For example, in your terminal:
    # export APCA_API_KEY_ID='YOUR_KEY_ID'
    # export APCA_API_SECRET_KEY='YOUR_SECRET_KEY'
    # export APCA_API_BASE_URL='https://paper-api.alpaca.markets'

    SYMBOL_TO_TRADE = "AAPL"  # Ticker symbol you want to trade
    TRADE_QUANTITY = 5       # Number of shares to trade
    
    # 1. Instantiate your desired strategy
    # This is the "plug-in" part. To use a different strategy,
    # you would simply instantiate a different strategy class here.
    sma_strategy = SmaCrossover(short_window=20, long_window=50)

    # 2. Instantiate the trader engine with your strategy
    trader_bot = AlpacaTrader(
        strategy=sma_strategy,
        symbol=SYMBOL_TO_TRADE,
        quantity=TRADE_QUANTITY,
        timeframe='15Min' # Options: 1Min, 5Min, 15Min, 1H, 1D
    )
    
    # 3. Run the bot!
    trader_bot.run()