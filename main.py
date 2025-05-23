#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Alpatrader - A trading bot for Alpaca paper trading that uses news sentiment
and insider/Congress trades to execute inverse trading strategies.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
import configparser

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data.insider_data import OpenInsiderScraper
from src.data.congress_data import SenateScraper
from src.data.news_data import NewsSentimentAnalyzer
from src.models.signal_processor import SignalProcessor
from src.strategies.inverse_strategy import InverseStrategy
from src.utils.db_manager import DatabaseManager
from src.utils.alpaca_wrapper import AlpacaWrapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('logs', f'alpatrader_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def print_disclaimer():
    """Prints legal disclaimer."""
    disclaimer = """
    DISCLAIMER: Not financial advice. Insider data may be delayed. 
    This tool is for educational and research purposes only.
    Use at your own risk. Past performance is not indicative of future results.
    """
    print(disclaimer)
    logger.info("Disclaimer printed")

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('config', 'config.ini'))
    return config

def main():
    """Main entry point for the trading bot."""
    print_disclaimer()
    
    # Load configuration
    config = load_config()
    
    # Initialize components
    db_manager = DatabaseManager()
    alpaca = AlpacaWrapper(
        api_key=config['alpaca']['api_key'],
        api_secret=config['alpaca']['api_secret'],
        base_url=config['alpaca']['base_url'],
        data_url=config['alpaca']['data_url']
    )
    
    # Initialize data sources
    insider_scraper = OpenInsiderScraper(
        min_transaction_size=config.getfloat('trading', 'min_insider_transaction_size'),
        sectors=config['filters']['sectors'].split(','),
        blacklist_sectors=config['filters']['blacklist_sectors'].split(','),
        db_manager=db_manager
    )
    
    congress_scraper = SenateScraper(
        max_transaction_size=config.getfloat('trading', 'max_congress_transaction_size'),
        delay_hours=config.getfloat('trading', 'congress_delay_hours'),
        db_manager=db_manager
    )
    
    news_analyzer = NewsSentimentAnalyzer(
        newsapi_key=config['news']['newsapi_key'],
        finnhub_key=config['sentiment']['finnhub_key'],
        db_manager=db_manager
    )
    
    # Initialize signal processor and strategy
    signal_processor = SignalProcessor(
        config=config,
        insider_scraper=insider_scraper,
        congress_scraper=congress_scraper,
        news_analyzer=news_analyzer
    )
    
    strategy = InverseStrategy(
        alpaca=alpaca,
        signal_processor=signal_processor,
        config=config
    )
    
    logger.info("Alpatrader started")
    
    # Main trading loop
    while True:
        try:
            # Only run during market hours
            if alpaca.is_market_open():
                logger.info("Market is open, processing signals...")
                  # Process signals and generate trades
                signals = signal_processor.process_signals()
                
                # Execute stock trades based on signals
                stock_trades = strategy.execute_trades(signals)
                
                # Execute options trades for strong signals (confidence > 0.7)
                strong_signals = [s for s in signals if s.get('confidence', 0) > 0.7]
                if strong_signals:
                    option_trades = strategy.execute_option_trades(strong_signals)
                    logger.info(f"Executed {len(option_trades)} option trades for strong signals")
                
                logger.info(f"Processed {len(signals)} signals ({len(stock_trades)} stock trades)")
            else:
                # Continue to collect data even when market is closed
                insider_scraper.fetch_latest_data()
                congress_scraper.fetch_latest_data()
                news_analyzer.fetch_latest_news()
                logger.info("Market is closed, updated data sources")
            
            # Sleep for 15 minutes before next cycle
            time.sleep(15 * 60)
            
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            time.sleep(5 * 60)  # Wait 5 minutes on error

if __name__ == "__main__":
    main()
