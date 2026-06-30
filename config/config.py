import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance Testnet API
    BINANCE_TESTNET_API_KEY = os.getenv('BINANCE_TESTNET_API_KEY')
    BINANCE_TESTNET_SECRET_KEY = os.getenv('BINANCE_TESTNET_SECRET_KEY')
    BINANCE_TESTNET_URL = 'https://testnet.binance.vision/api'
    
    # Trading Parameters
    SYMBOL = 'BTCUSDT'
    ENTRY_TIMEFRAME = '1m'
    CONFIRMATION_TIMEFRAME = '1m'
    
    # Risk Management
    RISK_PER_TRADE = 0.001
    MAX_POSITION_SIZE = 0.1
    STOP_LOSS_PERCENT = 0.001
    TAKE_PROFIT_PERCENT = 0.0015
    
    # Backtesting
    BACKTEST_START = '2024-01-01'
    BACKTEST_END = '2024-12-01'
    INITIAL_CAPITAL = 10000
    COMMISSION = 0.001  # 0.1%
    
    # Data paths
    BACKTEST_TRADES_PATH = 'data/backtest_trades.csv'
    LIVE_TRADES_PATH = 'data/live_trades.csv'
