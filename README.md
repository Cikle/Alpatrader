# Alpatrader

A Python trading bot for Alpaca paper trading that trades options inversely based on news sentiment, insider trades, and congressional trading data.

## 🚀 Features

- **Inverse Trading Strategy**: Takes the opposite side of insider, congress, and news signals
- **Multiple Data Sources**:
  - OpenInsider for insider trades (CEO/CFO)
  - Senate Stock Watcher for Congress trades
  - NewsAPI/GNews for news headlines
  - Finnhub for sentiment scoring
- **Smart Signal Processing**:
  - Combines signals from multiple sources
  - Applies position sizing based on signal strength
  - Filters out noise with configurable thresholds
- **Risk Management**:
  - Sector blacklisting for volatile industries
  - FOMC blackout period detection
  - Position size limits based on portfolio value
- **Backtesting**: Test strategies on historical data

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

```
python main.py
```

## 📈 Backtesting

Run the example backtests:

```
cd src/backtests
python backtest_examples.py
```

Example backtest scenarios include:
- 2023 SVB collapse (Congress bought banks)
- 2022 Meta insider sales (before crash)

## 📁 Project Structure

```
Alpatrader/
├── config/
│   └── config.ini           # Configuration settings
├── logs/                    # Log files and cache database
├── src/
│   ├── backtests/           # Backtesting modules
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
└── main.py                  # Main entry point
```

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
