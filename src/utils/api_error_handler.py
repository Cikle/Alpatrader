#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
API error handling utilities for Alpatrader.
This file contains helpers to manage API errors and fallbacks.
"""

import logging
import json
import requests
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)

class APIErrorHandler:
    """
    Class for handling API errors and providing fallbacks.
    """
    
    @staticmethod
    def handle_finnhub_error(ticker, finnhub_key):
        """
        Provides error handling and fallbacks for Finnhub API errors.
        
        Args:
            ticker (str): Stock ticker
            finnhub_key (str): Finnhub API key
            
        Returns:
            dict: Sentiment data for the ticker
        """
        logger.warning(f"Using fallback sentiment data for {ticker}")
        
        # Generate sample sentiment data
        sentiment_score = random.uniform(-0.5, 0.5)
        
        # Convert to signal
        if sentiment_score > 0.2:
            signal = 'BULLISH'
            confidence = min(0.7, sentiment_score + 0.3)  # Lower max confidence for sample data
        elif sentiment_score < -0.2:
            signal = 'BEARISH'
            confidence = min(0.7, abs(sentiment_score) + 0.3)
        else:
            signal = 'NEUTRAL'
            confidence = 0.5
            
        return {
            'sentiment_score': sentiment_score,
            'signal': signal,
            'confidence': confidence,
            'source_detail': 'Finnhub (Sample Data)'
        }
        
    @staticmethod
    def handle_congress_api_error(max_transaction_size=1000000, delay_hours=24):
        """
        Provides error handling and fallbacks for Congress API errors.
        
        Args:
            max_transaction_size (float): Maximum transaction size to consider
            delay_hours (int): Hours to delay after filing before considering the trade
            
        Returns:
            list: Sample Congress trade data
        """
        logger.warning("Using sample Congress trade data")
        
        # Sample politicians
        politicians = [
            "Sen. John Smith",
            "Sen. Maria Johnson",
            "Sen. Robert Davis",
            "Sen. Elizabeth Brown",
            "Sen. Michael Wilson"
        ]
        
        # Sample companies and tickers
        companies = [
            {"company": "Tech Innovations Inc.", "ticker": "TECH"},
            {"company": "Global Healthcare Corp", "ticker": "HLTH"},
            {"company": "American Energy Solutions", "ticker": "NRGY"},
            {"company": "Financial Services Group", "ticker": "FINC"},
            {"company": "Consumer Products Ltd", "ticker": "CSMR"}
        ]
        
        # Sample transaction types
        buy_transactions = ["Purchase", "Partial Purchase", "Buy"]
        sell_transactions = ["Sale", "Partial Sale", "Sell"]
          # Generate sample data
        sample_trades = []
        today = datetime.now()
        
        for i in range(random.randint(10, 15)):
            # Random date within the last month but not too recent
            days_ago = random.randint(int(delay_hours // 24) + 1, 30)
            trade_date = today - timedelta(days=days_ago)
            
            # Random company
            company_data = random.choice(companies)
            
            # Random buy/sell with 60% buys
            is_buy = random.random() < 0.6
            transaction_type = random.choice(buy_transactions if is_buy else sell_transactions)
            
            # Random value between $1,000 and $max_transaction_size
            value = random.randint(1000, int(max_transaction_size * 0.8))
            
            # Signal based on transaction type
            signal = 'BULLISH' if is_buy else 'BEARISH'
            confidence = min(0.8, value / max_transaction_size)
            
            trade = {
                'date': trade_date,
                'politician': random.choice(politicians),
                'ticker': company_data['ticker'],
                'company': company_data['company'],
                'transaction_type': transaction_type,
                'estimated_value': value,
                'asset_type': "Stock",
                'signal': signal,
                'confidence': confidence,
                'source': 'congress',
                'source_detail': 'Senate Stock Watcher (Sample Data)',
                'is_sample_data': True
            }
            
            sample_trades.append(trade)
            
        logger.info(f"Generated {len(sample_trades)} sample Congress trades")
        return sample_trades
