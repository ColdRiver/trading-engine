import time
import pandas as pd
from datetime import datetime
from src.trading.exchange import BinanceExchange
from src.utils.logger import setup_logger
from src.utils.data import save_trades_to_csv
from config.config import Config

logger = setup_logger('executor')

class TradeExecutor:
    def __init__(self, strategy, exchange, symbol=Config.SYMBOL):
        self.strategy = strategy
        self.exchange = exchange
        self.symbol = symbol
        self.current_position = None
        self.trades = []
        
    def get_market_data(self, interval, limit=100):
        df = self.exchange.get_klines(self.symbol, interval, limit)
        return df
    
    def round_quantity(self, size):
        symbol_info = self.exchange.get_symbol_info(self.symbol)
        if symbol_info:
            lot_size_filter = next(f for f in symbol_info['filters'] if f['filterType'] == 'LOT_SIZE')
            step_size = float(lot_size_filter['stepSize'])
            size = round(size / step_size) * step_size
            size = round(size, 8)
        return size
    
    def execute_trade(self, direction, price, size):
        side = 'BUY' if direction == 'long' else 'SELL'
        
        size = self.round_quantity(size)
        
        order = self.exchange.place_market_order(self.symbol, side, size)
        
        if order:
            logger.info(f"Trade executed: {direction} {size} at {price}")
            return order, size
        else:
            logger.error(f"Failed to execute trade: {direction} {size}")
            return None, size
    
    def close_position(self, price):
        if not self.current_position:
            return None
        
        direction = self.current_position['direction']
        size = self.current_position['size']
        
        side = 'SELL' if direction == 'long' else 'BUY'
        
        size = self.round_quantity(size)
        
        order = self.exchange.place_market_order(self.symbol, side, size)
        
        if order:
            logger.info(f"Position closed: {direction} {size} at {price}")
            return order
        else:
            logger.error(f"Failed to close position")
            return None
    
    def run_live(self, check_interval=60):
        logger.info(f"Starting live trading for {self.symbol}")
        
        while True:
            try:
                df_15m = self.get_market_data(Config.ENTRY_TIMEFRAME, limit=100)
                df_1h = self.get_market_data(Config.CONFIRMATION_TIMEFRAME, limit=100)
                
                if df_15m is None or df_1h is None:
                    logger.warning("Failed to fetch market data")
                    time.sleep(check_interval)
                    continue
                
                df_entry, df_confirm = self.strategy.generate_signals(df_15m, df_1h)
                
                current_index = df_entry.index[-1]
                current_price = df_entry.loc[current_index, 'close']
                logger.info(f"Price: {current_price:.2f} | Signal: {df_entry.loc[current_index, 'signal']}")
                
                if self.current_position is None:
                    direction, entry_price = self.strategy.should_enter_trade(
                        df_entry, df_confirm, current_index
                    )
                    
                    if direction:
                        balance = self.exchange.get_account_balance('USDT')
                        atr = df_entry.loc[current_index, 'atr']
                        position_size = self.strategy.calculate_position_size(
                            entry_price, balance, atr
                        )
                        
                        order, rounded_size = self.execute_trade(direction, entry_price, position_size)
                        
                        if order:
                            self.current_position = {
                                'direction': direction,
                                'entry_price': entry_price,
                                'entry_time': datetime.now(),
                                'size': rounded_size,
                                'order_id': order['orderId']
                            }
                            logger.info(f"Opened {direction} position: {rounded_size} at {entry_price}")
                
                else:
                    should_exit, exit_price, exit_reason = self.strategy.should_exit_trade(
                        df_entry, df_confirm, current_index,
                        self.current_position['entry_price'],
                        self.current_position['direction']
                    )
                    
                    if should_exit:
                        order = self.close_position(exit_price)
                        
                        if order:
                            if self.current_position['direction'] == 'long':
                                pnl = (exit_price - self.current_position['entry_price']) * self.current_position['size']
                            else:
                                pnl = (self.current_position['entry_price'] - exit_price) * self.current_position['size']
                            
                            trade = {
                                'entry_time': self.current_position['entry_time'],
                                'exit_time': datetime.now(),
                                'direction': self.current_position['direction'],
                                'entry_price': self.current_position['entry_price'],
                                'exit_price': exit_price,
                                'size': self.current_position['size'],
                                'pnl': pnl,
                                'exit_reason': exit_reason
                            }
                            
                            self.trades.append(trade)
                            logger.info(f"Closed position: PnL={pnl:.2f}, Reason={exit_reason}")
                            
                            self.current_position = None
                
                time.sleep(check_interval)
            
            except KeyboardInterrupt:
                logger.info("Stopping live trading...")
                break
            except Exception as e:
                logger.error(f"Error in live trading loop: {e}")
                time.sleep(check_interval)
        
        self.save_trades()
    
    def save_trades(self, filepath=None):
        if filepath is None:
            filepath = Config.LIVE_TRADES_PATH
        
        if self.trades:
            save_trades_to_csv(self.trades, filepath)
            logger.info(f"Saved {len(self.trades)} trades to {filepath}")