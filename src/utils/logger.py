import logging
import os
from datetime import datetime

def setup_logger(name, log_file=None, level=logging.INFO):
    """Set up logger with file and console handlers."""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_trade(logger, trade_type, direction, entry_price, exit_price, size, pnl, metadata=None):
    """Log trade details."""
    log_msg = f"Trade {trade_type.upper()} - {direction.upper()} | Entry: {entry_price} | Exit: {exit_price} | Size: {size} | PnL: {pnl:.2f}"
    if metadata:
        log_msg += f" | Metadata: {metadata}"
    logger.info(log_msg)
