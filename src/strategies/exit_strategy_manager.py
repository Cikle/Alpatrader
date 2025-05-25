#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exit Strategy Manager for the Alpatrader system.
Handles stop loss, take profit, time-based exits, and trailing stops.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class ExitStrategyManager:
    """
    Manager class for handling various exit strategies.
    """
    
    def __init__(self, alpaca, config):
        """
        Initialize the exit strategy manager.
        
        Args:
            alpaca (AlpacaWrapper): Alpaca API wrapper
            config (ConfigParser): Configuration object
        """
        self.alpaca = alpaca
        self.config = config
        
        # Load exit strategy configuration
        self.use_stop_loss = config.getboolean('exit_strategy', 'use_stop_loss', fallback=True)
        self.stop_loss_percent = config.getfloat('exit_strategy', 'stop_loss_percent', fallback=-10.0)
        
        self.use_take_profit = config.getboolean('exit_strategy', 'use_take_profit', fallback=True)
        self.take_profit_percent = config.getfloat('exit_strategy', 'take_profit_percent', fallback=20.0)
        
        self.use_time_based_exit = config.getboolean('exit_strategy', 'use_time_based_exit', fallback=True)
        self.max_hold_days = config.getint('exit_strategy', 'max_hold_days', fallback=30)
        
        self.use_trailing_stop = config.getboolean('exit_strategy', 'use_trailing_stop', fallback=False)
        self.trailing_stop_percent = config.getfloat('exit_strategy', 'trailing_stop_percent', fallback=5.0)
        
        self.exit_during_market_hours_only = config.getboolean('exit_strategy', 'exit_during_market_hours_only', fallback=True)
        
        # Store trailing stop levels for each position
        self.trailing_stops = {}
        
        logger.info(f"Exit Strategy Manager initialized:")
        logger.info(f"  Stop Loss: {self.use_stop_loss} ({self.stop_loss_percent}%)")
        logger.info(f"  Take Profit: {self.use_take_profit} ({self.take_profit_percent}%)")
        logger.info(f"  Time-based Exit: {self.use_time_based_exit} ({self.max_hold_days} days)")
        logger.info(f"  Trailing Stop: {self.use_trailing_stop} ({self.trailing_stop_percent}%)")
    
    def check_exit_conditions(self) -> List[Dict]:
        """
        Check all positions for exit conditions and return list of positions to close.
        
        Returns:
            List[Dict]: List of positions that should be closed with exit reasons
        """
        if self.exit_during_market_hours_only and not self.alpaca.is_market_open():
            return []
        
        positions_to_close = []
        
        try:
            # Get current positions
            positions = self.alpaca.get_positions()
            
            if not positions:
                return []
            
            logger.info(f"Checking exit conditions for {len(positions)} positions")
            
            for position in positions:
                exit_reasons = self._check_position_exit_conditions(position)
                
                if exit_reasons:
                    positions_to_close.append({
                        'position': position,
                        'reasons': exit_reasons
                    })
            
            if positions_to_close:
                logger.info(f"Found {len(positions_to_close)} positions to close")
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}", exc_info=True)
        
        return positions_to_close
    
    def _check_position_exit_conditions(self, position) -> List[str]:
        """
        Check exit conditions for a single position.
        
        Args:
            position: Position object from Alpaca
            
        Returns:
            List[str]: List of exit reasons (empty if no exit needed)
        """
        exit_reasons = []
        
        try:
            symbol = position.symbol
            qty = float(position.qty)
            cost_basis = float(position.cost_basis)
            current_price = float(position.current_price)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc) * 100  # Convert to percentage
            
            # Calculate entry price
            entry_price = cost_basis / abs(qty) if qty != 0 else 0
            
            # Check stop loss
            if self.use_stop_loss and unrealized_plpc <= self.stop_loss_percent:
                exit_reasons.append(f"Stop Loss ({unrealized_plpc:.2f}% <= {self.stop_loss_percent}%)")
            
            # Check take profit
            if self.use_take_profit and unrealized_plpc >= self.take_profit_percent:
                exit_reasons.append(f"Take Profit ({unrealized_plpc:.2f}% >= {self.take_profit_percent}%)")
            
            # Check time-based exit
            if self.use_time_based_exit and self.max_hold_days > 0:
                # Try to get position creation time from orders
                # This is a simplified approach - in reality you'd want to track this in a database
                days_held = self._estimate_position_age(symbol)
                if days_held >= self.max_hold_days:
                    exit_reasons.append(f"Time-based Exit ({days_held} days >= {self.max_hold_days} days)")
            
            # Check trailing stop
            if self.use_trailing_stop:
                trailing_exit = self._check_trailing_stop(symbol, current_price, unrealized_plpc, qty > 0)
                if trailing_exit:
                    exit_reasons.append(trailing_exit)
            
        except Exception as e:
            logger.error(f"Error checking exit conditions for {position.symbol}: {e}", exc_info=True)
        
        return exit_reasons
    
    def _estimate_position_age(self, symbol: str) -> int:
        """
        Estimate how long we've held a position by looking at recent orders.
        This is a simplified approach - ideally you'd track positions in a database.
        
        Args:
            symbol (str): Stock symbol
            
        Returns:
            int: Estimated days held
        """
        try:
            # Get recent orders for this symbol
            orders = self.alpaca.get_orders(
                status='filled',
                symbols=[symbol],
                limit=10
            )
            
            if orders:
                # Find the most recent buy order (opening the position)
                buy_orders = [o for o in orders if o.side == 'buy']
                if buy_orders:
                    # Sort by creation time and get the most recent
                    buy_orders.sort(key=lambda x: x.created_at, reverse=True)
                    latest_buy = buy_orders[0]
                    
                    # Calculate days since the order
                    order_date = latest_buy.created_at.replace(tzinfo=None)
                    days_held = (datetime.now() - order_date).days
                    return max(0, days_held)
            
        except Exception as e:
            logger.error(f"Error estimating position age for {symbol}: {e}")
        
        # Default to 0 if we can't determine age
        return 0
    
    def _check_trailing_stop(self, symbol: str, current_price: float, current_pl_percent: float, is_long: bool) -> Optional[str]:
        """
        Check trailing stop condition for a position.
        
        Args:
            symbol (str): Stock symbol
            current_price (float): Current stock price
            current_pl_percent (float): Current P&L percentage
            is_long (bool): True if long position, False if short
            
        Returns:
            Optional[str]: Exit reason if trailing stop triggered, None otherwise
        """
        try:
            # Initialize trailing stop if not exists
            if symbol not in self.trailing_stops:
                self.trailing_stops[symbol] = {
                    'highest_price': current_price if is_long else None,
                    'lowest_price': current_price if not is_long else None,
                    'best_pl_percent': current_pl_percent
                }
                return None
            
            trailing_data = self.trailing_stops[symbol]
            
            if is_long:
                # For long positions, track highest price and best P&L
                if current_price > trailing_data.get('highest_price', 0):
                    trailing_data['highest_price'] = current_price
                
                if current_pl_percent > trailing_data.get('best_pl_percent', float('-inf')):
                    trailing_data['best_pl_percent'] = current_pl_percent
                
                # Check if price dropped by trailing stop percentage from best
                if trailing_data['best_pl_percent'] > 0:  # Only apply if we're in profit
                    decline_from_best = trailing_data['best_pl_percent'] - current_pl_percent
                    if decline_from_best >= self.trailing_stop_percent:
                        return f"Trailing Stop (declined {decline_from_best:.2f}% from best {trailing_data['best_pl_percent']:.2f}%)"
            
            else:
                # For short positions, track lowest price and best P&L
                if current_price < trailing_data.get('lowest_price', float('inf')):
                    trailing_data['lowest_price'] = current_price
                
                if current_pl_percent > trailing_data.get('best_pl_percent', float('-inf')):
                    trailing_data['best_pl_percent'] = current_pl_percent
                
                # Check if price rose by trailing stop percentage from best
                if trailing_data['best_pl_percent'] > 0:  # Only apply if we're in profit
                    decline_from_best = trailing_data['best_pl_percent'] - current_pl_percent
                    if decline_from_best >= self.trailing_stop_percent:
                        return f"Trailing Stop (declined {decline_from_best:.2f}% from best {trailing_data['best_pl_percent']:.2f}%)"
            
        except Exception as e:
            logger.error(f"Error checking trailing stop for {symbol}: {e}")
        
        return None
    
    def execute_exits(self, positions_to_close: List[Dict]) -> List[Dict]:
        """
        Execute exit trades for positions that meet exit conditions.
        
        Args:
            positions_to_close (List[Dict]): List of positions to close with reasons
            
        Returns:
            List[Dict]: List of executed exit trades
        """
        executed_exits = []
        
        for position_data in positions_to_close:
            position = position_data['position']
            reasons = position_data['reasons']
            
            try:
                symbol = position.symbol
                qty = float(position.qty)
                
                # Determine action (opposite of current position)
                action = "SELL" if qty > 0 else "BUY"
                quantity = abs(qty)
                
                logger.info(f"Executing exit for {symbol}: {action} {quantity} shares")
                logger.info(f"  Exit reasons: {', '.join(reasons)}")
                
                # Execute the exit trade
                exit_result = self._execute_exit_trade(symbol, action, quantity, reasons)
                
                if exit_result:
                    executed_exits.append(exit_result)
                    
                    # Clean up trailing stop data
                    if symbol in self.trailing_stops:
                        del self.trailing_stops[symbol]
                
            except Exception as e:
                logger.error(f"Error executing exit for {position.symbol}: {e}", exc_info=True)
        
        return executed_exits
    
    def _execute_exit_trade(self, symbol: str, action: str, quantity: int, reasons: List[str]) -> Optional[Dict]:
        """
        Execute a single exit trade.
        
        Args:
            symbol (str): Stock symbol
            action (str): 'BUY' or 'SELL'
            quantity (int): Number of shares
            reasons (List[str]): Exit reasons
            
        Returns:
            Optional[Dict]: Trade execution details or None if failed
        """
        try:
            logger.info(f"Executing {action} order for {quantity} shares of {symbol} (Exit: {', '.join(reasons)})")
            
            # Submit exit order to Alpaca
            order = self.alpaca.submit_order(
                symbol=symbol,
                qty=quantity,
                side=action.lower(),
                type='market',
                time_in_force='day'
            )
            
            if not order:
                logger.error(f"Failed to submit exit order for {symbol}")
                return None
            
            # Wait for fill
            filled_order = self.alpaca.wait_for_order(order.id)
            
            if not filled_order or filled_order.status != 'filled':
                logger.error(f"Exit order for {symbol} was not filled")
                return None
            
            fill_price = float(filled_order.filled_avg_price)
            filled_qty = int(filled_order.filled_qty)
            total_value = fill_price * filled_qty
            
            exit_result = {
                'symbol': symbol,
                'action': action,
                'quantity': filled_qty,
                'price': fill_price,
                'total_value': total_value,
                'order_id': filled_order.id,
                'exit_reasons': reasons,
                'exit_time': datetime.now(),
                'trade_type': 'EXIT'
            }
            
            logger.info(f"Successfully executed exit: {action} {filled_qty} shares of {symbol} at ${fill_price:.2f}")
            logger.info(f"Exit reasons: {', '.join(reasons)}")
            
            return exit_result
            
        except Exception as e:
            logger.error(f"Error executing exit trade for {symbol}: {e}", exc_info=True)
            return None
    
    def reset_trailing_stops(self):
        """Reset all trailing stop data."""
        self.trailing_stops.clear()
        logger.info("Trailing stops reset")
    
    def get_trailing_stop_status(self) -> Dict:
        """Get current trailing stop status for all tracked positions."""
        return self.trailing_stops.copy()
