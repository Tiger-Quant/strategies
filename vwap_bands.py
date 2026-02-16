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

# Configuration
load_dotenv()
API_KEY = os.getenv("API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
SYMBOL = "SPY"
QUANTITY = 1

trading_client = TradingClient(API_KEY, SECRET_KEY, paper=True)
data_client = StockHistoricalDataClient(API_KEY, SECRET_KEY)


def get_latest_data():
    """
    Fetches the last five days of minute data to ensure valid rolling calculations.
    Returns empty DataFrame on error.
    """
    try:
        now = dt.datetime.now(dt.timezone.utc)
        start_time = now - dt.timedelta(days=5)
        request_params = StockBarsRequest(
            symbol_or_symbols=[SYMBOL], timeframe=TimeFrame.Minute, start=start_time
        )

        bars = data_client.get_stock_bars(request_params)
        df = bars.df

        if df.empty:
            print("No data returned from Alpaca.")
            return pd.DataFrame()

        # Clean index (Alpaca returns MultiIndex [symbol, timestamp])
        df = df.reset_index(level=0, drop=True)
        df.sort_index()

        return df

    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()


def calculate_indicators(df):
    """
    Applies Intraday VWAP and bands calculations to dataframe.
    """
    df["typical_price"] = (df["high"] + df["low"] + df["close"]) / 3
    df["pv"] = df["typical_price"] * df["volume"]

    # Group by day to reset VWAP at the start of each day.
    df["date"] = df.index.date
    df["cum_pv"] = df.groupby("date")["pv"].cumsum()
    df["cum_vol"] = df.groupby("date")["volume"].cumsum()
    df["vwap"] = df["cum_pv"] / df["cum_vol"]

    # Bands Logic -- rolling 20 min standard deviation
    rolling_window = 20
    df["std_dev"] = df["close"].rolling(window=rolling_window).std()

    df["upper_band"] = df["vwap"] + (df["std_dev"] * 2)
    df["lower_band"] = df["vwap"] - (df["std_dev"] * 2)

    return df


def get_current_position():
    """
    Returns the current position qty (positive for long, negative for short, 0 for flat).
    """
    try:
        pos = trading_client.get_open_position(SYMBOL)
        return float(pos.qty)
    except:
        return 0.0


def execute_trade(signal, current_qty):
    """
    Executes market orders based on signal and current position.
    1 = Buy,
    -1 = Sell/Short,
    0 = Exit,
    None = Hold
    """
    if signal is None:
        return  # Do nothing.

    # Logic: EXIT
    if signal == 0 and current_qty != 0:
        print(f"{dt.datetime.now()} SIGNAL: EXIT. Closing position.")
        try:
            trading_client.close_position(SYMBOL)
        except Exception as e:
            print(f"Error closing position: {e}")

    # Logic: LONG
    elif signal == 1 and current_qty <= 0:
        print(
            f"{dt.datetime.now()} SIGNAL: LONG. Closing position if short and buying {QUANTITY}."
        )
        try:
            trading_client.close_position(SYMBOL)
            time.sleep(2)
        except:
            pass  # No position to close

        req = MarketOrderRequest(
            symbol=SYMBOL,
            qty=QUANTITY,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY,
        )
        trading_client.submit_order(order_data=req)

    # Logic: SHORT
    elif signal == -1 and current_qty >= 0:
        print(
            f"{dt.datetime.now()} SIGNAL: SHORT. Closing position if long and selling {QUANTITY}."
        )
        try:
            trading_client.close_position(SYMBOL)
            time.sleep(2)
        except:
            pass  # No position to close

        req = MarketOrderRequest(
            symbol=SYMBOL,
            qty=QUANTITY,
            side=OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
        )
        trading_client.submit_order(order_data=req)


def run_bot(dry_run=False):
    print(f"Starting Bot (Dry Run: {dry_run})...")

    while True:
        try:
            # Market hours check
            clock = trading_client.get_clock()
            if not clock.is_open and not dry_run:
                opening_time = clock.next_open.replace(
                    tzinfo=dt.timezone.utc
                ).timestamp()
                curr_time = clock.timestamp.replace(tzinfo=dt.timezone.utc).timestamp()
                minutes_to_open = (opening_time - curr_time) / 60
                print(
                    f"Market is closed. Opens in {minutes_to_open:.0f} minutes. Sleeping..."
                )
                time.sleep(60)
                continue

            # Fetch data
            df = get_latest_data()
            if df.empty or len(df) < 20:
                print("Not enough data yet. Sleeping...")
                time.sleep(60)
                continue

            df = calculate_indicators(df)
            latest = df.iloc[-1]

            print(
                f"[{dt.datetime.now().strftime('%H:%M:%S')}] {SYMBOL} | "
                f"Price: {latest['close']:.2f} | "
                f"VWAP: {latest['vwap']:.2f} | "
                f"Lower: {latest['lower_band']:.2f} | "
                f"Upper: {latest['upper_band']:.2f}"
            )

            # Signal Logic
            signal = None

            # Entry conditions
            if latest["close"] < latest["lower_band"]:
                signal = 1  # Enter long
            elif latest["close"] > latest["upper_band"]:
                signal = -1  # Enter short

            # Exit conditions (mean reversion)
            current_qty = get_current_position()
            if current_qty > 0 and latest["close"] >= latest["vwap"]:
                signal = 0  # Exit Long
            elif current_qty < 0 and latest["close"] <= latest["vwap"]:
                signal = 0  # Exit Short

            # Execution
            # In DRY_RUN mode, force execution logic to print, even if market is closed
            if dry_run:
                if signal == 1:
                    print("   [DRY RUN] Would BUY now.")
                elif signal == -1:
                    print("   [DRY RUN] Would SELL SHORT now.")
                elif signal == 0:
                    print("   [DRY RUN] Would EXIT now.")
            else:
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
    run_bot(dry_run=False)
