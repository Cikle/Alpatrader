#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Congress data scraper using Senate Stock Watcher API.
This module scrapes Congress trading data and provides signals.
"""

import logging
import requests
import json
from datetime import datetime, timedelta
from src.utils.api_error_handler import APIErrorHandler

logger = logging.getLogger(__name__)

class SenateScraper:
    """
    Scraper for Senate Stock Watcher data.
    """
    
    def __init__(self, max_transaction_size=1000000, delay_hours=24, db_manager=None):
        """
        Initialize the SenateScraper.
        
        Args:
            max_transaction_size (float): Maximum transaction size to consider
            delay_hours (int): Hours to delay after filing before considering the trade
            db_manager: Database manager instance
        """
        self.max_transaction_size = max_transaction_size
        self.delay_hours = delay_hours
        self.db_manager = db_manager
        self.api_url = "https://senatestockwatcher.com/api"
        self.retry_count = 3
        self.timeout = 10  # seconds
        
        logger.info("SenateScraper initialized")
    
    def fetch_latest_data(self):
        """
        Fetch latest Congress trading data.
        
        Returns:
            list: List of processed Congress trades
        """
        logger.info("Fetching latest Congress data")
        
        try:
            # Try to fetch data from API
            trades = self._fetch_from_api()
            
            if trades and len(trades) > 0:
                logger.info(f"Successfully fetched {len(trades)} Congress trades")
                
                # Store in database if available
                if self.db_manager:
                    self._store_in_database(trades)
                
                return trades
            else:
                logger.warning("No Congress trades found or empty response from API")
                return self._get_sample_data()
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching Congress data: {e}")
            return self._get_sample_data()
    
    def _fetch_from_api(self):
        """
        Internal method to fetch data from Senate Stock Watcher API.
        
        Returns:
            list: List of processed Congress trades
        """
        processed_trades = []
        
        for attempt in range(self.retry_count):
            try:
                logger.info(f"Attempting to fetch Congress data (Attempt {attempt + 1}/{self.retry_count})")
                
                # Endpoint for recent trades
                endpoint = f"{self.api_url}/trades/recent"
                
                response = requests.get(endpoint, timeout=self.timeout)
                
                if response.status_code == 200:
                    trades = response.json()
                    
                    # Process each trade
                    for trade in trades:
                        processed_trade = self._process_trade(trade)
                        if processed_trade:
                            processed_trades.append(processed_trade)
                    
                    return processed_trades
                    
                elif response.status_code == 404:
                    logger.warning(f"Senate Stock Watcher API returned 404. Endpoint may have changed: {endpoint}")
                    break
                    
                else:
                    logger.warning(f"Senate Stock Watcher API returned status {response.status_code}")
            
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {e}")
                
            # Wait before retry if not the last attempt
            if attempt < self.retry_count - 1:
                import time
                time.sleep(2)
        
        logger.warning("All attempts to fetch Congress data failed")
        return []
    
    def _process_trade(self, trade):
        """
        Process a raw trade from the API into standard format.
        
        Args:
            trade (dict): Raw trade data from API
            
        Returns:
            dict: Processed trade or None if invalid
        """
        try:
            # Extract relevant fields (adapt based on actual API response)
            ticker = trade.get('ticker')
            transaction_type = trade.get('transaction_type')
            value = trade.get('amount')
            
            # Skip if missing critical information
            if not ticker or not transaction_type:
                logger.debug(f"Skipping trade with missing data: {trade}")
                return None
            
            # Convert date string to datetime
            trade_date = datetime.strptime(trade.get('transaction_date', ''), "%Y-%m-%d")
            
            # Skip if trade is too recent (respect delay_hours)
            if datetime.now() - trade_date < timedelta(hours=self.delay_hours):
                logger.debug(f"Skipping trade that is too recent: {trade_date}")
                return None
            
            # Skip if the value is above our max transaction size
            if value and float(value) > self.max_transaction_size:
                logger.debug(f"Skipping trade with value {value} > {self.max_transaction_size}")
                return None
            
            # Determine signal (buy = bullish, sell = bearish)
            is_buy = "buy" in transaction_type.lower() or "purchase" in transaction_type.lower()
            signal = 'BULLISH' if is_buy else 'BEARISH'
            
            # Calculate confidence based on value relative to max
            confidence = min(0.9, value / self.max_transaction_size if value else 0.5)
            
            return {
                'date': trade_date,
                'politician': trade.get('senator', 'Unknown'),
                'ticker': ticker,
                'company': trade.get('asset_description', ticker),
                'transaction_type': transaction_type,
                'estimated_value': value,
                'asset_type': trade.get('asset_type', 'Stock'),
                'signal': signal,
                'confidence': confidence,
                'source': 'congress',
                'source_detail': 'Senate Stock Watcher',
                'is_sample_data': False
            }
            
        except Exception as e:
            logger.error(f"Error processing trade: {e}")
            return None
    
    def _store_in_database(self, trades):
        """
        Store trades in the database.
        
        Args:
            trades (list): List of processed trades
        """
        if not self.db_manager:
            return
        
        try:
            for trade in trades:
                self.db_manager.insert_congress_trade(trade)
            logger.info(f"Stored {len(trades)} Congress trades in database")
        except Exception as e:
            logger.error(f"Error storing Congress trades in database: {e}")
    
    def _get_sample_data(self):
        """
        Generate sample Congress trade data for testing/fallback purposes.
        
        Returns:
            list: List of sample Congress trades
        """
        return APIErrorHandler.handle_congress_api_error(
            max_transaction_size=self.max_transaction_size,
            delay_hours=self.delay_hours
        )
