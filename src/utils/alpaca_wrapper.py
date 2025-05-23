#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper for the Alpaca API.
"""

import logging
import time
from datetime import datetime, timedelta
import alpaca_trade_api as tradeapi

logger = logging.getLogger(__name__)

class AlpacaWrapper:
    """
    Wrapper for Alpaca API to manage paper trading.
    """
    
    def __init__(self, api_key=None, api_secret=None, base_url=None, data_url=None):
        """
        Initialize the Alpaca API wrapper.
        
        Args:
            api_key (str): Alpaca API key
            api_secret (str): Alpaca API secret
            base_url (str): Alpaca API base URL
            data_url (str): Alpaca data URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url or "https://paper-api.alpaca.markets"
        self.data_url = data_url or "https://data.alpaca.markets"
        
        # Initialize API
        self.api = self._init_api()
        
    def _init_api(self):
        """
        Initialize the Alpaca API client.
        
        Returns:
            alpaca_trade_api.REST: Alpaca API client or None if initialization fails
        """
        try:
            if not self.api_key or not self.api_secret:
                logger.error("Alpaca API key or secret not provided")
                return None
                
            # Create API client
            api = tradeapi.REST(
                key_id=self.api_key,
                secret_key=self.api_secret,
                base_url=self.base_url,
                api_version='v2'
            )
            
            # Test connection
            account = api.get_account()
            logger.info(f"Connected to Alpaca API for account {account.id}")
            
            return api
            
        except Exception as e:
            logger.error(f"Error initializing Alpaca API: {e}", exc_info=True)
            return None
            
    def get_account(self):
        """
        Get account information.
        
        Returns:
            alpaca_trade_api.entity.Account: Account object or None if error
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None
                
            return self.api.get_account()
            
        except Exception as e:
            logger.error(f"Error getting account: {e}", exc_info=True)
            return None
            
    def get_positions(self):
        """
        Get current positions.
        
        Returns:
            list: List of positions
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return []
                
            return self.api.list_positions()
            
        except Exception as e:
            logger.error(f"Error getting positions: {e}", exc_info=True)
            return []
            
    def get_last_price(self, symbol):
        """
        Get last price for a symbol.
        
        Args:
            symbol (str): Symbol to get price for
            
        Returns:
            float: Last price or None if error
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None
                
            # Get bars
            bars = self.api.get_latest_bar(symbol)
            
            if bars:
                return float(bars.c)
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting last price for {symbol}: {e}", exc_info=True)
            return None
            
    def is_market_open(self):
        """
        Check if market is open.
        
        Returns:
            bool: True if market is open, False otherwise
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return False
                
            clock = self.api.get_clock()
            return clock.is_open
            
        except Exception as e:
            logger.error(f"Error checking if market is open: {e}", exc_info=True)
            return False
            
    def submit_order(self, symbol, qty, side, type, time_in_force):
        """
        Submit an order.
        
        Args:
            symbol (str): Symbol to trade
            qty (int): Quantity to trade
            side (str): 'buy' or 'sell'
            type (str): 'market', 'limit', etc.
            time_in_force (str): 'day', 'gtc', etc.
            
        Returns:
            alpaca_trade_api.entity.Order: Order object or None if error
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None
                
            # Submit order
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=type,
                time_in_force=time_in_force
            )
            
            logger.info(f"Submitted {side} order for {qty} shares of {symbol}")
            return order
            
        except Exception as e:
            logger.error(f"Error submitting order for {symbol}: {e}", exc_info=True)
            return None
            
    def wait_for_order(self, order_id, timeout=60):
        """
        Wait for an order to be filled.
        
        Args:
            order_id (str): Order ID to wait for
            timeout (int): Timeout in seconds
            
        Returns:
            alpaca_trade_api.entity.Order: Filled order or None if timeout
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None
                
            # Wait for order to be filled
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                order = self.api.get_order(order_id)
                
                if order.status == 'filled':
                    logger.info(f"Order {order_id} filled")
                    return order
                    
                elif order.status == 'rejected' or order.status == 'canceled':
                    logger.error(f"Order {order_id} {order.status}")
                    return order
                    
                # Wait 1 second before checking again
                time.sleep(1)
                
            logger.warning(f"Timeout waiting for order {order_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error waiting for order {order_id}: {e}", exc_info=True)
            return None
            
    def get_bars(self, symbol, timeframe='1D', start=None, end=None, limit=None):
        """
        Get bars for a symbol.
        
        Args:
            symbol (str): Symbol to get bars for
            timeframe (str): Timeframe (e.g., '1D', '1H')
            start (datetime): Start datetime
            end (datetime): End datetime
            limit (int): Limit number of bars
            
        Returns:
            list: List of bars
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return []
                
            # Set default dates if not provided
            if not end:
                end = datetime.now()
            if not start:
                start = end - timedelta(days=30)
                
            # Convert to string format
            start_str = start.isoformat()
            end_str = end.isoformat()
            
            # Get bars
            bars = self.api.get_bars(
                symbol,
                timeframe,
                start=start_str,
                end=end_str,
                limit=limit
            ).df
            
            return bars
            
        except Exception as e:
            logger.error(f"Error getting bars for {symbol}: {e}", exc_info=True)
            return []
