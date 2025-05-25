#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to demonstrate exit strategy functionality.
"""

import os
import sys
import configparser
import logging

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.strategies.exit_strategy_manager import ExitStrategyManager
from src.utils.alpaca_wrapper import AlpacaWrapper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('config', 'config.ini'))
    return config

def test_exit_strategies():
    """Test the exit strategy functionality."""
    logger.info("Testing Exit Strategy Manager")
    
    # Load configuration
    config = load_config()
    
    # Initialize Alpaca wrapper
    alpaca = AlpacaWrapper(
        api_key=config['alpaca']['api_key'],
        api_secret=config['alpaca']['api_secret'],
        base_url=config['alpaca']['base_url'],
        data_url=config['alpaca']['data_url']
    )
    
    # Initialize exit strategy manager
    exit_manager = ExitStrategyManager(
        alpaca=alpaca,
        config=config
    )
    
    logger.info("Exit Strategy Manager Configuration:")
    logger.info(f"  Stop Loss: {exit_manager.use_stop_loss} ({exit_manager.stop_loss_percent}%)")
    logger.info(f"  Take Profit: {exit_manager.use_take_profit} ({exit_manager.take_profit_percent}%)")
    logger.info(f"  Time-based Exit: {exit_manager.use_time_based_exit} ({exit_manager.max_hold_days} days)")
    logger.info(f"  Trailing Stop: {exit_manager.use_trailing_stop} ({exit_manager.trailing_stop_percent}%)")
    logger.info(f"  Market Hours Only: {exit_manager.exit_during_market_hours_only}")
    
    # Get current positions
    positions = alpaca.get_positions()
    
    if positions:
        logger.info(f"\nAnalyzing {len(positions)} current positions for exit conditions:")
        
        for position in positions:
            symbol = position.symbol
            qty = float(position.qty)
            cost_basis = float(position.cost_basis)
            current_price = float(position.current_price)
            unrealized_pl = float(position.unrealized_pl)
            unrealized_plpc = float(position.unrealized_plpc) * 100
            
            entry_price = cost_basis / abs(qty) if qty != 0 else 0
            side = 'Long' if qty > 0 else 'Short'
            
            logger.info(f"\n  {symbol} ({side} {abs(qty)} shares):")
            logger.info(f"    Entry Price: ${entry_price:.2f}")
            logger.info(f"    Current Price: ${current_price:.2f}")
            logger.info(f"    Unrealized P&L: ${unrealized_pl:.2f} ({unrealized_plpc:.2f}%)")
            
            # Check exit conditions for this position
            exit_reasons = exit_manager._check_position_exit_conditions(position)
            
            if exit_reasons:
                logger.info(f"    ⚠️  EXIT TRIGGERED: {', '.join(exit_reasons)}")
            else:
                logger.info(f"    ✅ No exit conditions met")
                
                # Show what would trigger exits
                remaining_loss = exit_manager.stop_loss_percent - unrealized_plpc
                remaining_gain = exit_manager.take_profit_percent - unrealized_plpc
                
                if exit_manager.use_stop_loss:
                    logger.info(f"    Stop Loss would trigger at {remaining_loss:.2f}% more loss")
                if exit_manager.use_take_profit:
                    logger.info(f"    Take Profit would trigger at {remaining_gain:.2f}% more gain")
        
        # Check all exit conditions
        logger.info("\n" + "="*50)
        logger.info("CHECKING ALL EXIT CONDITIONS")
        logger.info("="*50)
        
        positions_to_close = exit_manager.check_exit_conditions()
        
        if positions_to_close:
            logger.info(f"Found {len(positions_to_close)} positions that should be closed:")
            
            for position_data in positions_to_close:
                position = position_data['position']
                reasons = position_data['reasons']
                logger.info(f"  {position.symbol}: {', '.join(reasons)}")
                
            logger.info("\nNote: These positions would be automatically closed during market hours.")
        else:
            logger.info("No positions currently meet exit criteria.")
            
    else:
        logger.info("No current positions to analyze.")
    
    # Display trailing stop status
    trailing_status = exit_manager.get_trailing_stop_status()
    if trailing_status:
        logger.info(f"\nTrailing Stop Status:")
        for symbol, data in trailing_status.items():
            logger.info(f"  {symbol}: {data}")
    else:
        logger.info("\nNo trailing stops currently active.")

if __name__ == "__main__":
    test_exit_strategies()
