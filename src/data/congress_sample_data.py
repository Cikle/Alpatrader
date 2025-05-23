"""
Sample data method for the Congress scraper.
This method provides fallback data when the API is unavailable.
Add this method to your SenateScraper class.
"""

def _get_sample_data(self):
    """
    Generate sample Congress trade data for testing/fallback purposes.
    
    Returns:
        list: List of sample Congress trades
    """
    import logging
    from datetime import datetime, timedelta
    import random
    
    logger = logging.getLogger(__name__)
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
        {"company": "Consumer Products Ltd", "ticker": "CSMR"},
        {"company": "Advanced Manufacturing Co", "ticker": "MANU"},
        {"company": "Aerospace Technologies", "ticker": "AERO"},
        {"company": "BioTech Research", "ticker": "BIOR"}
    ]
    
    # Sample transaction types
    buy_transactions = ["Purchase", "Partial Purchase", "Buy"]
    sell_transactions = ["Sale", "Partial Sale", "Sell"]
    
    # Generate sample data
    sample_trades = []
    
    # Current date for reference
    today = datetime.now()
    
    # Create 10-15 sample trades
    for i in range(random.randint(10, 15)):
        # Random date within the last month but not today (respecting delay_hours)
        days_ago = random.randint(self.delay_hours // 24 + 1, 30)
        trade_date = today - timedelta(days=days_ago)
        
        # Random company
        company_data = random.choice(companies)
        
        # Random buy/sell with 60% buys
        is_buy = random.random() < 0.6
        transaction_type = random.choice(buy_transactions if is_buy else sell_transactions)
        
        # Random transaction value between $1,000 and $max_transaction_size
        value_range_start = random.randint(1000, min(100000, int(self.max_transaction_size * 0.3)))
        value_range_end = random.randint(value_range_start, min(value_range_start * 5, int(self.max_transaction_size * 0.8)))
        estimated_value = (value_range_start + value_range_end) / 2
        
        # Determine signal and confidence
        signal = 'BULLISH' if is_buy else 'BEARISH'
        confidence = min(0.8, estimated_value / self.max_transaction_size)
        
        # Create trade data
        trade = {
            'date': trade_date,
            'politician': random.choice(politicians),
            'ticker': company_data['ticker'],
            'company': company_data['company'],
            'transaction_type': transaction_type,
            'estimated_value': estimated_value,
            'asset_type': "Common Stock",
            'signal': signal,
            'confidence': confidence,
            'source': 'congress',
            'source_detail': 'Senate Stock Watcher (Sample Data)',
            'is_sample_data': True
        }
        
        sample_trades.append(trade)
    
    logger.info(f"Generated {len(sample_trades)} sample Congress trades")
    return sample_trades
