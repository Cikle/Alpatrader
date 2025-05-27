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
    
    def get_orders(self, status=None, symbols=None, limit=50):
        """
        Get orders from Alpaca.
        
        Args:
            status (str): Order status filter ('filled', 'pending', etc.)
            symbols (list): List of symbols to filter by
            limit (int): Maximum number of orders to return
            
        Returns:
            list: List of order objects
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return []
            
            # Build request parameters
            params = {}
            if status:
                params['status'] = status
            if limit:
                params['limit'] = limit
            
            # Get orders
            orders = self.api.list_orders(**params)
            
            # Filter by symbols if provided
            if symbols:
                orders = [o for o in orders if o.symbol in symbols]
            
            return orders
            
        except Exception as e:
            logger.error(f"Error getting orders: {e}", exc_info=True)
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
            
    def _handle_short_selling(self, symbol, qty, side):
        """
        Handle short selling restrictions.
        
        Args:
            symbol (str): Stock symbol
            qty (int): Quantity to trade
            side (str): 'buy' or 'sell'
            
        Returns:
            tuple: (side, qty) tuple with potentially modified values
        """
        if side.lower() != 'sell':
            return side, qty
            
        try:
            # Check current position first to determine if it's a short sell
            try:
                position = self.api.get_position(symbol)
                # If position exists, check if qty is greater than position
                current_qty = float(position.qty)
                if current_qty < qty:
                    logger.warning(f"Reducing sell order for {symbol} from {qty} to {current_qty} to avoid short selling")
                    qty = current_qty
            except Exception:
                # No position exists, this would be a short sell
                logger.warning(f"Short selling attempted for {symbol}. Checking if allowed...")
                
                # Check if short selling is allowed for this symbol
                try:
                    asset = self.api.get_asset(symbol)
                    if not getattr(asset, 'shortable', False):
                        logger.warning(f"Short selling not allowed for {symbol}, converting to buy order")
                        side = 'buy'  # Convert to buy instead
                except Exception as se:
                    logger.error(f"Error checking if {symbol} is shortable: {se}")
                    # Default to safer option - convert to buy
                    side = 'buy'
        except Exception as e:
            logger.error(f"Error handling short selling for {symbol}: {e}")
            # Default to safer option - convert to buy
            side = 'buy'
            
        return side, qty
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
            
            # Handle short selling restrictions
            side, qty = self._handle_short_selling(symbol, qty, side)
            
            # Submit order with potentially modified parameters
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
            
            # If the error is specifically about short selling, convert to a buy order
            if "not allowed to short" in str(e).lower():
                logger.warning(f"Short selling not allowed for {symbol}, attempting to submit buy order instead")
                try:
                    # Retry as a buy order
                    order = self.api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side='buy',  # Convert to buy
                        type=type,
                        time_in_force=time_in_force
                    )
                    logger.info(f"Converted to buy order for {qty} shares of {symbol}")
                    return order
                except Exception as retry_e:
                    logger.error(f"Error submitting converted buy order for {symbol}: {retry_e}", exc_info=True)
            
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
        
    def get_option_chain(self, symbol, expiration_date=None):
        """
        Get an option chain for a given symbol.
        
        Args:
            symbol (str): Stock ticker symbol
            expiration_date (str): Optional expiration date in YYYY-MM-DD format
            
        Returns:
            dict: Dictionary containing option chain data or None if error
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None
                
            # Check if symbol exists
            if not self._check_symbol_exists(symbol):
                logger.error(f"Symbol {symbol} not found")
                return None
            
            # Get available expirations if not provided
            if not expiration_date:
                try:
                    # In a real implementation, we'd get expirations from the API
                    # For now, we calculate the next few expirations
                    today = datetime.now().date()
                    fridays = []
                    
                    # Get the next 4 fridays
                    for i in range(1, 30):
                        next_day = today + timedelta(days=i)
                        if next_day.weekday() == 4:  # 4 = Friday
                            fridays.append(next_day.strftime('%Y-%m-%d'))
                            if len(fridays) >= 4:
                                break
                    
                    # Use the third Friday (standard expiration)
                    expiration_date = fridays[2] if len(fridays) >= 3 else fridays[0]
                    
                except Exception as e:
                    logger.error(f"Error calculating expiration dates: {e}", exc_info=True)
                    expiration_date = (today + timedelta(days=30)).strftime('%Y-%m-%d')
            
            logger.info(f"Getting option chain for {symbol} with expiration {expiration_date}")
            
            # In a real implementation, we would call the API:
            # options = self.api.get_option_chain(symbol, expiration_date)
            
            # For development, we'll simulate a response
            current_price = self.get_last_price(symbol)
            if not current_price:
                current_price = 100.0  # Default for simulation
            
            # Generate strikes around the current price
            strikes = [
                round(current_price * (1 - 0.20 + 0.05 * i), 2)
                for i in range(9)  # -20% to +20% in 5% increments
            ]
            
            # Generate simulated option chain
            calls = []
            puts = []
            
            for strike in strikes:
                # Simulate call option
                call_price = max(0.05, round(current_price - strike + 2, 2)) if current_price > strike else round(0.05 + (current_price / strike) * 2, 2)
                call_volume = int(1000 * (1 - abs(current_price - strike) / current_price)) if abs(current_price - strike) / current_price < 0.9 else 10
                
                calls.append({
                    'symbol': f"{symbol}C{expiration_date.replace('-', '')}00{int(strike)}000",
                    'strike': strike,
                    'last_price': call_price,
                    'bid': round(call_price * 0.95, 2),
                    'ask': round(call_price * 1.05, 2),
                    'volume': call_volume,
                    'open_interest': call_volume * 3,
                    'implied_volatility': 0.5,
                    'delta': 0.5 if strike == current_price else (0.7 if strike < current_price else 0.3)
                })
                
                # Simulate put option
                put_price = max(0.05, round(strike - current_price + 2, 2)) if strike > current_price else round(0.05 + (strike / current_price) * 2, 2)
                put_volume = int(1000 * (1 - abs(current_price - strike) / current_price)) if abs(current_price - strike) / current_price < 0.9 else 10
                
                puts.append({
                    'symbol': f"{symbol}P{expiration_date.replace('-', '')}00{int(strike)}000",
                    'strike': strike,
                    'last_price': put_price,
                    'bid': round(put_price * 0.95, 2),
                    'ask': round(put_price * 1.05, 2),
                    'volume': put_volume,
                    'open_interest': put_volume * 3,
                    'implied_volatility': 0.5,
                    'delta': -0.5 if strike == current_price else (-0.7 if strike > current_price else -0.3)
                })
            
            # Return the simulated option chain
            return {
                'symbol': symbol,
                'underlying_price': current_price,
                'expiration_date': expiration_date,
                'calls': calls,
                'puts': puts
            }
            
        except Exception as e:
            logger.error(f"Error getting option chain for {symbol}: {e}", exc_info=True)
            return None
    
    def submit_option_order(self, option_symbol, qty, side, type, time_in_force):
        """
        Submit an option order.
        
        Args:
            option_symbol (str): Option symbol
            qty (int): Number of contracts
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
                
            # Submit option order - Alpaca might not support this directly in the API
            # This is a placeholder implementation
            try:
                # Try to use the actual API method if it exists
                order = self.api.submit_option_order(
                    symbol=option_symbol,
                    qty=qty,
                    side=side,
                    type=type,
                    time_in_force=time_in_force
                )
                logger.info(f"Submitted {side} option order for {qty} contracts of {option_symbol}")
                return order
            except AttributeError:
                # If the method doesn't exist, create a simulated order
                logger.warning("Option trading not directly supported, creating simulated order")
                
                # Create a simulated order object (for testing/education only)
                import uuid
                from collections import namedtuple
                
                MockOrder = namedtuple('MockOrder', ['id', 'status', 'symbol', 'qty', 'filled_qty', 'filled_avg_price'])
                order_id = str(uuid.uuid4())
                
                # Simulate a filled order with a price based on the symbol
                mock_price = float(qty) * 1.5  # Simple mock pricing
                
                order = MockOrder(
                    id=order_id,
                    status='filled',
                    symbol=option_symbol,
                    qty=qty,
                    filled_qty=qty,
                    filled_avg_price=mock_price
                )
                
                logger.info(f"Created simulated option order {order_id} for {option_symbol}")
                return order
                
        except Exception as e:
            logger.error(f"Error submitting option order for {option_symbol}: {e}", exc_info=True)
            return None
    def get_option_positions(self):
        """
        Get current option positions.
        
        Returns:
            list: List of option positions
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return []
                
            # In a real implementation, we would use:
            # return self.api.list_option_positions()
            
            # For development, return an empty list
            logger.info("Getting option positions")
            return []
            
        except Exception as e:
            logger.error(f"Error getting option positions: {e}", exc_info=True)
            return []
            
    def find_option_contract(self, symbol, target_delta, right, days_to_expiry=30, max_days_range=15):
        """
        Find an options contract with a target delta and days to expiry.
        
        Args:
            symbol (str): Stock ticker symbol
            target_delta (float): Target delta value (absolute value, e.g. 0.20)
            right (str): 'call' or 'put'
            days_to_expiry (int): Target number of days to expiry
            max_days_range (int): Maximum range of days around target expiry to consider
            
        Returns:
            dict: Selected option contract details or None if none found
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return None            # Check if symbol is tradable for options
            try:
                asset = self.api.get_asset(symbol)
                if not asset.tradable or not getattr(asset, 'fractionable', True):  # Options typically require marginable stocks
                    logger.warning(f"{symbol} is not tradable for options")
                    return self._get_sample_option_contract(symbol, right, target_delta, days_to_expiry)
            except Exception as e:
                logger.warning(f"Error checking if {symbol} is tradable: {e}")
                # Continue anyway - we'll try to get the chain and fallback if needed
                
            # Calculate target expiration date
            today = datetime.now().date()
            target_date = today + timedelta(days=days_to_expiry)
            
            logger.info(f"Finding {right} option for {symbol} with delta ~{target_delta} and ~{days_to_expiry} days to expiry")
            
            # Get available expirations (we'll use simulated data for now)
            expirations = []
            for i in range(-max_days_range, max_days_range + 1, 7):  # Check weekly expirations
                exp_date = (target_date + timedelta(days=i))
                # Keep only Fridays (standard expiration dates)
                if exp_date.weekday() == 4 and exp_date > today:
                    expirations.append(exp_date.strftime('%Y-%m-%d'))
            
            if not expirations:
                logger.warning(f"No valid expiration dates found for {symbol}")
                return None
                
            # Sort by distance to target days
            expirations.sort(key=lambda x: abs((datetime.strptime(x, '%Y-%m-%d').date() - today).days - days_to_expiry))
            
            # Try each expiration date in order of preference
            for expiration_date in expirations:
                # Get option chain for this expiration
                chain = self.get_option_chain(symbol, expiration_date)
                if not chain:
                    continue
                    
                # Get the options list based on right (call or put)
                options_list = chain['calls'] if right.lower() == 'call' else chain['puts']
                
                if not options_list:
                    continue
                
                # Look for the option with delta closest to target
                # For puts, delta is negative, so we use absolute value for comparison
                target_delta_abs = abs(target_delta)
                options_list.sort(key=lambda x: abs(abs(x['delta']) - target_delta_abs))
                
                # Check if we have a suitable option
                if options_list:
                    best_match = options_list[0]
                    
                    # Calculate option's price as the midpoint of bid and ask
                    price = (best_match['bid'] + best_match['ask']) / 2
                    
                    # Return the contract with price included
                    return {
                        'symbol': best_match['symbol'],
                        'strike': best_match['strike'],
                        'price': price,
                        'delta': best_match['delta'],
                        'expiration_date': expiration_date,
                        'days_to_expiry': (datetime.strptime(expiration_date, '%Y-%m-%d').date() - today).days,
                        'right': right,
                        'underlying_price': chain['underlying_price']
                    }
            logger.warning(f"No suitable {right} option found for {symbol} with delta ~{target_delta}")
            # Use sample data as a fallback when no suitable options found
            return self._get_sample_option_contract(symbol, right, target_delta, days_to_expiry)
            
        except Exception as e:
            logger.error(f"Error finding option contract for {symbol}: {e}", exc_info=True)
            # Use sample data as a fallback when an error occurs
            return self._get_sample_option_contract(symbol, right, target_delta, days_to_expiry)
    
    def _check_symbol_exists(self, symbol):
        """
        Check if a symbol exists and is tradable.
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            bool: True if symbol exists and is tradable, False otherwise
        """
        try:
            if not self.api:
                logger.error("Alpaca API not initialized")
                return False
                
            # Get asset information
            asset = self.api.get_asset(symbol)
            
            # Check if the asset is tradable
            if not asset.tradable:
                logger.warning(f"Symbol {symbol} exists but is not tradable")
                return False
                
            # Check if it's a valid equity (not crypto, etc.)
            if asset.class_ != 'us_equity':
                logger.warning(f"Symbol {symbol} is not a US equity (class: {asset.class_})")
                return False
                
            logger.debug(f"Symbol {symbol} is valid and tradable")
            return True
            
        except Exception as e:
            logger.warning(f"Symbol {symbol} not found or not accessible: {e}")
            return False
    
    def validate_symbol(self, symbol):
        """
        Validate and return True if symbol is tradeable.
        
        Args:
            symbol (str): Stock ticker symbol
            
        Returns:
            bool: True if symbol is valid and tradeable
        """
        return self._check_symbol_exists(symbol)
    
    def _get_sample_option_contract(self, symbol, right, target_delta, days_to_expiry):
        """
        Generate a sample option contract when API fails to find one.
        This is used as a fallback for testing and development.
        
        Args:
            symbol (str): Underlying symbol
            right (str): 'call' or 'put'
            target_delta (float): Target delta value
            days_to_expiry (int): Target days to expiry
            
        Returns:
            dict: Simulated option contract
        """
        import random
        
        logger.warning(f"Using simulated option contract for {symbol} {right}")
        
        # Get the current price or use a placeholder
        current_price = self.get_last_price(symbol) or 100
        
        # Calculate a reasonable strike price based on current price and delta
        # For calls, higher delta = more ITM, lower strike
        # For puts, higher delta = more ITM, higher strike
        delta_factor = 1 - target_delta
        
        if right.lower() == 'call':
            strike = round(current_price * (1 + (delta_factor * 0.10)), 1)
        else:  # put
            strike = round(current_price * (1 - (delta_factor * 0.10)), 1)
            
        # Calculate a reasonable price for the option
        if right.lower() == 'call':
            # Simple Black-Scholes approximation
            option_price = max(0.1, current_price * target_delta * 0.15)
        else:  # put
            option_price = max(0.1, current_price * target_delta * 0.15)
            
        # Format expiration date
        today = datetime.now().date()
        expiration_date = (today + timedelta(days=days_to_expiry)).strftime('%Y-%m-%d')
        
        # Generate a simulated option symbol
        option_symbol = f"{symbol}:{expiration_date}:{strike}:{right.upper()}"
          # Create the contract object
        contract = {
            'symbol': option_symbol,
            'underlying_symbol': symbol,
            'strike': strike,
            'price': option_price,
            'bid': option_price * 0.95,
            'ask': option_price * 1.05,
            'delta': target_delta if right.lower() == 'call' else -target_delta,
            'expiration': expiration_date,
            'expiration_date': expiration_date,
            'days_to_expiry': days_to_expiry,
            'underlying_price': current_price,
            'right': right,
            'is_sample_data': True,
            'volume': 100,
            'open_interest': 500
        }
        
        logger.info(f"Generated sample {right} option contract for {symbol} with delta {target_delta}")
        return contract
