#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Backtest example for the Alpatrader system.
Tests the strategy on historical data.
"""

import os
import sys
import logging
import configparser
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.data.insider_data import OpenInsiderScraper
from src.data.congress_data import SenateScraper
from src.data.news_data import NewsSentimentAnalyzer
from src.models.signal_processor import SignalProcessor
from src.strategies.inverse_strategy import InverseStrategy
from src.utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('..', 'logs', f'backtest_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('..', 'config', 'config.ini'))
    return config

def create_mock_data():
    """
    Create mock data for backtesting.
    
    Returns:
        dict: Dictionary containing mock data
    """
    # Mock data for SVB collapse scenario (March 2023)
    svb_data = {
        'insider_trades': [
            {
                'date': datetime(2023, 2, 25),
                'ticker': 'SIVB',
                'company': 'SVB Financial Group',
                'insider': 'John Smith',
                'title': 'CEO',
                'trade_type': 'S-Sale',
                'price': 280.0,
                'quantity': 10000,
                'value': 2800000.0,
                'ownership_change': -25.0,
                'sector': 'finance',
                'signal': 'BULLISH',  # Inverse of Sale
                'source': 'insider',
                'source_detail': 'OpenInsider - John Smith (CEO)',
                'confidence': 0.9,
            },
            {
                'date': datetime(2023, 2, 27),
                'ticker': 'SIVB',
                'company': 'SVB Financial Group',
                'insider': 'Jane Doe',
                'title': 'CFO',
                'trade_type': 'S-Sale',
                'price': 275.0,
                'quantity': 8000,
                'value': 2200000.0,
                'ownership_change': -30.0,
                'sector': 'finance',
                'signal': 'BULLISH',  # Inverse of Sale
                'source': 'insider',
                'source_detail': 'OpenInsider - Jane Doe (CFO)',
                'confidence': 0.85,
            }
        ],
        'congress_trades': [
            {
                'date': datetime(2023, 3, 8),
                'ticker': 'JPM',
                'company': 'JPMorgan Chase & Co.',
                'politician': 'Senator Johnson',
                'transaction_type': 'Purchase',
                'estimated_value': 250000.0,
                'asset_type': 'Stock',
                'signal': 'BEARISH',  # Inverse of Purchase
                'source': 'congress',
                'source_detail': 'Senate Stock Watcher - Senator Johnson',
                'confidence': 0.95,
            },
            {
                'date': datetime(2023, 3, 8),
                'ticker': 'BAC',
                'company': 'Bank of America Corp',
                'politician': 'Senator Smith',
                'transaction_type': 'Purchase',
                'estimated_value': 180000.0,
                'asset_type': 'Stock',
                'signal': 'BEARISH',  # Inverse of Purchase
                'source': 'congress',
                'source_detail': 'Senate Stock Watcher - Senator Smith',
                'confidence': 0.9,
            }
        ],
        'news': [
            {
                'ticker': 'SIVB',
                'title': 'SVB Financial faces liquidity concerns as deposits drop',
                'url': 'https://example.com/svb-news1',
                'source': 'Financial Times',
                'date': datetime(2023, 3, 9),
                'summary': 'SVB Financial Group is facing liquidity concerns as deposits have dropped significantly.',
                'sentiment_score': -0.8,
                'signal': 'BULLISH',  # Inverse of negative news
                'confidence': 0.9,
                'source_detail': 'News Sentiment - SIVB'
            },
            {
                'ticker': 'SIVB',
                'title': 'SVB stock plunges as bank seeks capital raise',
                'url': 'https://example.com/svb-news2',
                'source': 'Wall Street Journal',
                'date': datetime(2023, 3, 9),
                'summary': 'SVB stock plunged more than 60% as the bank announced it is seeking to raise capital.',
                'sentiment_score': -0.9,
                'signal': 'BULLISH',  # Inverse of negative news
                'confidence': 0.95,
                'source_detail': 'News Sentiment - SIVB'
            }
        ]
    }
    
    # Mock data for Meta insider sales (2022)
    meta_data = {
        'insider_trades': [
            {
                'date': datetime(2022, 10, 5),
                'ticker': 'META',
                'company': 'Meta Platforms Inc',
                'insider': 'Mark Zuckerberg',
                'title': 'CEO',
                'trade_type': 'S-Sale',
                'price': 140.0,
                'quantity': 100000,
                'value': 14000000.0,
                'ownership_change': -5.0,
                'sector': 'technology',
                'signal': 'BULLISH',  # Inverse of Sale
                'source': 'insider',
                'source_detail': 'OpenInsider - Mark Zuckerberg (CEO)',
                'confidence': 0.95,
            },
            {
                'date': datetime(2022, 10, 7),
                'ticker': 'META',
                'company': 'Meta Platforms Inc',
                'insider': 'David Wehner',
                'title': 'CFO',
                'trade_type': 'S-Sale',
                'price': 138.0,
                'quantity': 20000,
                'value': 2760000.0,
                'ownership_change': -20.0,
                'sector': 'technology',
                'signal': 'BULLISH',  # Inverse of Sale
                'source': 'insider',
                'source_detail': 'OpenInsider - David Wehner (CFO)',
                'confidence': 0.9,
            }
        ],
        'congress_trades': [],  # No congress trades for Meta
        'news': [
            {
                'ticker': 'META',
                'title': 'Meta faces challenges with metaverse investments',
                'url': 'https://example.com/meta-news1',
                'source': 'CNBC',
                'date': datetime(2022, 10, 10),
                'summary': 'Meta is facing challenges with its metaverse investments as costs rise.',
                'sentiment_score': -0.6,
                'signal': 'BULLISH',  # Inverse of negative news
                'confidence': 0.8,
                'source_detail': 'News Sentiment - META'
            },
            {
                'ticker': 'META',
                'title': 'Advertisers reduce spending on Meta platforms',
                'url': 'https://example.com/meta-news2',
                'source': 'Reuters',
                'date': datetime(2022, 10, 12),
                'summary': 'Advertisers are reducing spending on Meta platforms due to economic concerns.',
                'sentiment_score': -0.7,
                'signal': 'BULLISH',  # Inverse of negative news
                'confidence': 0.85,
                'source_detail': 'News Sentiment - META'
            }
        ]
    }
    
    # Combine both scenarios
    all_data = {
        'svb': svb_data,
        'meta': meta_data
    }
    
    return all_data

def process_signals(mock_data, scenario):
    """
    Process signals from mock data.
    
    Args:
        mock_data (dict): Mock data dictionary
        scenario (str): Scenario name
        
    Returns:
        list: List of processed signals
    """
    # Get mock data for the specified scenario
    scenario_data = mock_data.get(scenario, {})
    
    # Get signal processor
    config = load_config()
    
    # Create dummy scrapers
    insider_scraper = OpenInsiderScraper(
        min_transaction_size=config.getfloat('trading', 'min_insider_transaction_size'),
        sectors=config['filters']['sectors'].split(','),
        blacklist_sectors=config['filters']['blacklist_sectors'].split(',')
    )
    
    congress_scraper = SenateScraper(
        max_transaction_size=config.getfloat('trading', 'max_congress_transaction_size'),
        delay_hours=config.getfloat('trading', 'congress_delay_hours')
    )
    
    news_analyzer = NewsSentimentAnalyzer()
    
    # Create signal processor
    signal_processor = SignalProcessor(
        config=config,
        insider_scraper=insider_scraper,
        congress_scraper=congress_scraper,
        news_analyzer=news_analyzer
    )
    
    # Monkey patch the fetch methods to return mock data
    insider_scraper.fetch_latest_data = lambda: scenario_data.get('insider_trades', [])
    congress_scraper.fetch_latest_data = lambda: scenario_data.get('congress_trades', [])
    
    # Create a mock method for news strong signals
    def mock_get_strong_news_signals(threshold=0.7):
        return [n for n in scenario_data.get('news', []) if n.get('confidence', 0) >= threshold]
    
    news_analyzer.get_strong_news_signals = mock_get_strong_news_signals
    
    # Process signals
    signals = signal_processor.process_signals()
    
    return signals

def run_backtest(mock_data, scenario, start_date, end_date):
    """
    Run backtest for a scenario.
    
    Args:
        mock_data (dict): Mock data dictionary
        scenario (str): Scenario name
        start_date (datetime): Start date for backtest
        end_date (datetime): End date for backtest
        
    Returns:
        dict: Backtest results
    """
    logger.info(f"Running backtest for {scenario} scenario")
    
    # Process signals
    signals = process_signals(mock_data, scenario)
    
    # Create strategy
    config = load_config()
    
    # Create dummy Alpaca wrapper
    class DummyAlpaca:
        def __init__(self):
            pass
            
        def get_account(self):
            class DummyAccount:
                def __init__(self):
                    self.equity = 100000
                    self.buying_power = 100000
                    
            return DummyAccount()
            
        def get_positions(self):
            return []
            
        def get_last_price(self, ticker):
            return 100.0
    
    alpaca = DummyAlpaca()
    
    # Create signal processor (dummy)
    signal_processor = None
    
    # Create strategy
    strategy = InverseStrategy(
        alpaca=alpaca,
        signal_processor=signal_processor,
        config=config
    )
    
    # Run backtest
    results = strategy.backtest(
        signals=signals,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000
    )
    
    return results

def plot_results(results, scenario, output_dir):
    """
    Plot backtest results.
    
    Args:
        results (dict): Backtest results
        scenario (str): Scenario name
        output_dir (str): Output directory for plots
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract data
    daily_equity = results['daily_equity']
    trades = results['trades']
    
    # Create DataFrame for equity
    equity_df = pd.DataFrame(daily_equity)
    equity_df['date'] = pd.to_datetime(equity_df['date'])
    equity_df.set_index('date', inplace=True)
    
    # Create figure for equity curve
    plt.figure(figsize=(12, 6))
    plt.plot(equity_df.index, equity_df['equity'])
    plt.title(f'{scenario.upper()} Scenario - Equity Curve')
    plt.xlabel('Date')
    plt.ylabel('Equity ($)')
    plt.grid(True)
    plt.savefig(os.path.join(output_dir, f'{scenario}_equity_curve.png'))
    
    # Create DataFrame for trades
    if trades:
        trade_data = []
        for trade in trades:
            trade_data.append({
                'date': trade['date'],
                'ticker': trade['ticker'],
                'action': trade['action'],
                'quantity': trade['quantity'],
                'price': trade['price'],
                'value': trade['value']
            })
            
        trades_df = pd.DataFrame(trade_data)
        trades_df['date'] = pd.to_datetime(trades_df['date'])
        
        # Group by ticker
        ticker_returns = {}
        for ticker in trades_df['ticker'].unique():
            ticker_trades = trades_df[trades_df['ticker'] == ticker]
            ticker_trades = ticker_trades.sort_values('date')
            
            buys = ticker_trades[ticker_trades['action'] == 'BUY']
            sells = ticker_trades[ticker_trades['action'] == 'SELL']
            
            if len(buys) > 0 and len(sells) > 0:
                buy_value = buys['value'].sum()
                sell_value = sells['value'].sum()
                
                returns = (sell_value - buy_value) / buy_value
                ticker_returns[ticker] = returns
        
        # Plot returns by ticker
        if ticker_returns:
            plt.figure(figsize=(10, 5))
            tickers = list(ticker_returns.keys())
            returns = [ticker_returns[t] * 100 for t in tickers]
            
            plt.bar(tickers, returns)
            plt.title(f'{scenario.upper()} Scenario - Returns by Ticker (%)')
            plt.xlabel('Ticker')
            plt.ylabel('Returns (%)')
            plt.grid(True, axis='y')
            
            # Add return values on top of bars
            for i, (ticker, ret) in enumerate(zip(tickers, returns)):
                plt.text(i, ret + (1 if ret >= 0 else -3), f'{ret:.1f}%', ha='center')
                
            plt.savefig(os.path.join(output_dir, f'{scenario}_ticker_returns.png'))
    
    # Summary
    initial_capital = results['initial_capital']
    final_value = results['final_value']
    returns = results['returns']
    
    summary_text = f"""
    {scenario.upper()} Scenario Backtest Summary
    --------------------------------------
    Initial Capital: ${initial_capital:,.2f}
    Final Value: ${final_value:,.2f}
    Total Return: {returns * 100:.2f}%
    Number of Trades: {len(trades)}
    """
    
    # Print and save summary
    print(summary_text)
    
    with open(os.path.join(output_dir, f'{scenario}_summary.txt'), 'w') as f:
        f.write(summary_text)

def main():
    """Main entry point for the backtest."""
    logger.info("Starting backtests")
    
    # Create mock data
    mock_data = create_mock_data()
    
    # Define date ranges for backtests
    scenarios = {
        'svb': {
            'start_date': datetime(2023, 2, 20),
            'end_date': datetime(2023, 3, 20)
        },
        'meta': {
            'start_date': datetime(2022, 10, 1),
            'end_date': datetime(2022, 10, 30)
        }
    }
    
    # Output directory
    output_dir = os.path.join('..', 'backtests', 'results')
    
    # Run backtests for each scenario
    for scenario, dates in scenarios.items():
        results = run_backtest(
            mock_data=mock_data,
            scenario=scenario,
            start_date=dates['start_date'],
            end_date=dates['end_date']
        )
        
        # Plot results
        plot_results(results, scenario, output_dir)
    
    logger.info("Backtests completed")

if __name__ == "__main__":
    main()
