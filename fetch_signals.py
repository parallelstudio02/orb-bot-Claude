"""
ORB Signal Bot — Pre-market data fetcher
Run this every night before 9:30 PM SGT (8:30 AM EST)

Pulls top 5 pre-market movers from Alpaca, scores them,
fetches news headlines, and saves to signals.json
"""

import requests
import json
import os
from datetime import datetime, timezone

# ─────────────────────────────────────────────
# FILL IN YOUR API KEYS HERE
# ─────────────────────────────────────────────
ALPACA_KEY    = "your_alpaca_key_here"
ALPACA_SECRET = "your_alpaca_secret_here"
NEWS_API_KEY  = "your_newsapi_key_here"
# ─────────────────────────────────────────────

ALPACA_BASE   = "https://data.alpaca.markets/v2"
ALPACA_TRADE  = "https://paper-api.alpaca.markets/v2"
NEWS_BASE     = "https://newsapi.org/v2"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET,
}

# Stocks to watch — good candidates for ORB at low price range
# You can expand this list. Keep prices roughly $5–$30.
WATCHLIST = [
    "HOOD", "SOFI", "MARA", "RIOT", "IONQ",
    "OPEN", "CLOV", "SNDL", "FFIE", "PSFE",
    "TLRY", "SIRI", "CLSK", "BITF", "HUT",
    "WKHS", "NKLA", "GOEV", "RIDE", "ENVX",
    "SPCE", "WISH", "CTRM", "ATER", "BBIG",
    "PROG", "OCGN", "PERI", "GFAI", "IDEX"
]


def get_prev_close(symbols):
    """Get previous day closing prices for a list of symbols."""
    result = {}
    try:
        url = f"{ALPACA_BASE}/stocks/bars"
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "limit": 2,
            "adjustment": "raw",
            "feed": "iex"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        bars = data.get("bars", {})
        for sym, bar_list in bars.items():
            if bar_list:
                result[sym] = bar_list[-1]["c"]  # closing price
    except Exception as e:
        print(f"Error fetching prev close: {e}")
    return result


def get_premarket_quotes(symbols):
    """Get latest pre-market quotes."""
    result = {}
    try:
        url = f"{ALPACA_BASE}/stocks/trades/latest"
        params = {"symbols": ",".join(symbols), "feed": "iex"}
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        trades = data.get("trades", {})
        for sym, trade in trades.items():
            result[sym] = trade.get("p", 0)
    except Exception as e:
        print(f"Error fetching quotes: {e}")
    return result


def get_premarket_volume(symbols):
    """Get pre-market volume using 1-min bars since 4 AM EST."""
    result = {}
    try:
        url = f"{ALPACA_BASE}/stocks/bars"
        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-%dT12:00:00Z")  # 4 AM EST = 12 PM UTC (approx)
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Min",
            "start": start,
            "adjustment": "raw",
            "feed": "iex"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        bars = data.get("bars", {})
        for sym, bar_list in bars.items():
            total_vol = sum(b.get("v", 0) for b in bar_list)
            result[sym] = total_vol
    except Exception as e:
        print(f"Error fetching pre-market volume: {e}")
    return result


def get_avg_volume(symbols):
    """Get 20-day average daily volume."""
    result = {}
    try:
        url = f"{ALPACA_BASE}/stocks/bars"
        params = {
            "symbols": ",".join(symbols),
            "timeframe": "1Day",
            "limit": 20,
            "adjustment": "raw",
            "feed": "iex"
        }
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        bars = data.get("bars", {})
        for sym, bar_list in bars.items():
            if bar_list:
                avg = sum(b.get("v", 0) for b in bar_list) / len(bar_list)
                result[sym] = avg
    except Exception as e:
        print(f"Error fetching avg volume: {e}")
    return result


def get_news(ticker):
    """Fetch latest news headline for a ticker."""
    try:
        url = f"{NEWS_BASE}/everything"
        params = {
            "q": ticker,
            "sortBy": "publishedAt",
            "pageSize": 1,
            "language": "en",
            "apiKey": NEWS_API_KEY
        }
        r = requests.get(url, params=params, timeout=8)
        data = r.json()
        articles = data.get("articles", [])
        if articles:
            a = articles[0]
            title = a.get("title", "")
            source = a.get("source", {}).get("name", "")
            if title:
                clean = title.split(" - ")[0]  # remove source suffix
                return f"{clean} ({source})" if source else clean
    except Exception as e:
        print(f"News error for {ticker}: {e}")
    return "No news found for today."


def score_signal(gap_pct, pm_vol, avg_vol, has_news, price, spy_ok=True):
    """Score a signal out of 5."""
    score = 0
    if has_news:      score += 1
    if pm_vol > 0 and avg_vol > 0 and (pm_vol / avg_vol) >= 0.15:  # 15% of daily vol in pre-market
        score += 1
    if gap_pct >= 2.0: score += 1
    if spy_ok:         score += 1
    if 5 <= price <= 30: score += 1
    return score


def calc_stop(price, gap_pct):
    """
    Estimate a reasonable stop loss distance based on price and gap size.
    Bigger gap = wider stop. Keep stop between 1.5% and 4% of price.
    """
    pct = max(0.015, min(0.04, gap_pct / 100 * 0.6))
    stop = round(price * pct, 2)
    # Minimum stop of $0.10
    return max(0.10, stop)


