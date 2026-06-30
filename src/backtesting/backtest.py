import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.utils.data import save_trades_to_csv
from config.config import Config

logger = setup_logger('backtest')

class Backtester:
    def __init__(self, strategy, df_entry, df_confirm, initial_capital=10000, commission=0.001):
        self.strategy = strategy
        self.df_entry = df_entry
        self.df_confirm = df_confirm
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.commission = commission
        self.trades = []
        self.positions = []
        self.equity_curve = []
        
    def run(self):
        logger.info("Starting backtest...")
        
        df_entry_signals, df_confirm_aligned = self.strategy.generate_signals(
            self.df_entry, self.df_confirm
        )
        
        self.df_entry = df_entry_signals
        self.df_confirm = df_confirm_aligned
        
        current_position = None
        
        for i, index in enumerate(self.df_entry.index):
            if current_position is None:
                direction, entry_price = self.strategy.should_enter_trade(
                    self.df_entry, self.df_confirm, index
                )
                
                if direction:
                    atr = self.df_entry.loc[index, 'atr']
                    position_size = self.strategy.calculate_position_size(
                        entry_price, self.capital, atr
                    )
                    
                    current_position = {
                        'direction': direction,
                        'entry_price': entry_price,
                        'entry_time': index,
                        'size': position_size,
                        'entry_capital': self.capital
                    }
                    
                    logger.info(f"ENTER {direction.upper()} at {entry_price} | Size: {position_size:.4f}")
            
            else:
                should_exit, exit_price, exit_reason = self.strategy.should_exit_trade(
                    self.df_entry, self.df_confirm, index,
                    current_position['entry_price'], current_position['direction']
                )
                
                if should_exit:
                    if current_position['direction'] == 'long':
                        pnl = (exit_price - current_position['entry_price']) * current_position['size']
                    else:
                        pnl = (current_position['entry_price'] - exit_price) * current_position['size']
                    
                    commission_cost = (current_position['entry_price'] * current_position['size'] * self.commission +
                                     exit_price * current_position['size'] * self.commission)
                    pnl -= commission_cost
                    
                    self.capital += pnl
                    
                    trade = {
                        'entry_time': current_position['entry_time'],
                        'exit_time': index,
                        'direction': current_position['direction'],
                        'entry_price': current_position['entry_price'],
                        'exit_price': exit_price,
                        'size': current_position['size'],
                        'pnl': pnl,
                        'pnl_percent': (pnl / current_position['entry_capital']) * 100,
                        'exit_reason': exit_reason,
                        'commission': commission_cost
                    }
                    
                    self.trades.append(trade)
                    logger.info(f"EXIT {current_position['direction'].upper()} at {exit_price} | PnL: {pnl:.2f} | Reason: {exit_reason}")
                    
                    current_position = None
            
            self.equity_curve.append({
                'timestamp': index,
                'equity': self.capital
            })
        
        logger.info(f"Backtest completed. Total trades: {len(self.trades)}")
        return self.get_results()
    
    def get_results(self):
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'total_return': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'final_capital': self.capital,
                'trades': []
            }
        
        df_trades = pd.DataFrame(self.trades)
        
        winning_trades = len(df_trades[df_trades['pnl'] > 0])
        losing_trades = len(df_trades[df_trades['pnl'] < 0])
        win_rate = (winning_trades / len(df_trades)) * 100 if len(df_trades) > 0 else 0
        
        total_pnl = df_trades['pnl'].sum()
        total_return = ((self.capital - self.initial_capital) / self.initial_capital) * 100
        
        avg_win = df_trades[df_trades['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        results = {
            'total_trades': len(df_trades),
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'total_return': total_return,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'final_capital': self.capital,
            'trades': self.trades
        }
        
        return results
    
    def save_trades(self, filepath=None):
        if filepath is None:
            filepath = Config.BACKTEST_TRADES_PATH
        
        if self.trades:
            save_trades_to_csv(self.trades, filepath)