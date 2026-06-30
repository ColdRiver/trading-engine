from src.strategy.multi_tf import MultiTimeframeStrategy
from src.trading.exchange import BinanceExchange
from src.trading.executor import TradeExecutor
from config.config import Config

def main():
    print("Connecting to Binance Testnet...")
    exchange = BinanceExchange(testnet=True)
    
    balance = exchange.get_account_balance('USDT')
    print(f"Account Balance: ${balance:.2f} USDT")
    
    current_price = exchange.get_current_price(Config.SYMBOL)
    print(f"Current {Config.SYMBOL} Price: ${current_price:.2f}")
    
    strategy = MultiTimeframeStrategy()
    
    executor = TradeExecutor(strategy=strategy, exchange=exchange)
    
    print(f"\nStarting live trading for {Config.SYMBOL}")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    executor.run_live(check_interval=20)

if __name__ == "__main__":
    main()
