import pandas as pd
import numpy as np
from binance.client import Client
from datetime import datetime, timedelta
from src.utils.logger import setup_logger

logger = setup_logger('data_utils')

def fetch_historical_data(symbol, interval, start_date, end_date, testnet=False):
    """Fetch historical kline data from Binance."""
    try:
        if testnet:
            client = Client(api_key="", api_secret="", testnet=True)
        else:
            client = Client(api_key="", api_secret="")
        
        klines = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=start_date,
            end_str=end_date
        )
        
        df = pd.DataFrame(klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        logger.info(f"Fetched {len(df)} rows for {symbol} at {interval}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        raise

def resample_timeframe(df, target_timeframe):
    """Resample data to target timeframe."""
    resample_dict = {
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }
    
    resampled = df.resample(target_timeframe).agg(resample_dict).dropna()
    return resampled

def align_timeframes(df_15m, df_1h):
    """Align two dataframes by timestamp."""
    df_1h_reindexed = df_1h.reindex(df_15m.index, method='ffill')
    return df_15m, df_1h_reindexed

def save_trades_to_csv(trades, filepath):
    """Save trades to CSV file."""
    df = pd.DataFrame(trades)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved {len(trades)} trades to {filepath}")

def load_trades_from_csv(filepath):
    """Load trades from CSV file."""
    try:
        df = pd.read_csv(filepath)
        logger.info(f"Loaded {len(df)} trades from {filepath}")
        return df
    except FileNotFoundError:
        logger.warning(f"File not found: {filepath}")
        return pd.DataFrame()
