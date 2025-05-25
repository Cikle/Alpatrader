#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Quick script to check current positions in Alpaca account.
"""

import os
import sys
import configparser

# Add src to the path so we can import modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.alpaca_wrapper import AlpacaWrapper

def load_config():
    """Loads configuration from config file."""
    config = configparser.ConfigParser()
    config.read(os.path.join('config', 'config.ini'))
    return config

def main():
    """Check current positions."""
    print("Checking current Alpaca positions...")
    
    try:
        # Load configuration
        config = load_config()
        print("Configuration loaded successfully")
        
        # Initialize Alpaca wrapper
        alpaca = AlpacaWrapper(
            api_key=config['alpaca']['api_key'],
            api_secret=config['alpaca']['api_secret'],
            base_url=config['alpaca']['base_url'],
            data_url=config['alpaca']['data_url']
        )
        
        if not alpaca.api:
            print("Failed to connect to Alpaca API")
            return
        
        print("Connected to Alpaca API successfully")
        
        # Get account info
        account = alpaca.get_account()
        if account:
            print(f"\nAccount ID: {account.id}")
            print(f"Account Status: {account.status}")
            print(f"Buying Power: ${float(account.buying_power):,.2f}")
            print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")            
            print(f"Cash: ${float(account.cash):,.2f}")
        else:
            print("Failed to get account information")
        
        # Get current positions
        print("\nGetting current positions...")
        positions = alpaca.get_positions()
        print(f"API returned {len(positions) if positions else 0} positions")
        
        if positions:
            print(f"\nFound {len(positions)} open positions:")
            print("-" * 60)
            for i, position in enumerate(positions, 1):
                qty = float(position.qty)
                cost_basis = float(position.cost_basis)
                entry_price = cost_basis / abs(qty) if qty != 0 else 0
                
                print(f"\nPosition {i}:")
                print(f"  Symbol: {position.symbol}")
                print(f"  Quantity: {position.qty}")
                print(f"  Side: {'Long' if qty > 0 else 'Short'}")
                print(f"  Entry Price: ${entry_price:.2f}")
                print(f"  Current Price: ${float(position.current_price):,.2f}")
                print(f"  Market Value: ${float(position.market_value):,.2f}")
                print(f"  Cost Basis: ${cost_basis:,.2f}")
                print(f"  Unrealized P&L: ${float(position.unrealized_pl):,.2f}")
                print(f"  Unrealized P&L %: {float(position.unrealized_plpc)*100:.2f}%")
                
            print("-" * 60)
            
            # Test the short selling handling for each position
            print("\nTesting short selling handling for current positions:")
            for position in positions:
                symbol = position.symbol
                current_qty = float(position.qty)
                
                print(f"\n{symbol} (Current: {current_qty} shares):")
                
                # Test selling exact amount
                side, qty = alpaca._handle_short_selling(symbol, current_qty, 'sell')
                print(f"  Sell {current_qty}: {side} {qty} shares")
                
                # Test selling more than we have
                side, qty = alpaca._handle_short_selling(symbol, current_qty + 10, 'sell')
                print(f"  Sell {current_qty + 10}: {side} {qty} shares")
                
            # Test selling when we have no position (simulate)
            print(f"\nTesting short selling for non-held stock:")
            side, qty = alpaca._handle_short_selling("FAKE", 100, 'sell')
            print(f"  Sell FAKE (no position): {side} {qty} shares")
        else:
            print("\nNo open positions found.")
            
            # Test short selling handling with no positions
            print("\nTesting short selling handling with no positions:")
            side, qty = alpaca._handle_short_selling("AAPL", 100, 'sell')
            print(f"  Sell AAPL (no position): {side} {qty} shares")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
