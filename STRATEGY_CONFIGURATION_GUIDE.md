# Configurable Trading Strategy Guide

## Overview

Your trading bot now has fully configurable strategies that allow you to control how it responds to insider and Congress trading signals. You can switch between different approaches without modifying any code.

## Configuration Options

### Strategy Types

**`inverse`** - Trade opposite to the signal
- When insiders/Congress buy → Bot sells (or buys puts)
- When insiders/Congress sell → Bot buys (or buys calls)
- This is the contrarian approach

**`normal`** - Follow the signal
- When insiders/Congress buy → Bot buys (or buys calls)  
- When insiders/Congress sell → Bot sells (or buys puts)
- This is the momentum/following approach

**`disabled`** - Ignore signals completely
- The bot will not consider signals from this source at all
- Useful for testing or when you want to focus on only one type of signal

## Configuration File Location

Edit the settings in: `config/config.ini`

```ini
[trading]
# INSIDER STRATEGY: How to trade based on insider transactions
# inverse = trade opposite to insiders (sell when they buy, buy when they sell)
# normal = follow insiders (buy when they buy, sell when they sell)  
# disabled = ignore insider signals completely
insider_strategy = inverse

# CONGRESS STRATEGY: How to trade based on Congress member transactions
# inverse = trade opposite to Congress (sell when they buy, buy when they sell)
# normal = follow Congress (buy when they buy, sell when they sell)
# disabled = ignore Congress signals completely  
congress_strategy = inverse
```

## Strategy Combinations

You can mix and match strategies for maximum flexibility:

### Popular Combinations

1. **Full Contrarian** (Default)
   ```ini
   insider_strategy = inverse
   congress_strategy = inverse
   ```
   - Trade opposite to both insiders and Congress
   - Based on the theory that they have access to information not yet public

2. **Mixed Strategy**
   ```ini
   insider_strategy = inverse
   congress_strategy = normal
   ```
   - Trade opposite to insiders but follow Congress trades
   - Different trust levels for different sources

3. **Congress Only**
   ```ini
   insider_strategy = disabled
   congress_strategy = inverse
   ```
   - Ignore insider trades completely, only trade opposite to Congress
   - Focus on political trading patterns

4. **Momentum Strategy**
   ```ini
   insider_strategy = normal
   congress_strategy = normal
   ```
   - Follow both insider and Congress trades
   - Assume they know something and ride the momentum

## How It Works

### Signal Processing Hierarchy

The bot processes signals in this priority order:

1. **Strong News + Insider/Congress** (Highest Priority)
   - When strong news aligns with transformed insider/Congress signals
   - Position size multiplied by `strong_news_multiplier` (default: 2x)

2. **Congress Only** (Medium Priority)  
   - Congress signals transformed according to `congress_strategy`
   - Position size multiplied by `congress_only_multiplier` (default: 1x)

3. **Insider Only** (Lowest Priority)
   - Insider signals transformed according to `insider_strategy`  
   - Position size multiplied by `insider_only_multiplier` (default: 0.5x)

### Strategy Transformation

**Before transformation:**
- Insider buys AAPL → Original signal: "buy"
- Congress sells AAPL → Original signal: "sell"

**After transformation (inverse strategies):**
- Insider buys AAPL → Bot signal: "sell" (opposite)
- Congress sells AAPL → Bot signal: "buy" (opposite)

**After transformation (normal strategies):**
- Insider buys AAPL → Bot signal: "buy" (follow)
- Congress sells AAPL → Bot signal: "sell" (follow)

## Logging and Monitoring

The bot logs all strategy decisions:

```
INFO - Signal Processor initialized with strategies: Insider=inverse, Congress=normal
INFO - Congress trade by Jane Smith (normal strategy)
INFO - Insider trade by John Doe (CEO) (inverse strategy)
```

This helps you track which strategy is being applied to each trade.

## Testing Your Configuration

Use the test script to verify your configuration:

```bash
python test_strategy_config.py
```

This will:
- ✅ Verify configuration loading
- ✅ Test all strategy combinations  
- ✅ Show signal processing examples
- ✅ Confirm everything is working

## Real-World Usage Examples

### Scenario 1: Market Uncertainty
```ini
insider_strategy = disabled
congress_strategy = inverse
```
During volatile periods, focus only on Congress trades and trade opposite to reduce noise.

### Scenario 2: Bull Market
```ini
insider_strategy = normal  
congress_strategy = normal
```
During strong bull markets, follow the smart money and ride momentum.

### Scenario 3: Testing Phase
```ini
insider_strategy = inverse
congress_strategy = disabled
```
Test only insider signals while ignoring Congress trades to isolate performance.

## Performance Monitoring

Track the performance of different strategies:

1. **Backtest different configurations** using historical data
2. **Monitor win rates** by strategy type in your logs
3. **Adjust position multipliers** based on strategy performance:
   - `insider_only_multiplier`: Default 0.5 (50% position size)
   - `congress_only_multiplier`: Default 1.0 (100% position size)  
   - `strong_news_multiplier`: Default 2.0 (200% position size)

## Advanced Configuration

### Fine-tuning Thresholds

```ini
[trading]
# Minimum confidence required for insider trades
min_insider_confidence = 0.6

# Minimum confidence required for Congress trades  
min_congress_confidence = 0.7

# Minimum transaction size to consider for insiders
min_insider_transaction_size = 200000

# Maximum transaction size to consider for Congress
max_congress_transaction_size = 1000000
```

### Timing Controls

```ini
[trading]
# Hours to wait after insider trade before acting
insider_delay_hours = 0

# Hours to wait after Congress trade before acting  
congress_delay_hours = 24
```

## Troubleshooting

### Common Issues

1. **Invalid strategy values** → Bot defaults to 'inverse' and logs warning
2. **Missing configuration** → Bot uses fallback values
3. **No signals generated** → Check if strategies are set to 'disabled'

### Validation

The bot automatically validates your configuration:
- Only accepts: `inverse`, `normal`, `disabled`
- Logs warnings for invalid values
- Falls back to safe defaults

## Summary

The configurable strategy system gives you complete control over how your trading bot responds to insider and Congress signals. You can:

- ✅ Switch between contrarian and momentum strategies
- ✅ Disable specific signal sources  
- ✅ Mix different approaches for each source
- ✅ Test configurations safely
- ✅ Monitor strategy performance
- ✅ Adjust without code changes

Start with the default `inverse` strategy for both sources, then experiment with different combinations based on market conditions and your risk tolerance.
