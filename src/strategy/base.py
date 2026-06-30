from abc import ABC, abstractmethod
import pandas as pd

class BaseStrategy(ABC):
    def __init__(self, params=None):
        self.params = params or {}
        
    @abstractmethod
    def generate_signals(self, df_entry, df_confirm):
        pass
    
    @abstractmethod
    def calculate_position_size(self, price, account_balance, volatility):
        pass
    
    @abstractmethod
    def should_enter_trade(self, df_entry, df_confirm, index):
        pass
    
    @abstractmethod
    def should_exit_trade(self, df_entry, df_confirm, index, entry_price, direction):
        pass
    
    def calculate_stop_loss(self, entry_price, direction, atr):
        if direction == 'long':
            return entry_price - (2 * atr)
        else:
            return entry_price + (2 * atr)
    
    def calculate_take_profit(self, entry_price, direction, atr):
        if direction == 'long':
            return entry_price + (3 * atr)
        else:
            return entry_price - (3 * atr)
