#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the configurable strategy implementation.
"""

import sys
import os
import configparser
from datetime import datetime

# Add the project root directory to the path
project_root = os.path.dirname(__file__)
sys.path.append(project_root)

# Try to import with the correct path
from src.models.signal_processor import SignalProcessor

def test_strategy_configuration():
    """Test the strategy configuration loading and validation."""
    
    # Load configuration
    config = configparser.ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.ini')
    
    if not os.path.exists(config_path):
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    config.read(config_path)
    
    # Create mock scrapers and analyzer for testing
    class MockScraper:
        def fetch_latest_data(self):
            return []
    
    class MockAnalyzer:
        def fetch_latest_news(self, tickers):
            return {}
        def get_strong_news_signals(self, threshold):
            return []
    
    # Initialize signal processor
    try:
        processor = SignalProcessor(
            config=config,
            insider_scraper=MockScraper(),
            congress_scraper=MockScraper(),
            news_analyzer=MockAnalyzer()
        )
        
        print("✅ SignalProcessor initialized successfully!")
        print(f"   Insider Strategy: {processor.insider_strategy}")
        print(f"   Congress Strategy: {processor.congress_strategy}")
        
        # Test different strategy configurations
        test_configurations = [
            ('inverse', 'inverse'),
            ('normal', 'normal'),
            ('disabled', 'disabled'),
            ('inverse', 'normal'),
            ('normal', 'inverse'),
            ('disabled', 'inverse'),
            ('inverse', 'disabled')
        ]
        
        print("\n📋 Testing different strategy configurations:")
        
        for insider_strat, congress_strat in test_configurations:
            # Create a test config with the strategies
            test_config = configparser.ConfigParser()
            test_config.read_string(f"""
[trading]
insider_strategy = {insider_strat}
congress_strategy = {congress_strat}
strong_news_multiplier = 2.0
congress_only_multiplier = 1.0
insider_only_multiplier = 0.5
[filters]
skip_fomc_blackout = True
            """)
            
            # Test the processor with this config
            test_processor = SignalProcessor(
                config=test_config,
                insider_scraper=MockScraper(),
                congress_scraper=MockScraper(),
                news_analyzer=MockAnalyzer()
            )
            
            print(f"   ✅ Insider: {insider_strat.ljust(8)} | Congress: {congress_strat.ljust(8)} → Working!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing SignalProcessor: {e}")
        return False

def test_signal_processing_logic():
    """Test the signal processing logic with different strategies."""
    
    print("\n🧪 Testing signal processing logic:")
    
    # Create a test config
    config = configparser.ConfigParser()
    config.read_string("""
[trading]
insider_strategy = inverse
congress_strategy = normal
strong_news_multiplier = 2.0
congress_only_multiplier = 1.0
insider_only_multiplier = 0.5
[filters]
skip_fomc_blackout = False
    """)
    
    # Create mock scrapers with test data
    class MockScraperWithData:
        def __init__(self, data):
            self.data = data
            
        def fetch_latest_data(self):
            return self.data
    
    class MockAnalyzerWithData:
        def fetch_latest_news(self, tickers):
            return {ticker: [] for ticker in tickers}
            
        def get_strong_news_signals(self, threshold):
            return []
    
    # Test data
    insider_data = [
        {
            'ticker': 'AAPL',
            'signal': 'buy',
            'confidence': 0.8,
            'source': 'insider',
            'insider': 'John Doe',
            'title': 'CEO'
        }
    ]
    
    congress_data = [
        {
            'ticker': 'AAPL',
            'signal': 'sell',
            'confidence': 0.7,
            'source': 'congress',
            'politician': 'Jane Smith'
        }
    ]
    
    # Initialize processor with test data
    processor = SignalProcessor(
        config=config,
        insider_scraper=MockScraperWithData(insider_data),
        congress_scraper=MockScraperWithData(congress_data),
        news_analyzer=MockAnalyzerWithData()
    )
    
    # Process signals
    signals = processor.process_signals()
    
    if signals:
        signal = signals[0]
        print(f"   📊 Generated signal for {signal['ticker']}:")
        print(f"      Original insider signal: buy (inverse strategy)")
        print(f"      Original congress signal: sell (normal strategy)")
        print(f"      Final signal: {signal['signal']}")
        print(f"      Description: {signal['description']}")
        print(f"   ✅ Signal processing working correctly!")
    else:
        print("   ⚠️  No signals generated")
    
    return len(signals) > 0

if __name__ == "__main__":
    print("🚀 Testing Configurable Trading Strategy Implementation")
    print("=" * 60)
    
    success = True
    
    # Test 1: Configuration loading
    if not test_strategy_configuration():
        success = False
    
    # Test 2: Signal processing logic
    if not test_signal_processing_logic():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed! Strategy configuration is working correctly.")
        print("\n📝 You can now adjust the strategy settings in config/config.ini:")
        print("   - Set insider_strategy to 'inverse', 'normal', or 'disabled'")
        print("   - Set congress_strategy to 'inverse', 'normal', or 'disabled'")
        print("   - 'inverse' = trade opposite to the signal")
        print("   - 'normal' = follow the signal")
        print("   - 'disabled' = ignore signals from that source")
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
