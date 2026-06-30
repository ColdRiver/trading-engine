import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import AverageTrueRange
from src.strategy.base import BaseStrategy
from config.config import Config

class MultiTimeframeStrategy(BaseStrategy):
    def __init__(self, params=None):
        default_params = {
            'rsi_period': 2,
            'rsi_overbought': 51,
            'rsi_oversold': 49,
            'ema_fast': 1,
            'ema_slow': 2,
            'ema_fast_confirm': 1,
            'ema_slow_confirm': 2,
            'macd_fast': 2,
            'macd_slow': 4,
            'macd_signal': 1,
            'atr_period': 2,
            'stop_loss_atr_multiplier': 0.1,
            'take_profit_atr_multiplier': 0.15,
            'risk_per_trade': 0.0005,

        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
    
    def add_indicators(self, df, is_confirm=False):
        df = df.copy()
        
        if is_confirm:
            df['ema_fast'] = EMAIndicator(df['close'], self.params['ema_fast_confirm']).ema_indicator()
            df['ema_slow'] = EMAIndicator(df['close'], self.params['ema_slow_confirm']).ema_indicator()
        else:
            df['ema_fast'] = EMAIndicator(df['close'], self.params['ema_fast']).ema_indicator()
            df['ema_slow'] = EMAIndicator(df['close'], self.params['ema_slow']).ema_indicator()
        
        macd = MACD(df['close'], self.params['macd_fast'], self.params['macd_slow'], self.params['macd_signal'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()
        
        df['rsi'] = RSIIndicator(df['close'], self.params['rsi_period']).rsi()
        
        df['atr'] = AverageTrueRange(df['high'], df['low'], df['close'], self.params['atr_period']).average_true_range()
        
        df = df.dropna()
        
        return df
    
    # def generate_signals(self, df_entry, df_confirm):
    #     df_entry = self.add_indicators(df_entry, is_confirm=False)
    #     df_confirm = self.add_indicators(df_confirm, is_confirm=True)
        
    #     df_entry['signal'] = 0
        
    #     df_confirm_aligned = df_confirm.reindex(df_entry.index, method='ffill')
        
    #     trend_15m = df_confirm_aligned['ema_fast'] - df_confirm_aligned['ema_slow']
        
    #     long_condition = (
    #         (df_entry['ema_fast'] > df_entry['ema_slow']) &
    #         (trend_15m > 0)
    #     )
        
    #     short_condition = (
    #         (df_entry['ema_fast'] < df_entry['ema_slow']) &
    #         (trend_15m < 0)
    #     )
        
    #     df_entry.loc[long_condition, 'signal'] = 1
    #     df_entry.loc[short_condition, 'signal'] = -1
        
    #     return df_entry, df_confirm_aligned

    def generate_signals(self, df_entry, df_confirm):
        df_entry = self.add_indicators(df_entry, is_confirm=False)
        df_confirm = self.add_indicators(df_confirm, is_confirm=True)
        
        df_entry['signal'] = 0
        
        df_confirm_aligned = df_confirm.reindex(df_entry.index, method='ffill')
        
        df_entry.loc[df_entry['ema_fast'] > df_entry['ema_slow'], 'signal'] = 1
        df_entry.loc[df_entry['ema_fast'] < df_entry['ema_slow'], 'signal'] = -1
        
        return df_entry, df_confirm_aligned
    
    def calculate_position_size(self, price, account_balance, volatility):
        risk_amount = account_balance * self.params['risk_per_trade']
        stop_distance = volatility * self.params['stop_loss_atr_multiplier']
        position_size = risk_amount / stop_distance
        max_position = (account_balance * Config.MAX_POSITION_SIZE) / price
        return min(position_size, max_position)
    
    def should_enter_trade(self, df_entry, df_confirm, index):
        if index not in df_entry.index:
            return None, None
        
        signal = df_entry.loc[index, 'signal']
        
        if signal == 1:
            return 'long', df_entry.loc[index, 'close']
        elif signal == -1:
            return 'short', df_entry.loc[index, 'close']
        
        return None, None
    
    def should_exit_trade(self, df_entry, df_confirm, index, entry_price, direction):
        if index not in df_entry.index:
            return False, None, None
        
        current_price = df_entry.loc[index, 'close']
        atr = df_entry.loc[index, 'atr']
        
        stop_loss = self.calculate_stop_loss(entry_price, direction, atr)
        take_profit = self.calculate_take_profit(entry_price, direction, atr)
        
        if direction == 'long':
            if current_price <= stop_loss:
                return True, current_price, 'stop_loss'
            elif current_price >= take_profit:
                return True, current_price, 'take_profit'
        else:
            if current_price >= stop_loss:
                return True, current_price, 'stop_loss'
            elif current_price <= take_profit:
                return True, current_price, 'take_profit'
        
        signal = df_entry.loc[index, 'signal']
        if (direction == 'long' and signal == -1) or (direction == 'short' and signal == 1):
            return True, current_price, 'signal_reversal'
        
        return False, None, None