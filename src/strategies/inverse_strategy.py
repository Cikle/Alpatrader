#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for implementing the inverse trading strategy.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class InverseStrategy:
    """
    Class for implementing inverse trading strategy based on signals.
    Takes the opposite side of insider, congress, and news signals.
    """
    
    def __init__(self, alpaca, signal_processor, config):
        """
        Initialize the inverse trading strategy.
        
        Args:
            alpaca (AlpacaWrapper): Alpaca API wrapper
            signal_processor (SignalProcessor): Signal processor
            config (ConfigParser): Configuration object
        """
        self.alpaca = alpaca
        self.signal_processor = signal_processor
        self.config = config
        
        # Read portfolio parameters from config
        self.max_position_size_percent = config.getfloat('trading', 'max_position_size_percent', fallback=5.0)
        
        # Portfolio constraints
        self.max_positions = 10
        self.min_cash_reserve = 0.2  # Keep at least 20% in cash
        
    def execute_trades(self, signals):
        """
        Execute trades based on the provided signals.
        
        Args:
            signals (list): List of signals with trading instructions
            
        Returns:
            list: List of executed trades
        """
        if not signals:
            logger.info("No signals to execute trades")
            return []
            
        logger.info(f"Executing trades for {len(signals)} signals")
        
        # Get account information
        account = self.alpaca.get_account()
        if not account:
            logger.error("Could not get account information")
            return []
            
        # Calculate available equity for new positions
        portfolio_value = float(account.equity)
        buying_power = float(account.buying_power)
        
        # Get existing positions
        positions = self.alpaca.get_positions()
        
        # Calculate max new position size
        max_position_value = portfolio_value * (self.max_position_size_percent / 100)
        
        executed_trades = []
        
        # Sort signals by confidence and source count
        signals.sort(key=lambda x: (x.get('source_count', 0), x.get('confidence', 0)), reverse=True)
        
        for signal in signals:
            ticker = signal.get('ticker')
            signal_direction = signal.get('signal')
            confidence = signal.get('confidence', 0)
            position_multiplier = signal.get('position_multiplier', 1.0)
            
            # Skip low confidence signals
            if confidence < 0.5:
                logger.info(f"Skipping low confidence signal for {ticker}")
                continue
                
            # Check if we already have a position in this ticker
            existing_position = next((p for p in positions if p.symbol == ticker), None)
            
            # Calculate position size based on signal strength
            position_value = max_position_value * position_multiplier
            
            # Get current price
            current_price = self.alpaca.get_last_price(ticker)
            if not current_price:
                logger.error(f"Could not get price for {ticker}")
                continue
                
            # Calculate number of shares
            shares = int(position_value / current_price)
            
            if shares <= 0:
                logger.warning(f"Calculated position size for {ticker} is too small")
                continue
                
            # Determine action based on signal and existing position
            if existing_position:
                # We already have a position, check if we need to adjust it
                current_shares = int(existing_position.qty)
                current_side = "LONG" if current_shares > 0 else "SHORT"
                
                # If signal matches our current position, check if we need to add more
                if (signal_direction == "BULLISH" and current_side == "LONG") or (signal_direction == "BEARISH" and current_side == "SHORT"):
                    # If our position is smaller than the new target, add more
                    target_shares = shares
                    
                    if abs(current_shares) < target_shares:
                        # Add to position
                        action = "BUY" if current_side == "LONG" else "SELL"
                        additional_shares = target_shares - abs(current_shares)
                        
                        # Execute trade
                        trade_result = self._execute_trade(ticker, action, additional_shares)
                        if trade_result:
                            trade_result['signal'] = signal
                            executed_trades.append(trade_result)
                            
                # If signal is opposite our current position, close it and open new one
                else:
                    # Close current position
                    close_action = "SELL" if current_side == "LONG" else "BUY"
                    
                    # Execute close
                    close_result = self._execute_trade(ticker, close_action, abs(current_shares))
                    
                    # Open new position
                    new_action = "BUY" if signal_direction == "BULLISH" else "SELL"
                    
                    # Execute new position
                    trade_result = self._execute_trade(ticker, new_action, shares)
                    if trade_result:
                        trade_result['signal'] = signal
                        executed_trades.append(trade_result)
            else:
                # No existing position, open a new one
                action = "BUY" if signal_direction == "BULLISH" else "SELL"
                
                # Execute trade
                trade_result = self._execute_trade(ticker, action, shares)
                if trade_result:
                    trade_result['signal'] = signal
                    executed_trades.append(trade_result)
                    
        logger.info(f"Executed {len(executed_trades)} trades")
        return executed_trades
                
    def _execute_trade(self, ticker, action, quantity):
        """
        Execute a trade on Alpaca.
        
        Args:
            ticker (str): Stock ticker symbol
            action (str): 'BUY' or 'SELL'
            quantity (int): Number of shares
            
        Returns:
            dict: Trade execution details or None if failed
        """
        if quantity <= 0:
            logger.warning(f"Invalid quantity {quantity} for {ticker}")
            return None
            
        try:
            logger.info(f"Executing {action} order for {quantity} shares of {ticker}")
            
            # Submit order to Alpaca
            order = self.alpaca.submit_order(
                symbol=ticker,
                qty=quantity,
                side=action.lower(),
                type='market',
                time_in_force='day'
            )
            
            if not order:
                logger.error(f"Failed to submit order for {ticker}")
                return None
                
            # Wait for fill
            filled_order = self.alpaca.wait_for_order(order.id)
            
            if not filled_order or filled_order.status != 'filled':
                logger.error(f"Order for {ticker} was not filled")
                return None
                
            fill_price = float(filled_order.filled_avg_price)
            filled_qty = int(filled_order.filled_qty)
            total_value = fill_price * filled_qty
            
            trade_result = {
                'ticker': ticker,
                'action': action,
                'quantity': filled_qty,
                'price': fill_price,
                'total_value': total_value,
                'order_id': filled_order.id,
                'date': datetime.now()
            }
            
            logger.info(f"Successfully executed {action} for {filled_qty} shares of {ticker} at ${fill_price:.2f}")
            return trade_result
            
        except Exception as e:
            logger.error(f"Error executing trade for {ticker}: {e}", exc_info=True)
            return None
            
    def backtest(self, signals, start_date, end_date, initial_capital=100000):
        """
        Backtest the strategy on historical signals.
        
        Args:
            signals (list): List of historical signals
            start_date (datetime): Start date for backtest
            end_date (datetime): End date for backtest
            initial_capital (float): Initial capital
            
        Returns:
            dict: Backtest results
        """
        logger.info(f"Running backtest from {start_date} to {end_date}")
        
        # Initialize backtest state
        capital = initial_capital
        positions = {}
        trades = []
        daily_equity = []
        
        # Filter signals within date range
        valid_signals = [s for s in signals if start_date <= s.get('date') <= end_date]
        valid_signals.sort(key=lambda x: x.get('date'))
        
        # Group signals by day
        signals_by_day = {}
        for signal in valid_signals:
            date_key = signal.get('date').strftime('%Y-%m-%d')
            if date_key not in signals_by_day:
                signals_by_day[date_key] = []
            signals_by_day[date_key].append(signal)
        
        # Run through each day
        current_date = start_date
        while current_date <= end_date:
            date_key = current_date.strftime('%Y-%m-%d')
            
            # Update positions with latest prices
            portfolio_value = capital
            for ticker, position in list(positions.items()):
                # Get historical price for this day
                # In a real implementation, you would use historical price data
                # For now, we'll use dummy prices
                current_price = self._get_historical_price(ticker, current_date)
                
                # Update position value
                if current_price:
                    position['current_price'] = current_price
                    position['current_value'] = position['quantity'] * current_price
                    portfolio_value += position['current_value']
            
            # Record daily equity
            daily_equity.append({
                'date': current_date,
                'equity': portfolio_value
            })
            
            # Process signals for this day
            day_signals = signals_by_day.get(date_key, [])
            
            for signal in day_signals:
                ticker = signal.get('ticker')
                signal_direction = signal.get('signal')
                position_multiplier = signal.get('position_multiplier', 1.0)
                
                # Calculate position size
                max_position_value = portfolio_value * (self.max_position_size_percent / 100)
                position_value = max_position_value * position_multiplier
                
                # Get price
                price = self._get_historical_price(ticker, current_date)
                if not price:
                    continue
                    
                # Calculate shares
                shares = int(position_value / price)
                
                if ticker in positions:
                    # Close existing position if opposite direction
                    current_position = positions[ticker]
                    current_direction = "BULLISH" if current_position['quantity'] > 0 else "BEARISH"
                    
                    if current_direction != signal_direction:
                        # Close position
                        trade_value = current_position['quantity'] * price
                        capital += trade_value
                        
                        trades.append({
                            'date': current_date,
                            'ticker': ticker,
                            'action': 'SELL' if current_position['quantity'] > 0 else 'BUY',
                            'quantity': abs(current_position['quantity']),
                            'price': price,
                            'value': trade_value,
                            'signal': signal
                        })
                        
                        # Remove from positions
                        del positions[ticker]
                        
                        # Open new position
                        if capital >= position_value:
                            new_quantity = shares if signal_direction == "BULLISH" else -shares
                            new_value = new_quantity * price
                            
                            positions[ticker] = {
                                'quantity': new_quantity,
                                'entry_price': price,
                                'entry_value': new_value,
                                'current_price': price,
                                'current_value': new_value,
                                'entry_date': current_date,
                                'signal': signal
                            }
                            
                            capital -= new_value
                            
                            trades.append({
                                'date': current_date,
                                'ticker': ticker,
                                'action': 'BUY' if new_quantity > 0 else 'SELL',
                                'quantity': abs(new_quantity),
                                'price': price,
                                'value': new_value,
                                'signal': signal
                            })
                else:
                    # Open new position
                    if capital >= position_value:
                        new_quantity = shares if signal_direction == "BULLISH" else -shares
                        new_value = new_quantity * price
                        
                        positions[ticker] = {
                            'quantity': new_quantity,
                            'entry_price': price,
                            'entry_value': new_value,
                            'current_price': price,
                            'current_value': new_value,
                            'entry_date': current_date,
                            'signal': signal
                        }
                        
                        capital -= new_value
                        
                        trades.append({
                            'date': current_date,
                            'ticker': ticker,
                            'action': 'BUY' if new_quantity > 0 else 'SELL',
                            'quantity': abs(new_quantity),
                            'price': price,
                            'value': new_value,
                            'signal': signal
                        })
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Calculate final portfolio value
        final_value = capital
        for ticker, position in positions.items():
            # Get final price
            final_price = self._get_historical_price(ticker, end_date)
            if final_price:
                final_value += position['quantity'] * final_price
        
        # Calculate performance metrics
        initial_value = initial_capital
        returns = (final_value - initial_value) / initial_value
        
        backtest_results = {
            'initial_capital': initial_capital,
            'final_value': final_value,
            'returns': returns,
            'trades': trades,
            'daily_equity': daily_equity
        }
        
        logger.info(f"Backtest completed with {len(trades)} trades and {returns:.2%} return")
        return backtest_results
        
    def _get_historical_price(self, ticker, date):
        """
        Get historical price for a ticker on a specific date.
        
        Args:
            ticker (str): Stock ticker symbol
            date (datetime): Date to get price for
            
        Returns:
            float: Historical price or None if not available
        """
        # In a real implementation, you would use historical price data
        # from Alpaca, Yahoo Finance, or another source
        
        # For demonstration, generate dummy prices
        import random
        
        # Use a seed based on ticker and date for consistency
        seed = hash(f"{ticker}{date.strftime('%Y%m%d')}")
        random.seed(seed)
        
        # Generate a price between 10 and 500
        price = random.uniform(10, 500)
        
        return price
