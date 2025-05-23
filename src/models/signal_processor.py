#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for processing signals from various sources and combining them.
"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SignalProcessor:
    """
    Class for processing and combining signals from insider, congress, and news sources.
    Implements the signal hierarchy as specified.
    """
    
    def __init__(self, config, insider_scraper, congress_scraper, news_analyzer):
        """
        Initialize the signal processor.
        
        Args:
            config (ConfigParser): Configuration object
            insider_scraper (OpenInsiderScraper): Insider trades scraper
            congress_scraper (SenateScraper): Congress trades scraper
            news_analyzer (NewsSentimentAnalyzer): News sentiment analyzer
        """
        self.config = config
        self.insider_scraper = insider_scraper
        self.congress_scraper = congress_scraper
        self.news_analyzer = news_analyzer
        
        # Read trading parameters from config
        self.strong_news_multiplier = config.getfloat('trading', 'strong_news_multiplier', fallback=2.0)
        self.congress_only_multiplier = config.getfloat('trading', 'congress_only_multiplier', fallback=1.0)
        self.insider_only_multiplier = config.getfloat('trading', 'insider_only_multiplier', fallback=0.5)
        
        # Thresholds for strong signals
        self.strong_news_threshold = 0.7
        
        # Whether to skip trades during FOMC blackout periods
        self.skip_fomc_blackout = config.getboolean('filters', 'skip_fomc_blackout', fallback=True)
        
    def process_signals(self):
        """
        Process signals from all sources and combine them according to the signal hierarchy.
        
        Returns:
            list: List of combined signals with trading instructions
        """
        logger.info("Processing signals from all sources")
        
        # Check if we're in an FOMC blackout period
        if self.skip_fomc_blackout and self._is_fomc_blackout():
            logger.info("Skipping signal processing due to FOMC blackout period")
            return []
        
        # Get data from all sources
        insider_trades = self.insider_scraper.fetch_latest_data()
        congress_trades = self.congress_scraper.fetch_latest_data()
        
        # Get list of all unique tickers
        tickers = set([t['ticker'] for t in insider_trades + congress_trades])
        
        # Get news for these tickers
        news_by_ticker = self.news_analyzer.fetch_latest_news(list(tickers))
        
        # Get strong news signals
        strong_news = self.news_analyzer.get_strong_news_signals(self.strong_news_threshold)
        
        # Add tickers from strong news if not already included
        news_tickers = set([n['ticker'] for n in strong_news if n['ticker'] != 'MARKET'])
        tickers.update(news_tickers)
        
        # Process each ticker
        combined_signals = []
        
        for ticker in tickers:
            # Get signals for this ticker
            ticker_insider = [t for t in insider_trades if t['ticker'] == ticker]
            ticker_congress = [t for t in congress_trades if t['ticker'] == ticker]
            ticker_news = news_by_ticker.get(ticker, [])
            ticker_strong_news = [n for n in strong_news if n['ticker'] == ticker]
            
            # Skip if no signals
            if not (ticker_insider or ticker_congress or ticker_strong_news):
                continue
            
            # Determine best signal based on hierarchy
            best_signal = self._determine_best_signal(
                ticker, ticker_insider, ticker_congress, ticker_news, ticker_strong_news
            )
            
            if best_signal:
                combined_signals.append(best_signal)
                
        logger.info(f"Generated {len(combined_signals)} combined signals")
        return combined_signals
        
    def _determine_best_signal(self, ticker, insider_trades, congress_trades, news, strong_news):
        """
        Determine the best signal based on the signal hierarchy.
        
        Args:
            ticker (str): Stock ticker symbol
            insider_trades (list): List of insider trades
            congress_trades (list): List of congress trades
            news (list): List of news items
            strong_news (list): List of strong news signals
            
        Returns:
            dict: Best signal with trading instructions or None
        """
        # Start with empty signal
        best_signal = None
        confidence = 0
        source_count = 0
        position_multiplier = 0
        sources = []
        
        # Check for strong news + insider/congress (highest priority)
        if strong_news and (insider_trades or congress_trades):
            # Use the best strong news signal
            strong_news.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            news_signal = strong_news[0]
            
            # Find matching signal from insider or congress
            other_signals = insider_trades + congress_trades
            other_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            
            # Find a signal that matches the news signal direction
            matching_signal = None
            for signal in other_signals:
                if signal.get('signal') == news_signal.get('signal'):
                    matching_signal = signal
                    break
            
            if matching_signal:
                # Strong news + matching insider/congress signal
                signal_direction = news_signal.get('signal')
                confidence = (news_signal.get('confidence', 0) + matching_signal.get('confidence', 0)) / 2
                source_count = 2
                position_multiplier = self.strong_news_multiplier
                sources = [news_signal, matching_signal]
                
                # Create combined signal
                best_signal = {
                    'ticker': ticker,
                    'signal': signal_direction,
                    'confidence': confidence,
                    'position_multiplier': position_multiplier,
                    'sources': sources,
                    'source_count': source_count,
                    'date': datetime.now(),
                    'description': f"Strong news signal + {'Insider' if matching_signal.get('source') == 'insider' else 'Congress'} trade"
                }
        
        # Check for congress only (medium priority)
        if not best_signal and congress_trades:
            # Get the most confident congress signal
            congress_trades.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            congress_signal = congress_trades[0]
            
            signal_direction = congress_signal.get('signal')
            confidence = congress_signal.get('confidence', 0)
            source_count = 1
            position_multiplier = self.congress_only_multiplier
            sources = [congress_signal]
            
            best_signal = {
                'ticker': ticker,
                'signal': signal_direction,
                'confidence': confidence,
                'position_multiplier': position_multiplier,
                'sources': sources,
                'source_count': source_count,
                'date': datetime.now(),
                'description': f"Congress trade by {congress_signal.get('politician', 'Unknown')}"
            }
        
        # Check for insider only (lowest priority)
        if not best_signal and insider_trades:
            # Get the most confident insider signal
            insider_trades.sort(key=lambda x: x.get('confidence', 0), reverse=True)
            insider_signal = insider_trades[0]
            
            signal_direction = insider_signal.get('signal')
            confidence = insider_signal.get('confidence', 0)
            source_count = 1
            position_multiplier = self.insider_only_multiplier
            sources = [insider_signal]
            
            best_signal = {
                'ticker': ticker,
                'signal': signal_direction,
                'confidence': confidence,
                'position_multiplier': position_multiplier,
                'sources': sources,
                'source_count': source_count,
                'date': datetime.now(),
                'description': f"Insider trade by {insider_signal.get('insider', 'Unknown')} ({insider_signal.get('title', 'Unknown')})"
            }
        
        return best_signal
    
    def _is_fomc_blackout_period(self):
        """
        Check if current date is within an FOMC blackout period.
        
        Returns:
            bool: True if in blackout period, False otherwise
        """
        # This is a placeholder. In a real implementation, you would:
        # 1. Maintain a calendar of FOMC meeting dates
        # 2. Check if current date is within blackout window (typically 10 days before meeting)
        
        # For demonstration, always return False
        return False
        
    def _is_fomc_blackout(self):
        """
        Check if current date is within an FOMC blackout period.
        Uses Federal Reserve calendar data.
        
        Returns:
            bool: True if in blackout period, False otherwise
        """
        # FOMC meetings in 2023-2024 (approximate dates)
        # Real implementation would fetch these from Fed website or financial calendar API
        fomc_dates = [
            datetime(2023, 1, 31),
            datetime(2023, 3, 21),
            datetime(2023, 5, 2),
            datetime(2023, 6, 13),
            datetime(2023, 7, 25),
            datetime(2023, 9, 19),
            datetime(2023, 10, 31),
            datetime(2023, 12, 12),
            datetime(2024, 1, 30),
            datetime(2024, 3, 19),
            datetime(2024, 4, 30),
            datetime(2024, 6, 11),
            datetime(2024, 7, 30),
            datetime(2024, 9, 17),
            datetime(2024, 11, 6),
            datetime(2024, 12, 17),
            datetime(2025, 1, 28),
            datetime(2025, 3, 18),
            datetime(2025, 4, 29),
        ]
        
        # Blackout period is typically 10 days before meeting
        blackout_period = 10
        
        # Check if current date is in any blackout period
        now = datetime.now()
        
        for meeting_date in fomc_dates:
            blackout_start = meeting_date - timedelta(days=blackout_period)
            
            if blackout_start <= now <= meeting_date:
                logger.info(f"In FOMC blackout period for meeting on {meeting_date.strftime('%Y-%m-%d')}")
                return True
                
        return False
