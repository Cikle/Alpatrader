#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for scraping insider trading data from OpenInsider.
"""

import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)

class OpenInsiderScraper:
    """
    Class for scraping and processing insider trading data from OpenInsider.
    Focuses on CEO/CFO trades above a certain size threshold.
    """
    
    def __init__(self, min_transaction_size=200000, sectors=None, blacklist_sectors=None, db_manager=None):
        """
        Initialize the OpenInsider scraper.
        
        Args:
            min_transaction_size (float): Minimum transaction size to consider
            sectors (list): List of sectors to monitor
            blacklist_sectors (list): List of sectors to blacklist
            db_manager (DatabaseManager): Database manager for caching results
        """
        self.min_transaction_size = min_transaction_size
        self.sectors = sectors or []
        self.blacklist_sectors = blacklist_sectors or []
        self.db_manager = db_manager
        self.base_url = "http://openinsider.com"
        self.latest_url = f"{self.base_url}/latest-insider-trading/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def fetch_latest_data(self):
        """
        Extracts recent CEO/CFO trades from OpenInsider.
        
        Returns:
            list: List of dictionaries containing filtered insider trades
        """
        logger.info("Fetching insider trades from OpenInsider")
        
        # Check if we have cached data in the database
        if self.db_manager:
            cached_data = self._get_cached_data()
            if cached_data:
                logger.info(f"Using {len(cached_data)} cached insider trades")
                return cached_data
        
        try:
            # Fetch the main page with latest insider trades
            response = requests.get(self.latest_url, headers=self.headers)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main table with insider trades
            table = soup.find('table', {'class': 'tinytable'})
            if not table:
                logger.error("Could not find insider trades table")
                return []
            
            # Extract table headers and data
            headers = [th.text.strip() for th in table.find_all('th')]
            
            # Process rows
            trades = []
            rows = table.find('tbody').find_all('tr')
            
            for row in rows:
                # Extract cell data
                cells = row.find_all('td')
                if len(cells) < len(headers):
                    continue
                    
                # Parse the insider trade data
                trade_data = {}
                
                # Date
                date_str = cells[1].text.strip()
                try:
                    trade_data['date'] = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    try:
                        trade_data['date'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        trade_data['date'] = datetime.now()  # Fallback
                
                # Ticker and company
                ticker_cell = cells[3]
                ticker_link = ticker_cell.find('a')
                if ticker_link:
                    trade_data['ticker'] = ticker_link.text.strip()
                    trade_data['company'] = cells[4].text.strip()
                else:
                    continue  # Skip trades without ticker
                
                # Insider name and title
                trade_data['insider'] = cells[5].text.strip()
                trade_data['title'] = cells[6].text.strip()
                
                # Trade type
                trade_data['trade_type'] = cells[7].text.strip()
                
                # Price, quantity, and value
                try:
                    price_str = cells[8].text.strip().replace('$', '').replace(',', '')
                    trade_data['price'] = float(price_str) if price_str else 0
                    
                    qty_str = cells[9].text.strip().replace('+', '').replace(',', '')
                    trade_data['quantity'] = int(qty_str) if qty_str else 0
                    
                    value_str = cells[10].text.strip().replace('$', '').replace(',', '')
                    trade_data['value'] = float(value_str) if value_str else 0
                except (ValueError, IndexError):
                    logger.warning(f"Error parsing numeric data for {trade_data.get('ticker')}")
                    continue
                
                # Ownership change
                try:
                    ownership_str = cells[11].text.strip().replace('%', '')
                    trade_data['ownership_change'] = float(ownership_str) if ownership_str else 0
                except (ValueError, IndexError):
                    trade_data['ownership_change'] = 0
                
                # Add sector (would need to be fetched separately in a real implementation)
                trade_data['sector'] = self._get_sector(trade_data['ticker'])
                
                # Determine signal based on trade type (P = Purchase, S = Sale)
                if 'P' in trade_data['trade_type']:
                    trade_data['signal'] = 'BULLISH'
                    trade_data['confidence'] = min(1.0, trade_data['value'] / 1000000)  # Scale by size up to 1.0
                elif 'S' in trade_data['trade_type']:
                    trade_data['signal'] = 'BEARISH'
                    trade_data['confidence'] = min(1.0, trade_data['value'] / 1000000)  # Scale by size up to 1.0
                else:
                    continue  # Skip trades that are neither buys nor sells
                
                # Filter by minimum transaction size
                if trade_data['value'] < self.min_transaction_size:
                    continue
                
                # Filter by title (CEO/CFO focus)
                if not any(title in trade_data['title'].upper() for title in ['CEO', 'CFO', 'CHIEF EXECUTIVE', 'CHIEF FINANCIAL']):
                    continue
                
                # Filter by sector
                if self.sectors and trade_data['sector'] and trade_data['sector'].lower() not in [s.lower() for s in self.sectors]:
                    continue
                    
                if self.blacklist_sectors and trade_data['sector'] and trade_data['sector'].lower() in [s.lower() for s in self.blacklist_sectors]:
                    continue
                
                # Add source information
                trade_data['source'] = 'insider'
                trade_data['source_detail'] = 'OpenInsider'
                
                # Add to trades list
                trades.append(trade_data)
            
            logger.info(f"Found {len(trades)} filtered insider trades")
            
            # Cache in database if available
            if self.db_manager and trades:
                self._cache_trades(trades)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error fetching insider trades: {e}", exc_info=True)
            return []
    
    def _get_sector(self, ticker):
        """
        Get sector for a ticker symbol.
        In a real implementation, this would use a sector database or API.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            str: Sector name or None if not found
        """
        # In a real implementation, we would:
        # 1. Check a local cache/database
        # 2. If not found, query an API like IEX, Alpha Vantage, or Yahoo Finance
        # 3. Store the result in the cache
        
        # For demonstration purposes, return a random sector
        sectors = ["technology", "healthcare", "finance", "consumer", "energy", "utilities", "materials", "industrials", "biotech"]
        return random.choice(sectors)
    
    def _get_cached_data(self):
        """
        Get cached insider trades from database.
        
        Returns:
            list: List of cached insider trades
        """
        if not self.db_manager:
            return None
            
        try:
            # Get trades from the last 24 hours
            query = """
            SELECT * FROM insider_trades 
            WHERE date >= datetime('now', '-1 day')
            """
            
            trades = self.db_manager.execute_query(query)
            if trades:
                return trades
                
        except Exception as e:
            logger.error(f"Error getting cached insider trades: {e}", exc_info=True)
            
        return None
    
    def _cache_trades(self, trades):
        """
        Cache insider trades in database.
        
        Args:
            trades (list): List of insider trades to cache
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
                self.db_manager.insert('insider_trades', trade)
                
            logger.info(f"Cached {len(trades)} insider trades in database")
            
        except Exception as e:
            logger.error(f"Error caching insider trades: {e}", exc_info=True)
