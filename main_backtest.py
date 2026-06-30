import pandas as pd
from src.strategy.multi_tf import MultiTimeframeStrategy
from src.backtesting.backtest import Backtester
from src.backtesting.analyzer import TradeAnalyzer
from src.utils.data import fetch_historical_data
from config.config import Config

def main():
    print("Fetching historical data...")
    df_15m = fetch_historical_data(
        Config.SYMBOL,
        Config.ENTRY_TIMEFRAME,
        Config.BACKTEST_START,
        Config.BACKTEST_END,
        testnet=False
    )
    
    df_1h = fetch_historical_data(
        Config.SYMBOL,
        Config.CONFIRMATION_TIMEFRAME,
        Config.BACKTEST_START,
        Config.BACKTEST_END,
        testnet=False
    )
    
    print(f"Data loaded: {len(df_15m)} rows (15m), {len(df_1h)} rows (1h)")
    
    strategy = MultiTimeframeStrategy()
    
    backtester = Backtester(
        strategy=strategy,
        df_entry=df_15m,
        df_confirm=df_1h,
        initial_capital=Config.INITIAL_CAPITAL,
        commission=Config.COMMISSION
    )
    
    print("Running backtest...")
    results = backtester.run()
    
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Total Trades: {results['total_trades']}")
    print(f"Winning Trades: {results['winning_trades']}")
    print(f"Losing Trades: {results['losing_trades']}")
    print(f"Win Rate: {results['win_rate']:.2f}%")
    print(f"Total PnL: ${results['total_pnl']:.2f}")
    print(f"Total Return: {results['total_return']:.2f}%")
    print(f"Average Win: ${results['avg_win']:.2f}")
    print(f"Average Loss: ${results['avg_loss']:.2f}")
    print(f"Final Capital: ${results['final_capital']:.2f}")
    print("="*50)
    
    backtester.save_trades()
    print(f"\nTrades saved to {Config.BACKTEST_TRADES_PATH}")
    
    analyzer = TradeAnalyzer(backtest_trades=results['trades'])
    report = analyzer.generate_report('data/backtest_report.txt')
    print("\nReport generated: data/backtest_report.txt")

if __name__ == "__main__":
    main()