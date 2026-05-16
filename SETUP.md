# Setup Guide

## Step 1 — Get your free API keys

### Alpaca (free real-time US stock data)
1. Go to https://alpaca.markets
2. Click "Sign Up" — choose the free paper trading account
3. Once inside, go to "API Keys" in the left menu
4. Click "Generate New Key"
5. Copy your API Key ID and Secret Key — save them somewhere safe
6. You will use these in the Python script below

### NewsAPI (free news headlines)
1. Go to https://newsapi.org
2. Click "Get API Key" — free tier gives 100 requests per day, enough for nightly use
3. Copy your API key

---

## Step 2 — Install Python

If you do not have Python installed:
- Mac: open Terminal, type `python3 --version`. If nothing shows, go to https://python.org and download Python 3.
- Windows: go to https://python.org, download Python 3, tick "Add to PATH" during install.

---

## Step 3 — Install required Python libraries

Open Terminal (Mac) or Command Prompt (Windows) and run:

```
pip install alpaca-trade-api requests
```

---

## Step 4 — Set up the data fetcher script

1. Download `fetch_signals.py` from this repo
2. Open it in any text editor (Notepad, TextEdit, VS Code)
3. Fill in your API keys at the top of the file:

```python
ALPACA_KEY = "your_alpaca_key_here"
ALPACA_SECRET = "your_alpaca_secret_here"
NEWS_API_KEY = "your_newsapi_key_here"
```

4. Save the file

---

## Step 5 — Run the script before each session

Every night before 9:30 PM SGT, open Terminal and run:

```
python3 fetch_signals.py
```

This will:
- Pull the top 5 pre-market movers from Alpaca
- Score each one against the 5 conditions
- Fetch the latest news headline for each stock
- Save the results to `signals.json` in the same folder

The bot in your browser will load from `signals.json` automatically.

---

## Step 6 — Host on GitHub Pages

See GITHUB.md for step-by-step instructions.
