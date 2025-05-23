# Alpatrader

A Python trading bot for Alpaca paper trading that trades options inversely based on news sentiment, insider trades, and congressional trading data. This bot is designed to identify potentially meaningful signals and take the opposite position, based on the theory that retail traders often react after insiders/politicians have already made their moves.

## 🚀 Features

- **Inverse Trading Strategy**: Takes the opposite side of insider, congress, and news signals
- **Multiple Data Sources**:
  - OpenInsider for insider trades (CEO/CFO focus)
  - Senate Stock Watcher for Congress trades
  - NewsAPI/GNews for news headlines
  - Finnhub for sentiment scoring
  - SQLite database for caching data
- **Smart Signal Processing**:
  - Combines signals from multiple sources with intelligent weighting
  - Applies position sizing based on signal strength and confidence
  - Filters out noise with configurable thresholds
- **Options Trading**:
  - Uses options for stronger directional bets on high-confidence signals
  - Automated selection of option contracts with target delta (typically 0.20)
  - Configurable expiration targeting (typically 30-45 days)
  - Smaller position sizing for options (typically 2% max vs 5% for stocks)
- **Risk Management**:
  - Sector blacklisting for volatile industries
  - FOMC blackout period detection
  - Position size limits based on portfolio value
  - Signal confidence scoring
- **Backtesting**: Test strategies on historical events (SVB collapse, Meta insider sales)

## 📊 Signal Hierarchy

The bot uses a specific hierarchy to determine position sizes:

1. **Strong News + Insider/Congress**: 2x position (max 5% portfolio)
2. **Congress Only**: 1x position
3. **Insider Only**: 0.5x position (more conservative)

## 📋 Requirements

- Python 3.7+
- Alpaca brokerage account (paper trading)
- Free API keys for news and sentiment analysis

## 🔧 Installation

1. Clone the repository:
   ```
   git clone https://github.com/Cikle/Alpatrader.git
   cd Alpatrader
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure your API keys in `config/config.ini`

## 🏃‍♀️ Running the Bot

Start by testing the scrapers to make sure everything is working:

```
python test_scrapers.py
```

Then run the actual trading bot:

```
python main.py
```

The bot will run continuously, fetching data from all sources and executing trades when the market is open according to the signal hierarchy.

## 📈 Backtesting

Run the example backtests:

```
cd src/backtests
python backtest_examples.py
```

Example backtest scenarios include:
- **2023 SVB Collapse**: The bot identified insiders selling before the public news broke, getting ahead of the 60% price drop
- **2021-2022 Meta Insider Sales**: Shows how the bot would have responded to repeated CEO/CFO sales before Meta's 26% price drop

Backtests generate performance reports and visualization charts in the `logs/backtests` directory.

## 📁 Project Structure

```
Alpatrader/
├── config/
│   ├── config.ini           # Configuration settings (your API keys)
│   └── config.ini.example   # Example configuration template
├── logs/                    # Log files and cache database
│   ├── alpatrader.db        # SQLite database for caching data
│   └── backtests/           # Backtest results and charts
├── src/
│   ├── backtests/           # Backtesting modules
│   │   └── backtest_examples.py # Example backtest implementations
│   ├── data/                # Data source modules
│   │   ├── congress_data.py # Congress trading data scraper
│   │   ├── insider_data.py  # Insider trading data scraper
│   │   └── news_data.py     # News and sentiment analysis
│   ├── models/              # Trading models
│   │   └── signal_processor.py # Signal processing logic
│   ├── strategies/          # Trading strategies
│   │   └── inverse_strategy.py # Inverse trading implementation
│   └── utils/               # Utility modules
│       ├── alpaca_wrapper.py # Alpaca API wrapper
│       └── db_manager.py     # SQLite database manager
├── main.py                  # Main entry point
├── test_scrapers.py         # Tool for testing data scrapers
├── requirements.txt         # Python dependencies
└── import_test.py           # Simple module import test script
```

## 🧠 Signal Processing Logic

### Data Collection
1. **Insider Trades**: Focuses on CEO/CFO transactions above $200,000
2. **Congress Trades**: Monitors Senator trades below $1M with a 24-hour delay
3. **News Sentiment**: Uses natural language processing and sentiment APIs to analyze news mood

### Signal Processing
1. The `SignalProcessor` collects data from all sources
2. Signals are filtered by confidence and relevance
3. For each ticker, the best signal is determined based on the hierarchy
4. Position size is calculated based on signal strength and portfolio value
5. The `InverseStrategy` executes trades based on the processed signals

### Position Sizing
- Base position size is configurable (default: 5% maximum of portfolio)
- Signal strength multipliers are applied:
  - Strong News + Insider/Congress: 2x multiplier
  - Congress Only: 1x multiplier
  - Insider Only: 0.5x multiplier

### Risk Management
- FOMC blackout periods are skipped
- Sectors can be blacklisted or whitelisted
- Position size is capped at a percentage of portfolio
- Multiple data sources helps validate signals
- Datapoints are cached in SQLite for offline analysis

## 🔄 Options Trading

The bot implements an options trading strategy for high-confidence signals:

- **Signal Selection**: Only signals with confidence > 0.7 are considered for options trading
- **Inverse Trading Logic**:
  - For BULLISH signals, the bot buys PUT options (taking a bearish position)
  - For BEARISH signals, the bot buys CALL options (taking a bullish position)
- **Contract Selection**:
  - Targets options with ~0.20 delta (approximately 20% out-of-the-money)
  - Aims for 30-45 day expiration to balance theta decay and time for the move to happen
  - Automatically selects the contract closest to the target parameters
- **Position Sizing**:
  - Uses smaller allocation than stock trades (typically 2% vs 5% max)
  - Number of contracts is calculated based on price and portfolio allocation
- **Configuration**:
  - Options trading can be enabled/disabled in the config file
  - Delta target, expiration, and position sizing are all configurable

## ⚠️ Disclaimer

```
DISCLAIMER: Not financial advice. Insider data may be delayed.
This tool is for educational and research purposes only.
Use at your own risk. Past performance is not indicative of future results.
```

## 📝 License

MIT License

## 🙏 Acknowledgements

- [Alpaca](https://alpaca.markets/) for their excellent trading API
- [OpenInsider](http://openinsider.com/) for insider trading data
- [Senate Stock Watcher](https://senatestockwatcher.com/) for congressional trading data
