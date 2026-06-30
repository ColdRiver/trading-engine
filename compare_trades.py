import pandas as pd
from src.backtesting.analyzer import TradeAnalyzer
from config.config import Config

def main():
    analyzer = TradeAnalyzer()
    analyzer.load_trades_from_files(
        backtest_path=Config.BACKTEST_TRADES_PATH,
        live_path=Config.LIVE_TRADES_PATH
    )
    
    if analyzer.backtest_trades is not None and not analyzer.backtest_trades.empty:
        backtest_metrics = analyzer.calculate_metrics(analyzer.backtest_trades)
        analyzer.print_metrics(backtest_metrics, "BACKTEST METRICS")
    
    if analyzer.live_trades is not None and not analyzer.live_trades.empty:
        live_metrics = analyzer.calculate_metrics(analyzer.live_trades)
        analyzer.print_metrics(live_metrics, "LIVE TRADING METRICS")
    
    comparison = analyzer.compare_trades()
    if comparison:
        print("\n" + "="*50)
        print("COMPARISON (Live - Backtest)")
        print("="*50)
        for key, value in comparison['differences'].items():
            print(f"{key}: {value:.2f}" if isinstance(value, float) else f"{key}: {value}")
        print("="*50)
    
    report = analyzer.generate_report('data/comparison_report.txt')
    print("\nFull report saved to: data/comparison_report.txt")

if __name__ == "__main__":
    main()