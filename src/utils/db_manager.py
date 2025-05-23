#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database manager for caching data from various sources.
"""

import logging
import os
import sqlite3
import json
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manager for SQLite database to cache insider, congress, and news data.
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        if not db_path:
            # Use default path in logs directory
            db_path = os.path.join('logs', 'alpatrader.db')
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create insider trades table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS insider_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                company TEXT,
                insider TEXT,
                title TEXT,
                trade_type TEXT,
                price REAL,
                quantity INTEGER,
                value REAL,
                ownership_change REAL,
                sector TEXT,
                signal TEXT,
                source TEXT,
                source_detail TEXT,
                confidence REAL,
                created_at TEXT
            )
            ''')
            
            # Create congress trades table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS congress_trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                company TEXT,
                politician TEXT,
                transaction_type TEXT,
                estimated_value REAL,
                asset_type TEXT,
                signal TEXT,
                source TEXT,
                source_detail TEXT,
                confidence REAL,
                created_at TEXT
            )
            ''')
            
            # Create news table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT,
                title TEXT,
                url TEXT,
                source TEXT,
                date TEXT,
                summary TEXT,
                sentiment_score REAL,
                signal TEXT,
                confidence REAL,
                source_detail TEXT,
                created_at TEXT
            )
            ''')
            
            # Create trades table (for executed trades)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                ticker TEXT,
                action TEXT,
                quantity INTEGER,
                price REAL,
                value REAL,
                signal_id INTEGER,
                signal_type TEXT,
                confidence REAL,
                created_at TEXT
            )
            ''')
            
            # Create indices for faster lookups
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_insider_ticker ON insider_trades (ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_insider_date ON insider_trades (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_congress_ticker ON congress_trades (ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_congress_date ON congress_trades (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_ticker ON news (ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_date ON news (date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_ticker ON trades (ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_date ON trades (date)')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}", exc_info=True)
    
    def insert(self, table, data):
        """
        Insert data into a table.
        
        Args:
            table (str): Table name
            data (dict): Data to insert
            
        Returns:
            int: Row ID of inserted record or None if error
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Filter out keys that don't correspond to columns in the table
            columns = self._get_table_columns(cursor, table)
            filtered_data = {k: v for k, v in data.items() if k in columns}
            
            # Build SQL query
            columns_str = ', '.join(filtered_data.keys())
            placeholders = ', '.join(['?' for _ in filtered_data])
            
            query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"
            
            # Execute query
            cursor.execute(query, list(filtered_data.values()))
            
            # Get ID of inserted row
            row_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return row_id
            
        except Exception as e:
            logger.error(f"Error inserting into {table}: {e}", exc_info=True)
            return None
    
    def execute_query(self, query, params=None):
        """
        Execute a SQL query and return results as a list of dictionaries.
        
        Args:
            query (str): SQL query to execute
            params (tuple): Parameters for the query
            
        Returns:
            list: Query results as a list of dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            # Enable row factory to get results as dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Execute query
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get results
            results = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error executing query: {e}", exc_info=True)
            return []
    
    def save_insider_trades(self, trades):
        """
        Save insider trades to the database.
        
        Args:
            trades (list): List of insider trade dictionaries
        """
        if not trades:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            for trade in trades:
                # Convert date object to string
                date_str = trade['date'].isoformat() if isinstance(trade['date'], datetime) else trade['date']
                
                cursor.execute('''
                INSERT INTO insider_trades 
                (date, ticker, company, insider, title, trade_type, price, quantity, 
                value, ownership_change, sector, signal, source, source_detail, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str, 
                    trade.get('ticker', ''), 
                    trade.get('company', ''), 
                    trade.get('insider', ''), 
                    trade.get('title', ''), 
                    trade.get('trade_type', ''), 
                    trade.get('price', 0.0), 
                    trade.get('quantity', 0), 
                    trade.get('value', 0.0), 
                    trade.get('ownership_change', 0.0), 
                    trade.get('sector', ''), 
                    trade.get('signal', 'NEUTRAL'), 
                    trade.get('source', 'insider'), 
                    trade.get('source_detail', ''), 
                    trade.get('confidence', 0.5),
                    now
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(trades)} insider trades to database")
            
        except Exception as e:
            logger.error(f"Error saving insider trades: {e}", exc_info=True)
    
    def save_congress_trades(self, trades):
        """
        Save congress trades to the database.
        
        Args:
            trades (list): List of congress trade dictionaries
        """
        if not trades:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            
            for trade in trades:
                # Convert date object to string
                date_str = trade['date'].isoformat() if isinstance(trade['date'], datetime) else trade['date']
                
                cursor.execute('''
                INSERT INTO congress_trades 
                (date, ticker, company, politician, transaction_type, estimated_value, 
                asset_type, signal, source, source_detail, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    date_str, 
                    trade.get('ticker', ''), 
                    trade.get('company', ''), 
                    trade.get('politician', ''), 
                    trade.get('transaction_type', ''), 
                    trade.get('estimated_value', 0.0), 
                    trade.get('asset_type', ''), 
                    trade.get('signal', 'NEUTRAL'), 
                    trade.get('source', 'congress'), 
                    trade.get('source_detail', ''), 
                    trade.get('confidence', 1.0),
                    now
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(trades)} Congress trades to database")
            
        except Exception as e:
            logger.error(f"Error saving Congress trades: {e}", exc_info=True)
    
    def save_news(self, news_by_ticker):
        """
        Save news items to the database.
        
        Args:
            news_by_ticker (dict): Dictionary of news items by ticker
        """
        if not news_by_ticker:
            return
            
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            count = 0
            
            for ticker, news_items in news_by_ticker.items():
                for news in news_items:
                    # Convert date object to string
                    date_str = news['date'].isoformat() if isinstance(news['date'], datetime) else news['date']
                    
                    cursor.execute('''
                    INSERT INTO news 
                    (ticker, title, url, source, date, summary, sentiment_score, 
                    signal, confidence, source_detail, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ticker, 
                        news.get('title', ''), 
                        news.get('url', ''), 
                        news.get('source', ''), 
                        date_str, 
                        news.get('summary', ''), 
                        news.get('sentiment_score', 0.0), 
                        news.get('signal', 'NEUTRAL'), 
                        news.get('confidence', 0.5),
                        news.get('source_detail', ''),
                        now
                    ))
                    count += 1
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {count} news items to database")
            
        except Exception as e:
            logger.error(f"Error saving news: {e}", exc_info=True)
    
    def save_trade(self, trade):
        """
        Save executed trade to the database.
        
        Args:
            trade (dict): Trade dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            now = datetime.now().isoformat()
            date_str = trade['date'].isoformat() if isinstance(trade['date'], datetime) else trade['date']
            
            cursor.execute('''
            INSERT INTO trades 
            (date, ticker, action, quantity, price, total_value, 
            signal, confidence, source, source_detail, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                date_str, 
                trade.get('ticker', ''), 
                trade.get('action', ''), 
                trade.get('quantity', 0), 
                trade.get('price', 0.0), 
                trade.get('total_value', 0.0), 
                trade.get('signal', 'NEUTRAL'), 
                trade.get('confidence', 0.5),
                trade.get('source', ''),
                trade.get('source_detail', ''),
                now
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved trade for {trade.get('ticker')} to database")
            
        except Exception as e:
            logger.error(f"Error saving trade: {e}", exc_info=True)
    
    def get_recent_insider_trades(self, days=14):
        """
        Get recent insider trades from the database.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            list: List of insider trades
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
            SELECT * FROM insider_trades 
            WHERE date >= ? 
            ORDER BY date DESC
            ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            trades = []
            for row in rows:
                trade = dict(row)
                
                # Convert string dates back to datetime
                try:
                    trade['date'] = datetime.fromisoformat(trade['date'])
                except ValueError:
                    pass
                    
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent insider trades: {e}", exc_info=True)
            return []
    
    def get_recent_congress_trades(self, days=14):
        """
        Get recent congress trades from the database.
        
        Args:
            days (int): Number of days to look back
            
        Returns:
            list: List of congress trades
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
            SELECT * FROM congress_trades 
            WHERE date >= ? 
            ORDER BY date DESC
            ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            trades = []
            for row in rows:
                trade = dict(row)
                
                # Convert string dates back to datetime
                try:
                    trade['date'] = datetime.fromisoformat(trade['date'])
                except ValueError:
                    pass
                    
                trades.append(trade)
            
            return trades
            
        except Exception as e:
            logger.error(f"Error getting recent congress trades: {e}", exc_info=True)
            return []
    
    def get_recent_news(self, tickers=None, days=7):
        """
        Get recent news from the database.
        
        Args:
            tickers (list): List of tickers to filter by
            days (int): Number of days to look back
            
        Returns:
            dict: Dictionary of news by ticker
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            if tickers:
                placeholders = ','.join(['?'] * len(tickers))
                cursor.execute(f'''
                SELECT * FROM news 
                WHERE date >= ? AND ticker IN ({placeholders})
                ORDER BY date DESC
                ''', [cutoff_date] + tickers)
            else:
                cursor.execute('''
                SELECT * FROM news 
                WHERE date >= ? 
                ORDER BY date DESC
                ''', (cutoff_date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Group by ticker
            news_by_ticker = {}
            for row in rows:
                news = dict(row)
                
                # Convert string dates back to datetime
                try:
                    news['date'] = datetime.fromisoformat(news['date'])
                except ValueError:
                    pass
                
                ticker = news['ticker']
                if ticker not in news_by_ticker:
                    news_by_ticker[ticker] = []
                news_by_ticker[ticker].append(news)
            
            return news_by_ticker
            
        except Exception as e:
            logger.error(f"Error getting recent news: {e}", exc_info=True)
            return {}
    
    def get_strong_news_signals(self, threshold=0.7, days=3):
        """
        Get strong news signals with confidence above the threshold.
        
        Args:
            threshold (float): Confidence threshold
            days (int): Number of days to look back
            
        Returns:
            list: List of news signals
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute('''
            SELECT * FROM news 
            WHERE date >= ? AND confidence >= ? AND signal != 'NEUTRAL'
            ORDER BY confidence DESC, date DESC
            ''', (cutoff_date, threshold))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            signals = []
            for row in rows:
                signal = dict(row)
                
                # Convert string dates back to datetime
                try:
                    signal['date'] = datetime.fromisoformat(signal['date'])
                except ValueError:
                    pass
                    
                signals.append(signal)
            
            return signals
            
        except Exception as e:
            logger.error(f"Error getting strong news signals: {e}", exc_info=True)
            return []
    
    def get_all_signals_for_ticker(self, ticker, days=14):
        """
        Get all signals for a specific ticker from all sources.
        
        Args:
            ticker (str): Stock ticker symbol
            days (int): Number of days to look back
            
        Returns:
            dict: Dictionary of signals by source
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate cutoff date
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Get insider trades
            cursor.execute('''
            SELECT * FROM insider_trades 
            WHERE ticker = ? AND date >= ?
            ORDER BY date DESC
            ''', (ticker, cutoff_date))
            
            insider_rows = cursor.fetchall()
            
            # Get congress trades
            cursor.execute('''
            SELECT * FROM congress_trades 
            WHERE ticker = ? AND date >= ?
            ORDER BY date DESC
            ''', (ticker, cutoff_date))
            
            congress_rows = cursor.fetchall()
            
            # Get news
            cursor.execute('''
            SELECT * FROM news 
            WHERE ticker = ? AND date >= ?
            ORDER BY date DESC
            ''', (ticker, cutoff_date))
            
            news_rows = cursor.fetchall()
            
            conn.close()
            
            # Convert to dictionaries
            insider_trades = [dict(row) for row in insider_rows]
            congress_trades = [dict(row) for row in congress_rows]
            news_items = [dict(row) for row in news_rows]
            
            # Convert string dates back to datetime
            for items in [insider_trades, congress_trades, news_items]:
                for item in items:
                    try:
                        item['date'] = datetime.fromisoformat(item['date'])
                    except ValueError:
                        pass
            
            return {
                'insider': insider_trades,
                'congress': congress_trades,
                'news': news_items
            }
            
        except Exception as e:
            logger.error(f"Error getting signals for {ticker}: {e}", exc_info=True)
            return {'insider': [], 'congress': [], 'news': []}
    
    def get_data(self, table, filters=None, order_by=None, limit=None):
        """
        Get data from a table with optional filters.
        
        Args:
            table (str): Table name
            filters (dict): Dictionary of column=value pairs for WHERE clause
            order_by (str): Column to order by (with optional DESC)
            limit (int): Maximum number of records to return
            
        Returns:
            list: Query results as a list of dictionaries
        """
        try:
            query = f"SELECT * FROM {table}"
            
            params = []
            
            # Add WHERE clause if filters provided
            if filters:
                where_clauses = []
                for column, value in filters.items():
                    where_clauses.append(f"{column} = ?")
                    params.append(value)
                
                query += f" WHERE {' AND '.join(where_clauses)}"
            
            # Add ORDER BY clause if provided
            if order_by:
                query += f" ORDER BY {order_by}"
            
            # Add LIMIT clause if provided
            if limit:
                query += f" LIMIT {limit}"
            
            return self.execute_query(query, tuple(params))
            
        except Exception as e:
            logger.error(f"Error getting data from {table}: {e}", exc_info=True)
            return []
    
    def delete_old_data(self, days=30):
        """
        Delete data older than the specified number of days.
        
        Args:
            days (int): Number of days to keep
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old data from all tables
            for table in ['insider_trades', 'congress_trades', 'news', 'trades']:
                cursor.execute(f"""
                DELETE FROM {table}
                WHERE date < datetime('now', '-{days} day')
                """)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted data older than {days} days")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting old data: {e}", exc_info=True)
            return False
    
    def _get_table_columns(self, cursor, table):
        """
        Get column names for a table.
        
        Args:
            cursor (sqlite3.Cursor): Database cursor
            table (str): Table name
            
        Returns:
            list: List of column names
        """
        cursor.execute(f"PRAGMA table_info({table})")
        return [row[1] for row in cursor.fetchall()]
    
    def export_to_csv(self, table, output_path=None):
        """
        Export a table to a CSV file.
        
        Args:
            table (str): Table name
            output_path (str): Path to output file
            
        Returns:
            str: Path to the exported file or None if error
        """
        try:
            if not output_path:
                # Use default path in logs directory
                os.makedirs('exports', exist_ok=True)
                output_path = os.path.join('exports', f"{table}_{datetime.now().strftime('%Y%m%d')}.csv")
            
            # Get data
            data = self.get_data(table)
            
            if not data:
                logger.warning(f"No data found in {table}")
                return None
            
            # Convert to DataFrame and export
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported {len(df)} rows from {table} to {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting {table} to CSV: {e}", exc_info=True)
            return None
    
    def get_statistics(self):
        """
        Get statistics about the database.
        
        Returns:
            dict: Dictionary with statistics
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Get table counts
            for table in ['insider_trades', 'congress_trades', 'news', 'trades']:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f"{table}_count"] = cursor.fetchone()[0]
            
            # Get signal counts
            cursor.execute("SELECT signal, COUNT(*) FROM insider_trades GROUP BY signal")
            stats['insider_signals'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT signal, COUNT(*) FROM congress_trades GROUP BY signal")
            stats['congress_signals'] = dict(cursor.fetchall())
            
            cursor.execute("SELECT signal, COUNT(*) FROM news GROUP BY signal")
            stats['news_signals'] = dict(cursor.fetchall())
            
            # Get date ranges
            for table in ['insider_trades', 'congress_trades', 'news', 'trades']:
                cursor.execute(f"SELECT MIN(date), MAX(date) FROM {table}")
                min_date, max_date = cursor.fetchone()
                stats[f"{table}_date_range"] = (min_date, max_date)
            
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}", exc_info=True)
            return {}
