#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script for data scrapers.
Use this to quickly test the OpenInsider and Senate Stock Watcher scrapers.
"""

import os
import sys
import logging
import configparser
from datetime import datetime, timedelta
import pandas as pd

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.data.insider_data import OpenInsiderScraper
from src.data.congress_data import SenateScraper
from src.data.news_data import NewsSentimentAnalyzer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('config', 'config.ini'))
    return config

def test_insider_scraper():
    """Test the OpenInsider scraper."""
    logger.info("Testing OpenInsider scraper...")
    
    config = load_config()
    
    # Create scraper
    insider_scraper = OpenInsiderScraper(
        min_transaction_size=config.getfloat('trading', 'min_insider_transaction_size'),
        sectors=config['filters']['sectors'].split(','),
        blacklist_sectors=config['filters']['blacklist_sectors'].split(',')
    )
    
    # Fetch data
    insider_trades = insider_scraper.fetch_latest_data()
    
    # Display results
    if insider_trades:
        logger.info(f"Found {len(insider_trades)} insider trades")
        
        # Convert to DataFrame for display
        df = pd.DataFrame(insider_trades)
        
        # Display summary
        print("\n--- INSIDER TRADES SUMMARY ---")
        print(f"Total trades: {len(df)}")
        
        if not df.empty:
            print("\nTrades by ticker:")
            print(df['ticker'].value_counts().head(10))
            
            print("\nTrades by signal:")
            print(df['signal'].value_counts())
            
            print("\nSample trades:")
            sample_cols = ['date', 'ticker', 'insider', 'title', 'trade_type', 'value', 'signal']
            print(df[sample_cols].head(5))
    else:
        logger.warning("No insider trades found")

def test_congress_scraper():
    """Test the Senate Stock Watcher scraper."""
    logger.info("Testing Senate Stock Watcher scraper...")
    
    config = load_config()
    
    # Create scraper
    congress_scraper = SenateScraper(
        max_transaction_size=config.getfloat('trading', 'max_congress_transaction_size'),
        delay_hours=config.getfloat('trading', 'congress_delay_hours')
    )
    
    # Fetch data
    congress_trades = congress_scraper.fetch_latest_data()
    
    # Display results
    if congress_trades:
        logger.info(f"Found {len(congress_trades)} Congress trades")
        
        # Convert to DataFrame for display
        df = pd.DataFrame(congress_trades)
        
        # Display summary
        print("\n--- CONGRESS TRADES SUMMARY ---")
        print(f"Total trades: {len(df)}")
        
        if not df.empty:
            print("\nTrades by ticker:")
            print(df['ticker'].value_counts().head(10))
            
            print("\nTrades by senator:")
            print(df['politician'].value_counts().head(10))
            
            print("\nTrades by signal:")
            print(df['signal'].value_counts())
            
            print("\nSample trades:")
            sample_cols = ['date', 'ticker', 'politician', 'transaction_type', 'estimated_value', 'signal']
            print(df[sample_cols].head(5))
    else:
        logger.warning("No Congress trades found")

def test_news_analyzer():
    """Test the News Sentiment Analyzer."""
    logger.info("Testing News Sentiment Analyzer...")
    
    config = load_config()
    
    # Create analyzer
    news_analyzer = NewsSentimentAnalyzer(
        newsapi_key=config['news'].get('newsapi_key', None),
        finnhub_key=config['sentiment'].get('finnhub_key', None)
    )
    
    # Test tickers
    test_tickers = ['AAPL', 'MSFT', 'GOOGL']
    
    # Fetch news
    news_by_ticker = news_analyzer.fetch_latest_news(test_tickers)
    
    # Display results
    if news_by_ticker:
        total_news = sum(len(news) for news in news_by_ticker.values())
        logger.info(f"Found {total_news} news items for {len(news_by_ticker)} tickers")
        
        # Display summary
        print("\n--- NEWS SENTIMENT SUMMARY ---")
        
        for ticker, news_items in news_by_ticker.items():
            print(f"\nTicker: {ticker} - {len(news_items)} news items")
            
            if news_items:
                # Convert to DataFrame
                df = pd.DataFrame(news_items)
                
                print("\nSentiment distribution:")
                print(df['signal'].value_counts())
                
                print("\nSample headlines:")
                for i, item in enumerate(news_items[:3]):
                    print(f"{i+1}. {item['title']} (Score: {item.get('sentiment_score', 'N/A')})")
    else:
        logger.warning("No news found. Check your API keys.")

def main():
    """Main entry point for the test script."""
    print("\n========== ALPATRADER DATA SCRAPER TEST ==========\n")
    
    # Test each scraper
    try:
        test_insider_scraper()
    except Exception as e:
        logger.error(f"Error testing insider scraper: {e}", exc_info=True)
    
    print("\n" + "="*50 + "\n")
    
    try:
        test_congress_scraper()
    except Exception as e:
        logger.error(f"Error testing congress scraper: {e}", exc_info=True)
    
    print("\n" + "="*50 + "\n")
    
    try:
        test_news_analyzer()
    except Exception as e:
        logger.error(f"Error testing news analyzer: {e}", exc_info=True)
    
    print("\n========== TEST COMPLETE ==========\n")

if __name__ == "__main__":
    main()
