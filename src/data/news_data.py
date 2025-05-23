#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module for retrieving and analyzing news sentiment.
"""

import logging
import requests
from datetime import datetime, timedelta
import re
from collections import defaultdict
import time
import json
import html
import random  # For fallback
import numpy as np

logger = logging.getLogger(__name__)

class NewsSentimentAnalyzer:
    """
    Class for retrieving news headlines and analyzing sentiment.
    Uses NewsAPI/GNews for headlines and Finnhub for sentiment scoring.
    """
    
    def __init__(self, newsapi_key=None, gnews_key=None, finnhub_key=None, db_manager=None):
        """
        Initialize the news sentiment analyzer.
        
        Args:
            newsapi_key (str): API key for NewsAPI
            gnews_key (str): API key for GNews
            finnhub_key (str): API key for Finnhub
            db_manager (DatabaseManager): Database manager for caching results
        """
        self.newsapi_key = newsapi_key
        self.gnews_key = gnews_key
        self.finnhub_key = finnhub_key
        self.db_manager = db_manager
        
        # API endpoints
        self.newsapi_url = "https://newsapi.org/v2/everything"
        self.gnews_url = "https://gnews.io/api/v4/search"
        self.finnhub_url = "https://finnhub.io/api/v1/news-sentiment"
        
        # Cache for sentiment scores (to reduce API calls)
        self.sentiment_cache = {}
        
        # Word lists for basic sentiment analysis when API is unavailable
        self.bullish_words = [
            'bullish', 'buy', 'positive', 'growth', 'surge', 'gain', 'boost', 'soar', 
            'rally', 'beat', 'exceed', 'upgrade', 'outperform', 'strong', 'higher', 
            'record', 'rise', 'growing', 'opportunity', 'optimistic'
        ]
        
        self.bearish_words = [
            'bearish', 'sell', 'negative', 'decline', 'drop', 'fall', 'plunge', 'slump', 
            'crash', 'miss', 'downgrade', 'underperform', 'weak', 'lower', 'warning', 
            'risk', 'concern', 'trouble', 'worrying', 'pessimistic'
        ]
        
    def fetch_latest_news(self, tickers=None, days_back=2):
        """
        Fetch the latest news for the given tickers.
        
        Args:
            tickers (list): List of stock ticker symbols
            days_back (int): Number of days to look back
            
        Returns:
            dict: Dictionary of news by ticker with sentiment scores
        """
        if not tickers:
            logger.info("No tickers provided, fetching market news")
            tickers = ['MARKET']
            
        logger.info(f"Fetching news for {len(tickers)} tickers")
        
        # Check if we have cached data in the database
        if self.db_manager:
            cached_news = self._get_cached_news(tickers, days_back)
            if cached_news:
                logger.info(f"Using cached news for {len(cached_news)} tickers")
                return cached_news
        
        # Initialize results dictionary
        news_by_ticker = defaultdict(list)
        
        # Get news for each ticker
        for ticker in tickers:
            try:
                # Fetch news from preferred source
                if self.newsapi_key:
                    news_items = self._fetch_from_newsapi(ticker, days_back)
                elif self.gnews_key:
                    news_items = self._fetch_from_gnews(ticker, days_back)
                else:
                    logger.warning("No news API keys provided, skipping news fetch")
                    news_items = []
                
                if not news_items:
                    logger.info(f"No news found for {ticker}")
                    continue
                
                # Process each news item
                processed_news = []
                
                for item in news_items:
                    # Extract basic info
                    news_data = {
                        'ticker': ticker,
                        'title': item.get('title', ''),
                        'url': item.get('url', ''),
                        'source': item.get('source', {}).get('name', 'Unknown'),
                        'summary': item.get('description', '')[:200] if item.get('description') else '',
                    }
                    
                    # Parse date
                    published_at = item.get('publishedAt') or item.get('published_date')
                    if published_at:
                        try:
                            news_data['date'] = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            news_data['date'] = datetime.now()
                    else:
                        news_data['date'] = datetime.now()
                    
                    # Get sentiment for this news item
                    sentiment = self._analyze_sentiment(news_data)
                    news_data.update(sentiment)
                    
                    # Add to processed news
                    processed_news.append(news_data)
                
                # Sort by confidence
                processed_news.sort(key=lambda x: x.get('confidence', 0), reverse=True)
                
                # Add to ticker's news
                news_by_ticker[ticker] = processed_news
                
                logger.info(f"Found {len(processed_news)} news items for {ticker}")
                
                # Throttle API requests
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error fetching news for {ticker}: {e}", exc_info=True)
        
        # Cache news in database
        if self.db_manager:
            self._cache_news(news_by_ticker)
            
        return dict(news_by_ticker)
    
    def get_strong_news_signals(self, threshold=0.7):
        """
        Get strong news signals with confidence above the threshold.
        
        Args:
            threshold (float): Confidence threshold
            
        Returns:
            list: List of strong news signals
        """
        strong_signals = []
        
        # If we have a database, query it for strong signals
        if self.db_manager:
            try:
                query = f"""
                SELECT * FROM news
                WHERE confidence >= {threshold}
                AND date >= datetime('now', '-3 day')
                ORDER BY confidence DESC
                LIMIT 50
                """
                
                signals = self.db_manager.execute_query(query)
                if signals:
                    return signals
            except Exception as e:
                logger.error(f"Error getting strong news signals from database: {e}", exc_info=True)
        
        # Otherwise, fetch fresh news for major indices
        market_tickers = ['SPY', 'QQQ', 'DIA', 'IWM']
        news_by_ticker = self.fetch_latest_news(market_tickers, days_back=2)
        
        # Extract strong signals
        for ticker, news_items in news_by_ticker.items():
            for item in news_items:
                if item.get('confidence', 0) >= threshold:
                    strong_signals.append(item)
        
        # Sort by confidence
        strong_signals.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return strong_signals
    
    def _fetch_from_newsapi(self, ticker, days_back):
        """
        Fetch news from NewsAPI.
        
        Args:
            ticker (str): Stock ticker symbol
            days_back (int): Number of days to look back
            
        Returns:
            list: List of news items
        """
        if not self.newsapi_key:
            return []
            
        try:
            # Set up parameters
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Different query for market news vs stock specific news
            if ticker == 'MARKET':
                query = '(stock market OR S&P 500 OR nasdaq OR dow jones OR economy)'
            else:
                # For specific stocks, search for ticker and company name
                query = f'${ticker} stock'
            
            # Make API request
            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(self.newsapi_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') != 'ok':
                logger.error(f"NewsAPI error: {data.get('message')}")
                return []
                
            return data.get('articles', [])
            
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}", exc_info=True)
            return []
    
    def _fetch_from_gnews(self, ticker, days_back):
        """
        Fetch news from GNews.
        
        Args:
            ticker (str): Stock ticker symbol
            days_back (int): Number of days to look back
            
        Returns:
            list: List of news items
        """
        if not self.gnews_key:
            return []
            
        try:
            # Set up parameters
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            # Different query for market news vs stock specific news
            if ticker == 'MARKET':
                query = '(stock market OR S&P 500 OR nasdaq OR dow jones OR economy)'
            else:
                # For specific stocks, search for ticker and company name
                query = f'${ticker} stock'
            
            # Make API request
            params = {
                'q': query,
                'from': from_date,
                'sortby': 'publishedAt',
                'lang': 'en',
                'apikey': self.gnews_key
            }
            
            response = requests.get(self.gnews_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # GNews returns articles in a different format than NewsAPI
            # Convert to NewsAPI format for consistency
            articles = []
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'publishedAt': article.get('publishedAt'),
                    'source': {'name': article.get('source', {}).get('name')}
                })
                
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching from GNews: {e}", exc_info=True)
            return []
    
    def _analyze_sentiment(self, news_item):
        """
        Analyze sentiment of a news item.
        
        Args:
            news_item (dict): News item
            
        Returns:
            dict: Sentiment analysis results
        """
        # Check if we can use Finnhub API
        if self.finnhub_key and news_item.get('ticker') != 'MARKET':
            try:
                return self._analyze_with_finnhub(news_item)
            except Exception as e:
                logger.error(f"Error analyzing with Finnhub: {e}")
          # Fall back to basic sentiment analysis
        return self._analyze_basic_sentiment(news_item)
        
    def _analyze_with_finnhub(self, news_item):
        """
        Analyze sentiment using Finnhub API.
        
        Args:
            news_item (dict): News item
            
        Returns:
            dict: Sentiment analysis results
        """
        ticker = news_item.get('ticker')
        
        # Check cache first
        cache_key = f"{ticker}_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key in self.sentiment_cache:
            return self.sentiment_cache[cache_key]
        
        # Check if we have a valid API key
        if not self.finnhub_key or self.finnhub_key == "YOUR_FINNHUB_KEY":
            logger.warning("No valid Finnhub API key provided. Using basic sentiment analysis.")
            return self._analyze_basic_sentiment(news_item)
        
        # Make API request
        params = {
            'symbol': ticker,
            'token': self.finnhub_key
        }
        
        try:
            response = requests.get(self.finnhub_url, params=params, timeout=10)
            # Handle various error codes
            if response.status_code == 403:
                logger.warning("Finnhub API returned 403 Forbidden. API key may be invalid or rate limit exceeded.")
                return self._analyze_basic_sentiment(news_item)
            elif response.status_code == 429:
                logger.warning("Finnhub API rate limit exceeded. Using basic sentiment analysis.")
                return self._analyze_basic_sentiment(news_item)
            elif response.status_code != 200:
                logger.warning(f"Finnhub API returned status code {response.status_code}. Using basic sentiment analysis instead.")
                return self._analyze_basic_sentiment(news_item)
            
            data = response.json()
            
            # Check if response contains actual data
            if not data or not data.get('sentiment'):
                logger.warning(f"Finnhub returned empty response for {ticker}. Using basic sentiment analysis.")
                return self._analyze_basic_sentiment(news_item)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"Finnhub API request failed: {e}. Using basic sentiment analysis instead.")
            return self._analyze_basic_sentiment(news_item)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Finnhub response for {ticker}. Using basic sentiment analysis.")
            return self._analyze_basic_sentiment(news_item)
        
        # Extract sentiment
        sentiment_score = data.get('sentiment', {}).get('signal', 0)
        
        # Convert to our format
        if sentiment_score > 0.2:
            signal = 'BULLISH'
            confidence = min(1.0, sentiment_score + 0.3)  # Scale up for decision making
        elif sentiment_score < -0.2:
            signal = 'BEARISH'
            confidence = min(1.0, abs(sentiment_score) + 0.3)  # Scale up for decision making
        else:
            signal = 'NEUTRAL'
            confidence = 0.5
        
        result = {
            'sentiment_score': sentiment_score,
            'signal': signal,
            'confidence': confidence,
            'source_detail': 'Finnhub'
        }
        
        # Cache result
        self.sentiment_cache[cache_key] = result
        
        return result
    
    def _analyze_basic_sentiment(self, news_item):
        """
        Analyze sentiment using basic word matching.
        
        Args:
            news_item (dict): News item
            
        Returns:
            dict: Sentiment analysis results
        """
        # Extract text to analyze
        title = news_item.get('title', '').lower()
        description = news_item.get('summary', '').lower()
        text = f"{title} {description}"
        
        # Count bullish and bearish words
        bullish_count = sum(1 for word in self.bullish_words if word in text)
        bearish_count = sum(1 for word in self.bearish_words if word in text)
        
        # Calculate sentiment
        total_count = bullish_count + bearish_count
        
        if total_count == 0:
            return {
                'sentiment_score': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.5,
                'source_detail': 'Basic Analysis'
            }
        
        sentiment_score = (bullish_count - bearish_count) / total_count
        
        # Convert to signal
        if sentiment_score > 0.2:
            signal = 'BULLISH'
            confidence = min(0.8, 0.5 + sentiment_score)  # Max confidence 0.8 for basic analysis
        elif sentiment_score < -0.2:
            signal = 'BEARISH'
            confidence = min(0.8, 0.5 + abs(sentiment_score))  # Max confidence 0.8 for basic analysis
        else:
            signal = 'NEUTRAL'
            confidence = 0.5
        
        return {
            'sentiment_score': sentiment_score,
            'signal': signal,
            'confidence': confidence,
            'source_detail': 'Basic Analysis'
        }
    
    def _analyze_sentiment_with_nlp(self, text):
        """
        Analyze sentiment using NLP techniques when API is not available.
        
        Args:
            text (str): Text to analyze
            
        Returns:
            dict: Sentiment analysis results
        """
        # Convert to lowercase and clean text
        text = text.lower()
        
        # Count bullish and bearish words
        bullish_count = sum(1 for word in self.bullish_words if word in text)
        bearish_count = sum(1 for word in self.bearish_words if word in text)
        
        # Calculate sentiment score
        total_words = len(text.split())
        if total_words == 0:
            return {
                'sentiment_score': 0,
                'signal': 'NEUTRAL',
                'confidence': 0.5,
                'source_detail': 'NLP Analysis'
            }
        
        # Calculate net sentiment
        net_sentiment = bullish_count - bearish_count
        
        # Apply sigmoid function to normalize between -1 and 1
        if net_sentiment != 0:
            sentiment_score = 2 / (1 + np.exp(-0.5 * net_sentiment)) - 1
        else:
            sentiment_score = 0
        
        # Convert to signal
        if sentiment_score > 0.2:
            signal = 'BULLISH'
            confidence = min(0.75, 0.5 + sentiment_score * 0.5)
        elif sentiment_score < -0.2:
            signal = 'BEARISH'
            confidence = min(0.75, 0.5 + abs(sentiment_score) * 0.5)
        else:
            signal = 'NEUTRAL'
            confidence = 0.5
        
        return {
            'sentiment_score': sentiment_score,
            'signal': signal,
            'confidence': confidence,
            'source_detail': 'NLP Analysis'
        }
    
    def analyze_market_mood(self, days_back=3):
        """
        Analyze overall market mood from recent news.
        
        Args:
            days_back (int): Number of days to look back
            
        Returns:
            dict: Market mood analysis
        """
        try:
            # Get recent market news
            market_news = self.fetch_latest_news(['MARKET', 'SPY', 'QQQ'], days_back)
            
            if not market_news:
                return {
                    'mood': 'NEUTRAL',
                    'confidence': 0.5,
                    'description': 'No recent market news found'
                }
            
            # Flatten news from all tickers
            all_news = []
            for ticker_news in market_news.values():
                all_news.extend(ticker_news)
            
            if not all_news:
                return {
                    'mood': 'NEUTRAL',
                    'confidence': 0.5,
                    'description': 'No recent market news found'
                }
            
            # Calculate average sentiment
            total_score = 0
            bullish_count = 0
            bearish_count = 0
            neutral_count = 0
            
            for news in all_news:
                sentiment_score = news.get('sentiment_score', 0)
                total_score += sentiment_score
                
                if news.get('signal') == 'BULLISH':
                    bullish_count += 1
                elif news.get('signal') == 'BEARISH':
                    bearish_count += 1
                else:
                    neutral_count += 1
            
            avg_score = total_score / len(all_news) if all_news else 0
            
            # Determine market mood
            if avg_score > 0.3:
                mood = 'BULLISH'
                confidence = min(0.9, 0.5 + avg_score)
                description = 'Market sentiment is overall positive'
            elif avg_score < -0.3:
                mood = 'BEARISH'
                confidence = min(0.9, 0.5 + abs(avg_score))
                description = 'Market sentiment is overall negative'
            else:
                mood = 'NEUTRAL'
                confidence = 0.5 - abs(avg_score)
                description = 'Market sentiment is relatively neutral'
            
            # Add statistics to description
            description += f" ({bullish_count} bullish, {bearish_count} bearish, {neutral_count} neutral news)"
            
            return {
                'mood': mood,
                'confidence': confidence,
                'description': description,
                'avg_sentiment': avg_score,
                'news_count': len(all_news)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing market mood: {e}", exc_info=True)
            return {
                'mood': 'NEUTRAL',
                'confidence': 0.5,
                'description': f'Error analyzing market mood: {str(e)}'
            }
    
    def _get_cached_news(self, tickers, days_back):
        """
        Get cached news from database.
        
        Args:
            tickers (list): List of stock ticker symbols
            days_back (int): Number of days to look back
            
        Returns:
            dict: Dictionary of news by ticker
        """
        if not self.db_manager:
            return None
            
        try:
            # Create placeholders for SQL query
            ticker_list = ','.join([f"'{t}'" for t in tickers])
            
            query = f"""
            SELECT * FROM news
            WHERE ticker IN ({ticker_list})
            AND date >= datetime('now', '-{days_back} day')
            ORDER BY confidence DESC
            """
            
            news_items = self.db_manager.execute_query(query)
            if not news_items:
                return None
                
            # Organize by ticker
            news_by_ticker = defaultdict(list)
            for item in news_items:
                news_by_ticker[item['ticker']].append(item)
                
            return dict(news_by_ticker)
                
        except Exception as e:
            logger.error(f"Error getting cached news: {e}", exc_info=True)
            
        return None
    
    def _cache_news(self, news_by_ticker):
        """
        Cache news in database.
        
        Args:
            news_by_ticker (dict): Dictionary of news by ticker
        """
        if not self.db_manager:
            return
            
        try:
            count = 0
            for ticker, news_items in news_by_ticker.items():
                for item in news_items:
                    # Convert datetime to string if needed
                    if isinstance(item.get('date'), datetime):
                        item['date'] = item['date'].strftime('%Y-%m-%d %H:%M:%S')
                        
                    # Add creation timestamp
                    item['created_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Insert into database
                    self.db_manager.insert('news', item)
                    count += 1
                    
            logger.info(f"Cached {count} news items in database")
                
        except Exception as e:
            logger.error(f"Error caching news: {e}", exc_info=True)
