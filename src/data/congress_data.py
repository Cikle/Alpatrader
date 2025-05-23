#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for scraping congressional trading data from Senate Stock Watcher.
"""

import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import re
import time
import random

logger = logging.getLogger(__name__)

class SenateScraper:
    """
    Class for scraping and processing congressional trading data from Senate Stock Watcher.
    Focuses on Senator trades below a certain size threshold.
    """
    
    def __init__(self, max_transaction_size=1000000, delay_hours=24, db_manager=None):
        """
        Initialize the Senate Stock Watcher scraper.
        
        Args:
            max_transaction_size (float): Maximum transaction size to consider
            delay_hours (int): Hours to delay after filing before considering the trade
            db_manager (DatabaseManager): Database manager for caching results
        """
        self.max_transaction_size = max_transaction_size
        self.delay_hours = delay_hours
        self.db_manager = db_manager
        self.base_url = "https://www.senatestockwatcher.com"
        self.trades_url = f"{self.base_url}/trades"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def fetch_latest_data(self):
        """
        Gets latest Senator trades from Senate Stock Watcher.
        Applies 24hr delay and $1M cap as specified.
        
        Returns:
            list: List of dictionaries containing filtered Congress trades
        """
        logger.info("Fetching Congress trades from Senate Stock Watcher")
        
        # Check if we have cached data in the database
        if self.db_manager:
            cached_data = self._get_cached_data()
            if cached_data:
                logger.info(f"Using {len(cached_data)} cached Congress trades")
                return cached_data
        
        try:
            # Fetch the main page with latest trades
            response = requests.get(self.trades_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main container with trades
            trade_cards = soup.find_all('div', {'class': 'trade-card'})
            if not trade_cards:
                logger.error("Could not find Congress trades")
                return []
            
            # Process trades
            trades = []
            
            for card in trade_cards:
                # Extract trade data
                trade_data = {}
                
                # Date
                date_elem = card.find('div', {'class': 'filing-date'})
                if date_elem:
                    date_str = date_elem.text.strip()
                    try:
                        # Handle different date formats
                        match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
                        if match:
                            month, day, year = match.groups()
                            trade_data['date'] = datetime(int(year), int(month), int(day))
                        else:
                            # Try another format
                            trade_data['date'] = datetime.strptime(date_str, '%B %d, %Y')
                    except (ValueError, AttributeError):
                        # Default to current date if parsing fails
                        trade_data['date'] = datetime.now()
                else:
                    trade_data['date'] = datetime.now()
                
                # Check if the trade meets the delay requirement
                time_since_filing = datetime.now() - trade_data['date']
                if time_since_filing.total_seconds() < self.delay_hours * 3600:
                    continue  # Skip trades that are too recent
                
                # Politician name
                politician_elem = card.find('div', {'class': 'politician-name'})
                trade_data['politician'] = politician_elem.text.strip() if politician_elem else "Unknown"
                
                # Ticker and company
                ticker_elem = card.find('div', {'class': 'ticker'})
                company_elem = card.find('div', {'class': 'company-name'})
                
                if ticker_elem:
                    # Extract ticker from element
                    ticker_text = ticker_elem.text.strip()
                    # Clean up ticker (remove $ symbol if present)
                    trade_data['ticker'] = ticker_text.replace('$', '').strip().upper()
                else:
                    continue  # Skip trades without ticker
                
                trade_data['company'] = company_elem.text.strip() if company_elem else "Unknown"
                
                # Transaction type and value
                transaction_elem = card.find('div', {'class': 'transaction-type'})
                value_elem = card.find('div', {'class': 'value'})
                
                if transaction_elem:
                    trade_data['transaction_type'] = transaction_elem.text.strip()
                else:
                    continue  # Skip trades without transaction type
                
                # Parse value
                if value_elem:
                    value_text = value_elem.text.strip()
                    # Extract value range (e.g., "$15,001 - $50,000")
                    range_match = re.search(r'\$([0-9,]+)(?:\s*-\s*\$([0-9,]+))?', value_text)
                    
                    if range_match:
                        # Get the lower and upper bounds
                        lower_bound = range_match.group(1).replace(',', '')
                        upper_bound = range_match.group(2).replace(',', '') if range_match.group(2) else lower_bound
                        
                        # Calculate average value
                        try:
                            lower = float(lower_bound)
                            upper = float(upper_bound)
                            trade_data['estimated_value'] = (lower + upper) / 2
                        except ValueError:
                            trade_data['estimated_value'] = 0
                    else:
                        # Try to extract a single value
                        value_match = re.search(r'\$([0-9,]+)', value_text)
                        if value_match:
                            try:
                                trade_data['estimated_value'] = float(value_match.group(1).replace(',', ''))
                            except ValueError:
                                trade_data['estimated_value'] = 0
                        else:
                            trade_data['estimated_value'] = 0
                else:
                    trade_data['estimated_value'] = 0
                
                # Filter by maximum transaction size
                if trade_data['estimated_value'] > self.max_transaction_size:
                    continue
                
                # Asset type (stock, option, etc.)
                asset_elem = card.find('div', {'class': 'asset-type'})
                trade_data['asset_type'] = asset_elem.text.strip() if asset_elem else "Stock"
                
                # Skip if not a stock
                if not any(asset_type in trade_data['asset_type'].lower() for asset_type in ['stock', 'common', 'share']):
                    continue
                
                # Determine signal based on transaction type
                if any(buy_term in trade_data['transaction_type'].lower() for buy_term in ['purchase', 'buy']):
                    trade_data['signal'] = 'BULLISH'
                    # Scale confidence by value, max 0.8 since Congress trades are less reliable than insider
                    trade_data['confidence'] = min(0.8, trade_data['estimated_value'] / self.max_transaction_size)
                elif any(sell_term in trade_data['transaction_type'].lower() for sell_term in ['sale', 'sell']):
                    trade_data['signal'] = 'BEARISH'
                    trade_data['confidence'] = min(0.8, trade_data['estimated_value'] / self.max_transaction_size)
                else:
                    continue  # Skip trades that are neither buys nor sells
                
                # Add source information
                trade_data['source'] = 'congress'
                trade_data['source_detail'] = 'Senate Stock Watcher'
                
                # Add to trades list
                trades.append(trade_data)
            
            logger.info(f"Found {len(trades)} filtered Congress trades")
            
            # Cache in database if available
            if self.db_manager and trades:
                self._cache_trades(trades)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching Congress trades: {e}", exc_info=True)
            return []
    
    def _get_cached_data(self):
        """
        Get cached Congress trades from database.
        
        Returns:
            list: List of cached Congress trades
        """
        if not self.db_manager:
            return None
            
        try:
            # Get trades from the last week (Congress trades are less frequent)
            query = """
            SELECT * FROM congress_trades 
            WHERE date >= datetime('now', '-7 day')
            """
            
            trades = self.db_manager.execute_query(query)
            if trades:
                return trades
                
        except Exception as e:
            logger.error(f"Error getting cached Congress trades: {e}", exc_info=True)
            
        return None
    
    def _cache_trades(self, trades):
        """
        Cache Congress trades in database.
        
        Args:
            trades (list): List of Congress trades to cache
        """
        if not self.db_manager:
            return
            
        try:
            for trade in trades:
                # Convert datetime to string if needed
                if isinstance(trade.get('date'), datetime):
                    trade['date'] = trade['date'].strftime('%Y-%m-%d %H:%M:%S')
                    
                # Add creation timestamp
                trade['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Insert into database
                self.db_manager.insert('congress_trades', trade)
                
            logger.info(f"Cached {len(trades)} Congress trades in database")
            
        except Exception as e:
            logger.error(f"Error caching Congress trades: {e}", exc_info=True)