def fmt_vol(v):
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    elif v >= 1_000:
        return f"{v/1_000:.0f}K"
    return str(int(v))


def main():
    print("Fetching pre-market data...")
    print(f"Scanning {len(WATCHLIST)} symbols\n")

    prev_closes  = get_prev_close(WATCHLIST)
    pm_quotes    = get_premarket_quotes(WATCHLIST)
    pm_volumes   = get_premarket_volume(WATCHLIST)
    avg_volumes  = get_avg_volume(WATCHLIST)

    candidates = []

    for sym in WATCHLIST:
        prev  = prev_closes.get(sym, 0)
        price = pm_quotes.get(sym, 0)
        pm_v  = pm_volumes.get(sym, 0)
        avg_v = avg_volumes.get(sym, 1)

        if prev <= 0 or price <= 0:
            continue

        gap_pct = ((price - prev) / prev) * 100

        # Only interested in gap-ups above 1.5%
        if gap_pct < 1.5:
            continue

        # Only interested in stocks priced $2–$35
        if not (2 <= price <= 35):
            continue

        pm_vol_x = round(pm_v / avg_v, 1) if avg_v > 0 else 0
        has_news = False  # will fetch below for top candidates
        spy_ok = True     # assume ok; you can check SPY manually

        score = score_signal(gap_pct, pm_v, avg_v, has_news, price, spy_ok)
        stop  = calc_stop(price, gap_pct)

        conditions = {
            "catalyst": has_news,
            "volume":   pm_v > 0 and (pm_v / avg_v) >= 0.15 if avg_v > 0 else False,
            "gap":      gap_pct >= 2.0,
            "spy":      spy_ok,
            "price":    5 <= price <= 30
        }

        candidates.append({
            "ticker":   sym,
            "price":    round(price, 2),
            "gap":      round(gap_pct, 2),
            "pmVol":    fmt_vol(pm_v),
            "pmVolX":   pm_vol_x,
            "stop":     stop,
            "score":    score,
            "conditions": conditions,
            "news":     ""
        })

    # Sort by score then gap size
    candidates.sort(key=lambda x: (x["score"], x["gap"]), reverse=True)
    top5 = candidates[:5]

    # Fetch news for top 5 only (saves API calls)
    print("Fetching news headlines...")
    for c in top5:
        news = get_news(c["ticker"])
        c["news"] = news
        # Re-score with news
        has_news = "No news" not in news
        c["conditions"]["catalyst"] = has_news
        c["score"] = score_signal(
            c["gap"], 0, 1,  # vol already scored above
            has_news, c["price"]
        )
        # Adjust score to not double-count volume
        vol_bonus = 1 if c["conditions"]["volume"] else 0
        spy_bonus = 1 if c["conditions"]["spy"] else 0
        gap_bonus = 1 if c["conditions"]["gap"] else 0
        price_bonus = 1 if c["conditions"]["price"] else 0
        c["score"] = (1 if has_news else 0) + vol_bonus + gap_bonus + spy_bonus + price_bonus
        print(f"  {c['ticker']:6} | Gap: +{c['gap']:.1f}% | Score: {c['score']}/5 | {news[:60]}...")

    # Pad to 5 if fewer candidates found
    while len(top5) < 5:
        top5.append({
            "ticker":     "N/A",
            "name":       "No qualifying stock found",
            "price":      0,
            "gap":        0,
            "pmVol":      "—",
            "pmVolX":     0,
            "stop":       0.20,
            "score":      0,
            "conditions": {"catalyst": False, "volume": False, "gap": False, "spy": False, "price": False},
            "news":       "No qualifying pre-market mover found for this slot."
        })

    # Add company names (basic lookup — expand as needed)
    NAMES = {
        "HOOD": "Robinhood Markets",
        "SOFI": "SoFi Technologies",
        "MARA": "Marathon Digital Holdings",
        "RIOT": "Riot Platforms",
        "IONQ": "IonQ Inc.",
        "OPEN": "Opendoor Technologies",
        "CLOV": "Clover Health",
        "SNDL": "SNDL Inc.",
        "TLRY": "Tilray Brands",
        "SIRI": "Sirius XM",
        "CLSK": "CleanSpark Inc.",
        "BITF": "Bitfarms Ltd.",
        "HUT":  "Hut 8 Corp.",
        "SPCE": "Virgin Galactic",
        "NKLA": "Nikola Corporation",
        "ENVX": "Enovix Corporation",
        "WKHS": "Workhorse Group",
        "OCGN": "Ocugen Inc.",
    }

    for c in top5:
        if "name" not in c or not c.get("name"):
            c["name"] = NAMES.get(c["ticker"], c["ticker"])

    # Save to signals.json
    output = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M SGT"),
        "signals": top5
    }

    with open("signals.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nDone. signals.json saved with {len(top5)} signals.")
    print("Upload signals.json to your GitHub repo to update the live bot.")
    print("\nTop signals tonight:")
    for i, c in enumerate(top5, 1):
        print(f"  {i}. {c['ticker']:6} | ${c['price']:.2f} | Gap +{c['gap']:.1f}% | Score {c['score']}/5")


if __name__ == "__main__":
    main()
