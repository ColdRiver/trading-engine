from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
from src.utils.logger import setup_logger
from config.config import Config

logger = setup_logger('exchange')

class BinanceExchange:
    def __init__(self, api_key=None, secret_key=None, testnet=True):
        self.api_key = api_key or Config.BINANCE_TESTNET_API_KEY
        self.secret_key = secret_key or Config.BINANCE_TESTNET_SECRET_KEY
        self.testnet = testnet
        
        try:
            if testnet:
                self.client = Client(self.api_key, self.secret_key, testnet=True)
                self.client.API_URL = 'https://testnet.binance.vision/api'
            else:
                self.client = Client(self.api_key, self.secret_key)
            
            logger.info(f"Connected to Binance {'Testnet' if testnet else 'Live'}")
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            raise
    
    def get_account_balance(self, asset='USDT'):
        try:
            balance = self.client.get_asset_balance(asset=asset)
            return float(balance['free'])
        except BinanceAPIException as e:
            logger.error(f"Error getting balance: {e}")
            return 0
    
    def get_current_price(self, symbol):
        try:
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_klines(self, symbol, interval, limit=100):
        try:
            klines = self.client.get_klines(symbol=symbol, interval=interval, limit=limit)
            
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df[['open', 'high', 'low', 'close', 'volume']]
        
        except BinanceAPIException as e:
            logger.error(f"Error fetching klines: {e}")
            return None
    
    def place_market_order(self, symbol, side, quantity):
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            logger.info(f"Market order placed: {side} {quantity} {symbol}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(self, symbol, side, quantity, price):
        try:
            order = self.client.create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                timeInForce='GTC',
                quantity=quantity,
                price=price
            )
            logger.info(f"Limit order placed: {side} {quantity} {symbol} at {price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    def get_order_status(self, symbol, order_id):
        try:
            order = self.client.get_order(symbol=symbol, orderId=order_id)
            return order
        except BinanceAPIException as e:
            logger.error(f"Error getting order status: {e}")
            return None
    
    def cancel_order(self, symbol, order_id):
        try:
            result = self.client.cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order {order_id} cancelled")
            return result
        except BinanceAPIException as e:
            logger.error(f"Error cancelling order: {e}")
            return None
    
    def get_symbol_info(self, symbol):
        try:
            info = self.client.get_symbol_info(symbol)
            return info
        except BinanceAPIException as e:
            logger.error(f"Error getting symbol info: {e}")
            return None
