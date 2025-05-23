"""
This file contains a function to enhance the AlpacaWrapper class to handle short selling restrictions.
You can incorporate these methods into your AlpacaWrapper class.
"""

def handle_short_selling(self, symbol, qty, side, type, time_in_force):
    """
    Handle short selling restrictions for order submission.
    
    Args:
        symbol (str): Symbol to trade
        qty (int): Quantity to trade
        side (str): 'buy' or 'sell'
        type (str): 'market', 'limit', etc.
        time_in_force (str): 'day', 'gtc', etc.
        
    Returns:
        tuple: Modified (side, qty) parameters
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Only check sells for short selling issues
    if side.lower() == 'sell':
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
            logger.warning(f"Short selling attempted for {symbol}. Converting to buy order...")
            side = 'buy'  # Convert to buy instead to avoid short selling restrictions
    
    return side, qty

def submit_order_with_short_check(self, symbol, qty, side, type, time_in_force):
    """
    Submit an order with short selling protection.
    
    Args:
        symbol (str): Symbol to trade
        qty (int): Quantity to trade
        side (str): 'buy' or 'sell'
        type (str): 'market', 'limit', etc.
        time_in_force (str): 'day', 'gtc', etc.
        
    Returns:
        alpaca_trade_api.entity.Order: Order object or None if error
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        if not self.api:
            logger.error("Alpaca API not initialized")
            return None
        
        # Handle short selling restrictions
        side, qty = self.handle_short_selling(symbol, qty, side, type, time_in_force)
        
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
