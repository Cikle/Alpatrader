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
import time

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.data.insider_data import OpenInsiderScraper
from src.data.congress_data import SenateScraper
from src.data.news_data import NewsSentimentAnalyzer
from src.utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join("config", "config.ini"))
    return config

def test_insider_scraper():
    """Test the OpenInsider scraper."""
    logger.info("Testing OpenInsider scraper...")
    
    config = load_config()
    db_manager = DatabaseManager()
    
    # Create scraper
    insider_scraper = OpenInsiderScraper(
        min_transaction_size=config.getfloat("trading", "min_insider_transaction_size", fallback=200000),
        sectors=config["filters"]["sectors"].split(",") if "filters" in config and "sectors" in config["filters"] else [],
        blacklist_sectors=config["filters"]["blacklist_sectors"].split(",") if "filters" in config and "blacklist_sectors" in config["filters"] else [],
        db_manager=db_manager
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
            print(df["ticker"].value_counts().head(10))
            
            print("\nTrades by signal:")
            print(df["signal"].value_counts())
            
            print("\nSample trades:")
            sample_cols = ["date", "ticker", "insider", "title", "trade_type", "value", "signal", "confidence"]
            print(df[sample_cols].head(5))
    else:
        logger.warning("No insider trades found")

def test_congress_scraper():
    """Test the Senate Stock Watcher scraper."""
    logger.info("Testing Senate Stock Watcher scraper...")
    
    config = load_config()
    db_manager = DatabaseManager()
    
    # Create scraper
    congress_scraper = SenateScraper(
        max_transaction_size=config.getfloat("trading", "max_congress_transaction_size", fallback=1000000),
        delay_hours=config.getfloat("trading", "congress_delay_hours", fallback=24),
        db_manager=db_manager
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
            print(df["ticker"].value_counts().head(10))
            
            print("\nTrades by politician:")
            if "politician" in df.columns:
                print(df["politician"].value_counts().head(10))
            
            print("\nTrades by signal:")
            print(df["signal"].value_counts())
            
            print("\nSample trades:")
            sample_cols = ["date", "ticker", "politician", "transaction_type", "estimated_value", "signal"]
            sample_cols = [col for col in sample_cols if col in df.columns]
            print(df[sample_cols].head(5))
    else:
        logger.warning("No Congress trades found")

def test_news_analyzer():
    """Test the News Sentiment Analyzer."""
    logger.info("Testing News Sentiment Analyzer...")
    
    config = load_config()
    db_manager = DatabaseManager()
    
    # Create analyzer
    news_analyzer = NewsSentimentAnalyzer(
        newsapi_key=config["news"]["newsapi_key"] if "news" in config and "newsapi_key" in config["news"] else None,
        gnews_key=config["news"]["gnews_key"] if "news" in config and "gnews_key" in config["news"] else None,
        finnhub_key=config["sentiment"]["finnhub_key"] if "sentiment" in config and "finnhub_key" in config["sentiment"] else None,
        db_manager=db_manager
    )
    
    # Test tickers
    test_tickers = ["AAPL", "MSFT", "GOOGL", "MARKET"]
    
    # Fetch news
    print("\n--- FETCHING NEWS ---")
    for ticker in test_tickers:
        print(f"\nTesting news for {ticker}...")
        news_items = news_analyzer.fetch_latest_news([ticker], days_back=2)
        
        if not news_items or ticker not in news_items:
            print(f"No news found for {ticker}")
            continue
            
        items = news_items[ticker]
        print(f"Found {len(items)} news items for {ticker}")
        
        if not items:
            continue
            
        # Display sample
        print("\nSample news items:")
        for i, item in enumerate(items[:3]):  # Show up to 3 items
            print(f"\nNews {i+1}:")
            print(f"  Title: {item.get('title')}")
            print(f"  Signal: {item.get('signal')}")
            print(f"  Confidence: {item.get('confidence', 0):.2f}")
            print(f"  Source: {item.get('source')}")
            print(f"  Date: {item.get('date')}")
            
    # Test market mood analysis
    print("\n--- MARKET MOOD ANALYSIS ---")
    mood = news_analyzer.analyze_market_mood(days_back=2)
    print(f"Market mood: {mood.get('mood')}")
    print(f"Confidence: {mood.get('confidence', 0):.2f}")
    print(f"Description: {mood.get('description')}")
    
    # Test strong news signals
    print("\n--- STRONG NEWS SIGNALS ---")
    strong_signals = news_analyzer.get_strong_news_signals(threshold=0.7)
    
    if strong_signals:
        print(f"Found {len(strong_signals)} strong news signals")
        
        for i, signal in enumerate(strong_signals[:5]):  # Show up to 5 signals
            print(f"\nStrong signal {i+1}:")
            print(f"  Ticker: {signal.get('ticker')}")
            print(f"  Title: {signal.get('title')}")
            print(f"  Signal: {signal.get('signal')}")
            print(f"  Confidence: {signal.get('confidence', 0):.2f}")
    else:
        print("No strong news signals found")

def main():
    """Run scraper tests."""
    print("=" * 80)
    print("ALPATRADER SCRAPER TEST")
    print("=" * 80)
    print("\nThis test will check all data scrapers and show sample outputs.")
    print("Press Ctrl+C at any time to abort.\n")
    
    # Test all scrapers
    test_insider_scraper()
    print("\n" + "=" * 80 + "\n")
    time.sleep(1)  # Pause between tests
    
    test_congress_scraper()
    print("\n" + "=" * 80 + "\n")
    time.sleep(1)  # Pause between tests
    
    test_news_analyzer()
    print("\n" + "=" * 80)
    print("Tests completed successfully!")

if __name__ == "__main__":
    main()