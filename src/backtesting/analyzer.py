import pandas as pd
import numpy as np
from src.utils.logger import setup_logger
from src.utils.data import load_trades_from_csv
from config.config import Config

logger = setup_logger('analyzer')

class TradeAnalyzer:
    def __init__(self, backtest_trades=None, live_trades=None):
        self.backtest_trades = backtest_trades
        self.live_trades = live_trades
    
    def load_trades_from_files(self, backtest_path=None, live_path=None):
        if backtest_path:
            self.backtest_trades = load_trades_from_csv(backtest_path)
        if live_path:
            self.live_trades = load_trades_from_csv(live_path)
    
    def calculate_metrics(self, trades_df):
        if isinstance(trades_df, list):
            trades_df = pd.DataFrame(trades_df)
        
        if trades_df.empty or len(trades_df) == 0:
            return {}
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['pnl'] > 0])
        losing_trades = len(trades_df[trades_df['pnl'] < 0])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['pnl'].sum()
        avg_pnl = trades_df['pnl'].mean()
        
        avg_win = trades_df[trades_df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if losing_trades > 0 and avg_loss != 0 else 0
        
        max_win = trades_df['pnl'].max()
        max_loss = trades_df['pnl'].min()
        
        cumulative_pnl = trades_df['pnl'].cumsum()
        running_max = cumulative_pnl.cummax()
        drawdown = cumulative_pnl - running_max
        max_drawdown = drawdown.min()
        
        metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl': total_pnl,
            'avg_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'max_win': max_win,
            'max_loss': max_loss,
            'max_drawdown': max_drawdown
        }
        
        return metrics
    
    def compare_trades(self):
        if self.backtest_trades is None or self.live_trades is None:
            logger.warning("Both backtest and live trades required for comparison")
            return None
        
        backtest_metrics = self.calculate_metrics(self.backtest_trades)
        live_metrics = self.calculate_metrics(self.live_trades)
        
        comparison = {
            'backtest': backtest_metrics,
            'live': live_metrics,
            'differences': {}
        }
        
        for key in backtest_metrics.keys():
            if key in live_metrics:
                diff = live_metrics[key] - backtest_metrics[key]
                comparison['differences'][key] = diff
        
        return comparison
    
    def print_metrics(self, metrics, title="Trade Metrics"):
        print(f"\n{'='*50}")
        print(f"{title}")
        print(f"{'='*50}")
        
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        
        print(f"{'='*50}\n")
    
    def generate_report(self, output_path=None):
        report = []
        
        if self.backtest_trades is not None:
            if isinstance(self.backtest_trades, list):
                self.backtest_trades = pd.DataFrame(self.backtest_trades)
            
            if not self.backtest_trades.empty:
                backtest_metrics = self.calculate_metrics(self.backtest_trades)
                report.append("BACKTEST RESULTS")
                report.append("="*50)
                for key, value in backtest_metrics.items():
                    report.append(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
                report.append("")
        
        if self.live_trades is not None:
            if isinstance(self.live_trades, list):
                self.live_trades = pd.DataFrame(self.live_trades)
            
            if not self.live_trades.empty:
                live_metrics = self.calculate_metrics(self.live_trades)
                report.append("LIVE TRADING RESULTS")
                report.append("="*50)
                for key, value in live_metrics.items():
                    report.append(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
                report.append("")
        
        if self.backtest_trades is not None and self.live_trades is not None:
            comparison = self.compare_trades()
            if comparison:
                report.append("COMPARISON (Live - Backtest)")
                report.append("="*50)
                for key, value in comparison['differences'].items():
                    report.append(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        
        report_text = "\n".join(report)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
            logger.info(f"Report saved to {output_path}")
        
        return report_text