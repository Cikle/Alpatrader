"""
Short selling handling method for AlpacaWrapper.

Add this method to your AlpacaWrapper class to handle short selling scenarios.
"""

def _handle_short_selling(self, symbol, qty, side):
    """
    Handle short selling restrictions.
    
    Args:
        symbol (str): Stock symbol
        qty (int): Quantity to trade
        side (str): 'buy' or 'sell'
        
    Returns:
        tuple: (side, qty) tuple with potentially modified values
    """
    if side.lower() != 'sell':
        return side, qty
        
    try:
        # Check current position first to determine if it's a short sell
        try:
            position = self.api.get_position(symbol)
            # If position exists, check if qty is greater than position
            current_qty = float(position.qty)
            if current_qty < qty:
                self.logger.warning(f"Reducing sell order for {symbol} from {qty} to {current_qty} to avoid short selling")
                qty = current_qty
        except Exception:
            # No position exists, this would be a short sell
            self.logger.warning(f"Short selling attempted for {symbol}. Converting to buy order...")
            side = 'buy'  # Convert to buy instead to avoid short selling restrictions
    except Exception as e:
        self.logger.error(f"Error handling short selling for {symbol}: {e}")
        # Default to safer option - convert to buy
        side = 'buy'
        
    return side, qty
