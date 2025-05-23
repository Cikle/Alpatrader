# Alpatrader Quick Start Guide

This guide will help you quickly set up the Alpatrader bot and start trading on Alpaca's paper trading platform.

## 1. Setup Environment

### Clone Repository
```bash
git clone https://github.com/yourusername/Alpatrader.git
cd Alpatrader
```

### Create Virtual Environment
```bash
# Using venv (recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1  # For Windows PowerShell
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Configure API Keys

1. Copy the example config file:
```bash
Copy-Item .\config\config.ini.example .\config\config.ini
```

2. Edit `config/config.ini` with your API keys:
   - Alpaca API keys: Get from [Alpaca Dashboard](https://app.alpaca.markets/paper/dashboard/overview)
   - NewsAPI key: Get from [NewsAPI](https://newsapi.org/register)
   - Finnhub key: Get from [Finnhub](https://finnhub.io/register)

## 3. Run the Bot

### Start the Trading Bot
```bash
python main.py
```

### Run in Paper Trading Mode
The bot will automatically connect to Alpaca's paper trading API (as configured in `config.ini`). It will:

1. Fetch insider trades from OpenInsider
2. Get Congress trades from Senate Stock Watcher
3. Analyze news sentiment from various sources
4. Process signals and execute trades based on the inverse strategy

## 4. Monitor Performance

- Check the logs in the `logs/` directory
- Monitor your paper trading account on the Alpaca dashboard
- Review the trades executed by the bot

## 5. Run Backtests

```bash
cd src/backtests
python backtest_examples.py
```

This will run example backtests for:
- 2023 SVB collapse scenario
- 2022 Meta insider sales scenario

Results will be saved to `backtests/results/` directory.

## 6. Customization

You can customize the bot by editing the `config.ini` file:

- Adjust position sizes and confidence thresholds
- Change the sectors you want to focus on
- Modify filtering criteria for insider and Congress trades
- Adjust risk management parameters

## 7. Production Deployment

For production use:
1. Review all risk parameters carefully
2. Start with small position sizes
3. Consider using a monitoring system for alerts
4. Modify the `config.ini` to use Alpaca's live trading API instead of paper trading

## Need Help?

Refer to the full documentation in the `README.md` file or open an issue on GitHub.

Remember: This is for educational purposes only. Trade at your own risk!
