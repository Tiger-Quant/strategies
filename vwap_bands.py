import time
import pandas as pd
import datetime as dt
import os
from dotenv import load_dotenv
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce



load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
SYMBOL = "SPY"
QUANTITY = 1

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)


def get_latest_data():
    """
    Fetches the current day's minute data from market open to now.
    """
    now = dt.datetime.now(dt.timezone.utc)
    start_time = now - dt.timedelta(days=5)
    request_params = StockBarsRequest(
        symbol_or_symbols=[SYMBOL], timeframe=TimeFrame.Minute, start=start_time
    )

    bars = data_client.get_stock_bars(request_params)
    df = bars.df
    if df.empty:
        print("No data returned from Alpaca.")
        return df

    df = df.reset_index(level=0, drop=True)
    df.sort_index()

    current_date = df.index.max().date()
    df_today = df[df.index.date == current_date].copy()

    return df_today


def calculate_indicators(df):
    """
    Applies VWAP and bands calculations to dataframe.
    """
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["pv"] = df["typical_price"] * df["volume"]

    df["cum_pv"] = df["pv"].cumsum()
    df["cum_vol"] = df["volume"].cumsum()
    df["vwap"] = df["cum_pv"] / df["cum_vol"]

    rolling_window = 20
    df["std_dev"] = df["close"].rolling(window=rolling_window).std()

    df["upper_band"] = df["vwap"] + (df["std_dev"] * 2)
    df["lower_band"] = df["vwap"] - (df["std_dev"] * 2)

    return df


def get_current_position():
    """
    Returns the current position qty (positive for long, negative for short, 0 for flat)
    """
    try:
        pos = trading_client.get_open_position(SYMBOL)
        return float(pos.qty)
    except:
        return 0.0
    

def execute_trade(signal, current_qty):
    """
    Executes market orders based on signal and current position.
    Signal: 1 (Buy), -1 (Sell/Short), 0 (Hold/Exit)
    """
    if signal == 1 and current_qty <= 0:
        print(f"SIGNAL: LONG. Closing existing {current_qty} and buying {QUANTITY}.")
        trading_client.close_all_positions(cancel_orders=True)
        time.sleep(2)

        req = MarketOrderRequest(symbol=SYMBOL, qty=QUANTITY, side=OrderSide.BUY, time_in_force=TimeInForce.DAY)
        trading_client.submit_order(order_data=req)

    elif signal == -1 and current_qty >= 0:
        print(f"SIGNAL: SHORT. Closing existing {current_qty} and selling {QUANTITY}.")
        trading_client.close_all_positions(cancel_orders=True)
        time.sleep(2)

        req = MarketOrderRequest(symbol=SYMBOL, qty=QUANTITY, side=OrderSide.SELL, time_in_force=TimeInForce.DAY)
        trading_client.submit_order(order_data=req)
    
    elif signal == 0 and current_qty != 0:
        print(f"SIGNAL: EXIT. Closing position.")
        trading_client.close_all_positions(cancel_orders=True)

    else:
        print("No action required.")

def run_bot(dry_run=False):
    print(f"Starting Bot (Dry Run: {dry_run})...")
    
    while True:
        try:
            clock = trading_client.get_clock()
            if not clock.is_open and not dry_run:
                # Calculate time until open
                opening_time = clock.next_open.replace(tzinfo=dt.timezone.utc).timestamp()
                curr_time = clock.timestamp.replace(tzinfo=dt.timezone.utc).timestamp()
                time_to_open = int(opening_time - curr_time) / 60
                
                print(f"Market is closed. Opens in {time_to_open:.0f} minutes. Sleeping for 60s...")
                time.sleep(60)
                continue

            # (If testing on weekend, this fetches Friday's data)
            df = get_latest_data()
            if df.empty:
                print("No data. Sleeping...")
                time.sleep(60)
                continue
                
            df = calculate_indicators(df)
            
            # Analyze Latest Bar
            latest = df.iloc[-1]
            print(f"[{dt.datetime.now().strftime('%H:%M:%S')}] Price: {latest['close']:.2f} | VWAP: {latest['vwap']:.2f} | L: {latest['lower_band']:.2f} | U: {latest['upper_band']:.2f}")

            # Signal Logic
            signal = 0
            if latest['close'] < latest['lower_band']:
                signal = 1  # Long
            elif latest['close'] > latest['upper_band']:
                signal = -1 # Short
            
            current_qty = get_current_position()
            if current_qty > 0 and latest['close'] >= latest['vwap']:
                signal = 0 # Exit Long
            elif current_qty < 0 and latest['close'] <= latest['vwap']:
                signal = 0 # Exit Short

            # Execute
            # In DRY_RUN mode, force execution logic to print, even if market is closed
            if dry_run:
                if signal == 1: print("   [DRY RUN] Would BUY now.")
                elif signal == -1: print("   [DRY RUN] Would SELL SHORT now.")
                elif signal == 0 and current_qty != 0: print("   [DRY RUN] Would EXIT now.")
            else:
                # Real Trading Mode
                if signal != 0:
                     execute_trade(signal, current_qty)

            # Sleep
            time.sleep(60)

        except KeyboardInterrupt:
            print("Bot stopped by user.")
            break
        except Exception as e:
            print(f"Critical Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot(dry_run=True)



# if __name__ == "__main__":
#     try:
#         account = trading_client.get_account()
#         print(f"Connection verified. Buying Power: ${account.buying_power}")
#     except Exception as e:
#         print(f"Connection Failed: {e}")
#         exit()

#     print("Fetching data...")
#     df = get_latest_data()

#     if not df.empty:
#         print(f"Data retrieved. Rows: {len(df)}")
#         print(df.tail(3)[["close", "volume"]])
#     else:
#         print("Dataframe is empty.")

#     print("\nTesting Indicators...")
#     try:
#         df = calculate_indicators(df)
#         last_row = df.iloc[-1]
#         print(f"Indicators Calculated.")
#         print(f"   Close: {last_row['close']}")
#         print(f"   VWAP:  {last_row['vwap']:.2f}")
#         print(f"   Upper: {last_row['upper_band']:.2f}")
#         print(f"   Lower: {last_row['lower_band']:.2f}")

#         if last_row['upper_band'] > last_row['vwap'] > last_row['lower_band']:
#              print("   Logic Check: Bands are correctly surrounding VWAP.")
#         else:
#              print("    Logic Check Failed: VWAP is not between bands.")

#     except Exception as e:
#         print(f"Indicator Calculation Failed: {e}")
#         exit()

#     print("\nTesting Position Check...")
#     qty = get_current_position()
#     print(f"✅ Current SPY Position: {qty}")