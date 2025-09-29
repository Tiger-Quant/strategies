import os
from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd
import time
import numpy as np

load_dotenv()

API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

# Connect to Alpaca Trading API
trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
account = trading_client.get_account()
print(f"Connection successful. Account status: {account.status}")

# Connect to Alpaca Market Data API and create request
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)

request_params = StockBarsRequest(
    symbol_or_symbols=["SPY"],
    timeframe=TimeFrame.Day,
    start="2022-01-01"
)

bars = data_client.get_stock_bars(request_params)
data = bars.df
print("Successfully fetched historical data for SPY:\n")
print(data.tail())

# Apply SMA logic
# To make it automated, we need to put it in a loop that runs continuously.
# Basic flow:
#   1. Fetch the most recent data
#   2. Calculate the SMA and check for a crossover
#   3. Act if a signal is generated (make trade)
#   4. Wait for a set amount of time before repeating cycle

while True: 
    print(f"Checking for signals at {pd.Timestamp.now(tz='America/Chicago').isoformat()} ---")

    # 1. FETCH DATA (already done in the previous step, assuming 'data' DataFrame exists)
    
    # 2. ANALYZE DATA
    data['SMA50'] = data['close'].rolling(window=50).mean()
    data['Position'] = np.where(data['close'] > data['SMA50'], 1, 0)
    data['Signal'] = data['Position'].diff()
    
    
    # Let's look at the most recent data point
    latest_close = data['close'].iloc[-1]
    latest_signal = data['Signal'].iloc[-1]

    print(f"Latest Close: {latest_close:.2f}")
    print(f"Latest Signal: {latest_signal}")

    # 3. ACT (make trade)
    # Check current position and signal first
    # Alpaca API raises an error if you ask for a position that doesn't exist.
    try:
        position = trading_client.get_open_position('SPY')
        position_exists = True
    except Exception as e:
        position_exists = False

    # IF the signal is "buy" AND we don't have a position, THEN submit a buy order.
    if latest_signal == 1.0 and not position_exists:
        print("Buy signal detected! Submitting market order for 1 share.")
        trading_client.submit_order(
        symbol="SPY",
        qty=1,
        side="buy",
        type="market",
        time_in_force="gtc" # good-til-cancelled
    )
    # IF the signal is "sell" AND we already have a position, THEN sell it.
    elif latest_signal == -1.0 and position_exists:
        print("Sell signal detected! Selling our 1 share.")
        trading_client.submit_order(
        symbol="SPY",
        qty=1,
        side="buy",
        type="market",
        time_in_force="gtc" # good-til-cancelled
    )
    else:
        print("Signal is neutral or position status prevents action. Holding.")
    
    
    # 4. WAIT
    print("Waiting for 60 seconds before the next check...")
    time.sleep(60*60*3) # Pauses the script for 3 hours