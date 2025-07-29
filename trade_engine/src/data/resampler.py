import pandas as pd


def apply_resampler(df, mode="time", **kwargs):
    if mode == "time":
        return time_bar(df, **kwargs)
    elif mode == "range":
        return range_bar(df, **kwargs)
    elif mode == "tick":
        return tick_bar(df, **kwargs)
    else:
        raise ValueError(f"Unsupported resample mode: {mode}")

def time_bar(df: pd.DataFrame, timeframe: str = '5min') -> pd.DataFrame:
    if not {'Open', 'High', 'Low', 'Close', 'Volume'}.issubset(df.columns):
        raise ValueError("OHLCV 데이터가 누락되었습니다.")

    ohlcv = pd.DataFrame()
    ohlcv['Open'] = df['Open'].resample(timeframe).first()
    ohlcv['High'] = df['High'].resample(timeframe).max()
    ohlcv['Low'] = df['Low'].resample(timeframe).min()
    ohlcv['Close'] = df['Close'].resample(timeframe).last()
    ohlcv['Volume'] = df['Volume'].resample(timeframe).sum()

    return ohlcv.dropna()

def range_bar(df: pd.DataFrame, price_column: str = 'Close', range_size: float = 1.0) -> pd.DataFrame:
    bars = []
    last_price = None
    bar = {}

    for i, (ts, row) in enumerate(df.iterrows()):
        price = row[price_column]

        if last_price is None:
            last_price = price
            bar = {
                'timestamp': ts,
                'Open': price,
                'High': price,
                'Low': price,
                'Close': price,
                'Volume': row['Volume']
            }
            continue

        bar['High'] = max(bar['High'], price)
        bar['Low'] = min(bar['Low'], price)
        bar['Close'] = price
        bar['Volume'] += row['Volume']

        if abs(price - bar['Open']) >= range_size:
            bars.append(bar)
            last_price = price
            bar = {
                'timestamp': ts,
                'Open': price,
                'High': price,
                'Low': price,
                'Close': price,
                'Volume': 0.0
            }

    bars_df = pd.DataFrame(bars)
    bars_df.set_index('timestamp', inplace=True)
    return bars_df


def tick_bar(df: pd.DataFrame, price_column: str = 'Close', range_size: float = 1.0) -> pd.DataFrame:
    pass