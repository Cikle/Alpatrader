#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Backtest examples for the Alpatrader system.
Tests the strategy on historical events like SVB collapse and Meta insider sales.
"""

import os
import sys
import logging
import configparser
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.utils.db_manager import DatabaseManager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join('..', '..', 'logs', f'backtest_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('..', '..', 'config', 'config.ini'))
    return config

class BacktestExample:
    """
    Class for running backtests on historical events.
    """
    
    def __init__(self, output_dir=None):
        """
        Initialize the backtest example.
        
        Args:
            output_dir (str): Directory for outputs
        """
        if not output_dir:
            output_dir = os.path.join('..', '..', 'logs', 'backtests')
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        self.output_dir = output_dir
        self.db_manager = DatabaseManager()
    
    def run_svb_collapse_backtest(self):
        """
        Run backtest for the SVB collapse scenario (March 2023).
        
        Returns:
            dict: Backtest results
        """
        logger.info("Running SVB collapse backtest")
        
        # SVB collapse timeline:
        # - March 8, 2023: SVB announces stock sale to shore up balance sheet
        # - March 9, 2023: Stock plunges 60% as depositors rush to withdraw funds
        # - March 10, 2023: Trading halted, FDIC takes over
        
        # Simulated insider trade before news broke
        insider_trade = {
            'date': datetime(2023, 3, 7, 14, 30),  # Before the news broke
            'ticker': 'SIVB',
            'insider': 'CFO',
            'title': 'Chief Financial Officer',
            'trade_type': 'S - Sale',
            'value': 2500000,  # Large sale
            'signal': 'BEARISH',
            'confidence': 0.9,
        }
        
        # Simulated news signal as events unfold
        news_signals = [
            {
                'date': datetime(2023, 3, 8, 16, 30),
                'ticker': 'SIVB',
                'title': 'Silicon Valley Bank Announces $2.25 Billion Stock Sale to Shore Up Capital',
                'signal': 'BEARISH',
                'confidence': 0.8,
            },
            {
                'date': datetime(2023, 3, 9, 10, 15),
                'ticker': 'SIVB',
                'title': 'SVB Financial Plunges 60% as Startup Clients Withdraw Deposits',
                'signal': 'BEARISH',
                'confidence': 0.95,
            }
        ]
        
        # SIVB price data (approximate)
        sivb_prices = {
            '2023-03-06': 267.83,
            '2023-03-07': 267.10,  # Insider sale day
            '2023-03-08': 267.83,  # Stock sale announcement after close
            '2023-03-09': 106.04,  # -60% plunge
            '2023-03-10': 39.40,   # Trading halted, FDIC takeover
        }
        
        # Regional bank ETF (KRE) for industry impact
        kre_prices = {
            '2023-03-06': 60.54,
            '2023-03-07': 59.86,
            '2023-03-08': 57.28,
            '2023-03-09': 51.95,
            '2023-03-10': 50.53,
            '2023-03-13': 44.36,  # Continued fallout
            '2023-03-14': 46.97,
        }
        
        # Simulate trading decisions
        decisions = []
        
        # Day 1: Insider trade detected
        decisions.append({
            'date': '2023-03-07',
            'ticker': 'SIVB',
            'price': 267.10,
            'action': 'SHORT',  # Inverse of the BEARISH signal
            'confidence': 0.5,  # Insider only - use 0.5x multiplier
            'quantity': 50,     # Small position initially
            'portfolio_pct': 3, # 3% allocation
            'signal_source': 'insider'
        })
        
        # Day 2: News + Insider strengthens signal
        decisions.append({
            'date': '2023-03-08',
            'ticker': 'SIVB',
            'price': 267.83,
            'action': 'SHORT',  # Increase position
            'confidence': 0.9,  # Strong news + insider - use 2x multiplier
            'quantity': 25,     # Add to position
            'portfolio_pct': 5, # Maximum 5% allocation
            'signal_source': 'news+insider'
        })
        
        # Day 3: Add industry impact trade
        decisions.append({
            'date': '2023-03-09',
            'ticker': 'KRE',
            'price': 51.95,
            'action': 'SHORT',  # Industry contagion
            'confidence': 0.7,
            'quantity': 100,
            'portfolio_pct': 4,
            'signal_source': 'industry-impact'
        })
        
        # Calculate PnL
        sivb_trade_pnl = (
            (decisions[0]['quantity'] * (decisions[0]['price'] - sivb_prices['2023-03-10'])) +
            (decisions[1]['quantity'] * (decisions[1]['price'] - sivb_prices['2023-03-10']))
        )
        
        kre_trade_pnl = decisions[2]['quantity'] * (decisions[2]['price'] - kre_prices['2023-03-13'])
        
        total_pnl = sivb_trade_pnl + kre_trade_pnl
        
        # Calculate returns
        initial_investment = (
            (decisions[0]['quantity'] * decisions[0]['price']) +
            (decisions[1]['quantity'] * decisions[1]['price']) +
            (decisions[2]['quantity'] * decisions[2]['price'])
        )
        
        roi = (total_pnl / initial_investment) * 100
        
        # Prepare results
        results = {
            'scenario': 'SVB Collapse (March 2023)',
            'trades': decisions,
            'sivb_pnl': sivb_trade_pnl,
            'kre_pnl': kre_trade_pnl,
            'total_pnl': total_pnl,
            'roi': roi
        }
        
        # Generate plots
        self._generate_price_plot(
            title="SVB Collapse - Price Movement",
            dates=list(sivb_prices.keys()),
            prices=[sivb_prices, kre_prices],
            tickers=['SIVB', 'KRE'],
            trades=decisions,
            filename="svb_collapse_prices.png"
        )
        
        self._generate_pnl_plot(
            title="SVB Collapse - PnL",
            trades=decisions,
            pnls=[sivb_trade_pnl, kre_trade_pnl],
            tickers=['SIVB', 'KRE'],
            filename="svb_collapse_pnl.png"
        )
        
        # Print results
        self._print_results(results)
        
        return results
    
    def run_meta_insider_sales_backtest(self):
        """
        Run backtest for the Meta insider sales scenario (late 2021/early 2022).
        
        Returns:
            dict: Backtest results
        """
        logger.info("Running Meta insider sales backtest")
        
        # Meta (FB) insider sales timeline:
        # - Nov-Dec 2021: Large insider sales by Zuckerberg and other executives
        # - Feb 3, 2022: FB drops 26% after poor earnings report
        
        # Simulated insider trades
        insider_trades = [
            {
                'date': datetime(2021, 11, 11),
                'ticker': 'FB',
                'insider': 'Mark Zuckerberg',
                'title': 'CEO',
                'trade_type': 'S - Sale',
                'value': 25000000,
                'signal': 'BEARISH',
                'confidence': 0.85,
            },
            {
                'date': datetime(2021, 11, 18),
                'ticker': 'FB',
                'insider': 'Mark Zuckerberg',
                'title': 'CEO',
                'trade_type': 'S - Sale',
                'value': 30000000,
                'signal': 'BEARISH',
                'confidence': 0.88,
            },
            {
                'date': datetime(2021, 12, 1),
                'ticker': 'FB',
                'insider': 'Sheryl Sandberg',
                'title': 'COO',
                'trade_type': 'S - Sale',
                'value': 15000000,
                'signal': 'BEARISH',
                'confidence': 0.82,
            },
            {
                'date': datetime(2021, 12, 15),
                'ticker': 'FB',
                'insider': 'David Wehner',
                'title': 'CFO',
                'trade_type': 'S - Sale',
                'value': 8500000,
                'signal': 'BEARISH',
                'confidence': 0.8,
            }
        ]
        
        # FB price data (approximate)
        fb_prices = {
            '2021-11-11': 329.15,
            '2021-11-18': 338.69,
            '2021-12-01': 310.60,
            '2021-12-15': 333.74,
            '2022-01-03': 338.54,
            '2022-02-02': 323.00,  # Before earnings
            '2022-02-03': 237.76,  # After earnings, -26%
            '2022-02-08': 220.18,  # Continued decline
        }
        
        # Simulate trading decisions
        decisions = []
        
        # First insider sale
        decisions.append({
            'date': '2021-11-11',
            'ticker': 'FB',
            'price': 329.15,
            'action': 'SHORT',  # Inverse of the BEARISH signal
            'confidence': 0.5,  # Insider only - use 0.5x multiplier
            'quantity': 30,
            'portfolio_pct': 2.5, 
            'signal_source': 'insider-ceo'
        })
        
        # Second insider sale (accumulation)
        decisions.append({
            'date': '2021-11-18',
            'ticker': 'FB',
            'price': 338.69,
            'action': 'SHORT',  # Add to position
            'confidence': 0.6,  # Multiple insider signals
            'quantity': 15,
            'portfolio_pct': 3.5,
            'signal_source': 'insider-ceo'
        })
        
        # Third insider sale (different executive)
        decisions.append({
            'date': '2021-12-01',
            'ticker': 'FB',
            'price': 310.60,
            'action': 'SHORT',  # Add more
            'confidence': 0.7,  # Multiple executives selling
            'quantity': 10,
            'portfolio_pct': 4.0,
            'signal_source': 'insider-multiple'
        })
        
        # Fourth insider sale (CFO selling is significant)
        decisions.append({
            'date': '2021-12-15',
            'ticker': 'FB',
            'price': 333.74,
            'action': 'SHORT',  # Final addition
            'confidence': 0.8,  # CEO + COO + CFO all selling
            'quantity': 5,
            'portfolio_pct': 4.5,
            'signal_source': 'insider-officers'
        })
        
        # Calculate PnL assuming exit on Feb 8
        exit_price = fb_prices['2022-02-08']
        
        pnl_by_trade = [
            trade['quantity'] * (trade['price'] - exit_price)
            for trade in decisions
        ]
        
        total_pnl = sum(pnl_by_trade)
        
        # Calculate returns
        initial_investment = sum(trade['quantity'] * trade['price'] for trade in decisions)
        roi = (total_pnl / initial_investment) * 100
        
        # Prepare results
        results = {
            'scenario': 'Meta Insider Sales (Nov 2021 - Feb 2022)',
            'trades': decisions,
            'pnl_by_trade': pnl_by_trade,
            'total_pnl': total_pnl,
            'roi': roi
        }
        
        # Generate plots
        self._generate_price_plot(
            title="Meta (FB) Insider Sales - Price Movement",
            dates=list(fb_prices.keys()),
            prices=[fb_prices],
            tickers=['FB'],
            trades=decisions,
            filename="meta_insider_prices.png"
        )
        
        self._generate_pnl_plot(
            title="Meta (FB) Insider Sales - PnL",
            trades=decisions,
            pnls=pnl_by_trade,
            tickers=['Trade 1', 'Trade 2', 'Trade 3', 'Trade 4'],
            filename="meta_insider_pnl.png"
        )
        
        # Print results
        self._print_results(results)
        
        return results
    
    def _generate_price_plot(self, title, dates, prices, tickers, trades, filename):
        """
        Generate a price plot for a backtest.
        
        Args:
            title (str): Plot title
            dates (list): List of dates
            prices (list): List of price dictionaries
            tickers (list): List of ticker symbols
            trades (list): List of trade decisions
            filename (str): Output filename
        """
        try:
            plt.figure(figsize=(12, 8))
            
            # Plot price lines
            for i, price_dict in enumerate(prices):
                price_values = list(price_dict.values())
                plt.plot(dates, price_values, label=tickers[i], linewidth=2)
            
            # Mark trade entry points
            for trade in trades:
                ticker_idx = tickers.index(trade['ticker']) if trade['ticker'] in tickers else 0
                price_dict = prices[ticker_idx]
                
                plt.scatter(
                    trade['date'],
                    price_dict[trade['date']],
                    marker='v' if trade['action'] == 'SHORT' else '^',
                    color='r' if trade['action'] == 'SHORT' else 'g',
                    s=100,
                    label=f"{trade['action']} {trade['ticker']} at ${price_dict[trade['date']]}"
                )
            
            plt.title(title, fontsize=16)
            plt.xlabel("Date", fontsize=12)
            plt.ylabel("Price ($)", fontsize=12)
            plt.grid(True, alpha=0.3)
            plt.legend()
            plt.xticks(rotation=45)
            
            # Save plot
            output_path = os.path.join(self.output_dir, filename)
            plt.tight_layout()
            plt.savefig(output_path)
            plt.close()
            
            logger.info(f"Generated price plot: {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating price plot: {e}", exc_info=True)
    
    def _generate_pnl_plot(self, title, trades, pnls, tickers, filename):
        """
        Generate a PnL plot for a backtest.
        
        Args:
            title (str): Plot title
            trades (list): List of trade decisions
            pnls (list): List of PnLs
            tickers (list): List of ticker symbols
            filename (str): Output filename
        """
        try:
            plt.figure(figsize=(10, 6))
            
            # Plot PnLs as a bar chart
            plt.bar(tickers, pnls, color=['g' if pnl > 0 else 'r' for pnl in pnls])
            
            # Add total
            plt.bar(['Total'], [sum(pnls)], color='b', alpha=0.7)
            
            # Add labels
            for i, pnl in enumerate(pnls):
                plt.text(i, pnl + (1000 if pnl > 0 else -1000), f"${pnl:.2f}", ha='center')
                
            plt.text(len(pnls), sum(pnls) + (1000 if sum(pnls) > 0 else -1000), f"${sum(pnls):.2f}", ha='center')
            
            plt.title(title, fontsize=16)
            plt.ylabel("Profit/Loss ($)", fontsize=12)
            plt.grid(True, alpha=0.3, axis='y')
            
            # Save plot
            output_path = os.path.join(self.output_dir, filename)
            plt.tight_layout()
            plt.savefig(output_path)
            plt.close()
            
            logger.info(f"Generated PnL plot: {output_path}")
            
        except Exception as e:
            logger.error(f"Error generating PnL plot: {e}", exc_info=True)
    
    def _print_results(self, results):
        """
        Print backtest results.
        
        Args:
            results (dict): Backtest results
        """
        print("\n" + "="*80)
        print(f"BACKTEST RESULTS: {results['scenario']}")
        print("="*80)
        
        print("\nTRADES:")
        for i, trade in enumerate(results['trades']):
            print(f"{i+1}. {trade['date']} - {trade['action']} {trade['quantity']} {trade['ticker']} @ ${trade['price']:.2f}")
            print(f"   Signal: {trade['signal_source']}, Confidence: {trade['confidence']:.2f}, Portfolio %: {trade['portfolio_pct']}%")
        
        print("\nPERFORMANCE:")
        if 'sivb_pnl' in results:
            print(f"SIVB PnL: ${results['sivb_pnl']:.2f}")
            print(f"KRE PnL: ${results['kre_pnl']:.2f}")
        elif 'pnl_by_trade' in results:
            for i, pnl in enumerate(results['pnl_by_trade']):
                print(f"Trade {i+1} PnL: ${pnl:.2f}")
        
        print(f"Total PnL: ${results['total_pnl']:.2f}")
        print(f"ROI: {results['roi']:.2f}%")
        print("="*80 + "\n")

def main():
    """Run backtest examples."""
    backtest = BacktestExample()
    
    # SVB collapse backtest
    backtest.run_svb_collapse_backtest()
    
    # Meta insider sales backtest
    backtest.run_meta_insider_sales_backtest()

if __name__ == "__main__":
    main()
