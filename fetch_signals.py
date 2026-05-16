"""
ORB Signal Bot - Pre-market data fetcher
Run before 9:30 PM SGT (1:30 PM UTC)

Requires only: pip install requests
"""

import requests
import json
import os
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────
# FILL IN YOUR API KEYS BELOW
# Alpaca free key:  https://alpaca.markets  (paper account)
# NewsAPI free key: https://newsapi.org
# ─────────────────────────────────────────────────────────────
ALPACA_KEY    = os.environ.get("ALPACA_KEY",    "PKWQRUSIPZOIFHRPY2GLLIXL4A")
ALPACA_SECRET = os.environ.get("ALPACA_SECRET", "EpnXC8QDXiKhhi7kjfkxTf6mtzEHLnBYUrXM5rcJatgV")
NEWS_API_KEY  = os.environ.get("NEWS_API_KEY",  "87715ba23be74830bf0007538c7e40ae")
# ─────────────────────────────────────────────────────────────

ALPACA_DATA = "https://data.alpaca.markets/v2"

HEADERS = {
    "APCA-API-KEY-ID": ALPACA_KEY,
    "APCA-API-SECRET-KEY": ALPACA_SECRET,
}

WATCHLIST = [
    "HOOD", "SOFI", "MARA", "RIOT", "IONQ",
    "OPEN", "TLRY", "SIRI", "CLSK", "BITF",
    "HUT",  "ENVX", "WKHS", "OCGN", "PERI",
    "SPCE", "NKLA", "CLOV", "PSFE", "ATER",
    "PROG", "GFAI", "IDEX", "FFIE", "BBIG"
]

NAMES = {
    "HOOD": "Robinhood Markets",
    "SOFI": "SoFi Technologies",
    "MARA": "Marathon Digital Holdings",
    "RIOT": "Riot Platforms",
    "IONQ": "IonQ Inc.",
    "OPEN": "Opendoor Technologies",
    "TLRY": "Tilray Brands",
    "SIRI": "Sirius XM",
    "CLSK": "CleanSpark Inc.",
    "BITF": "Bitfarms Ltd.",
    "HUT":  "Hut 8 Corp.",
    "ENVX": "Enovix Corporation",
    "WKHS": "Workhorse Group",
    "OCGN": "Ocugen Inc.",
    "PERI": "Perion Network",
    "SPCE": "Virgin Galactic",
    "NKLA": "Nikola Corporation",
    "CLOV": "Clover Health",
    "PSFE": "Paysafe Ltd.",
    "ATER": "Aterian Inc.",
    "PROG": "Progenity Inc.",
    "GFAI": "Guardforce AI",
    "IDEX": "Ideanomics",
    "FFIE": "Faraday Future",
    "BBIG": "Vinco Ventures",
}


def fetch_bars(symbols, timeframe, limit):
    result = {}
    chunk_size = 10
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i+chunk_size]
        try:
            r = requests.get(
                f"{ALPACA_DATA}/stocks/bars",
                headers=HEADERS,
                params={
                    "symbols": ",".join(chunk),
                    "timeframe": timeframe,
                    "limit": limit,
                    "adjustment": "raw",
                    "feed": "iex"
                },
                timeout=12
            )
            if r.status_code == 200:
                result.update(r.json().get("bars", {}))
            else:
                print(f"  Alpaca {r.status_code}: {r.text[:80]}")
        except Exception as e:
            print(f"  Request error: {e}")
    return result


def fetch_latest_trades(symbols):
    result = {}
    chunk_size = 10
    for i in range(0, len(symbols), chunk_size):
        chunk = symbols[i:i+chunk_size]
        try:
            r = requests.get(
                f"{ALPACA_DATA}/stocks/trades/latest",
                headers=HEADERS,
                params={"symbols": ",".join(chunk), "feed": "iex"},
                timeout=12
            )
            if r.status_code == 200:
                for sym, trade in r.json().get("trades", {}).items():
                    result[sym] = trade.get("p", 0)
        except Exception as e:
            print(f"  Trade fetch error: {e}")
    return result


def get_news(ticker):
    if NEWS_API_KEY == "your_newsapi_key_here":
        return "Add your NewsAPI key to see live headlines."
    try:
        r = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": ticker,
                "sortBy": "publishedAt",
                "pageSize": 1,
                "language": "en",
                "apiKey": NEWS_API_KEY
            },
            timeout=8
        )
        if r.status_code == 200:
            articles = r.json().get("articles", [])
            if articles:
                a = articles[0]
                title = a.get("title", "")
                source = a.get("source", {}).get("name", "")
                clean = title.split(" - ")[0].strip()
                return (clean + " — " + source) if source else clean
    except Exception as e:
        print(f"  News error for {ticker}: {e}")
    return "No headline found."


def calc_stop(price, gap_pct):
    pct = max(0.015, min(0.035, (gap_pct / 100) * 0.55))
    stop = round(price * pct, 2)
    return max(0.08, stop)


def fmt_vol(v):
    if v >= 1000000:
        return f"{v/1000000:.1f}M"
    elif v >= 1000:
        return f"{v/1000:.0f}K"
    return str(int(v))


def score_conditions(gap_pct, pm_vol_x, has_news, price, spy_ok):
    conds = {
        "catalyst": has_news,
        "volume":   pm_vol_x >= 0.5,
        "gap":      gap_pct >= 2.0,
        "spy":      spy_ok,
        "price":    5 <= price <= 30
    }
    return conds, sum(conds.values())


def save_signals(signals, note=""):
    output = {
        "generated_at": datetime.now().strftime("%d %b %Y %H:%M") + " SGT" + note,
        "signals": signals
    }
    with open("signals.json", "w") as f:
        json.dump(output, f, indent=2)
    print("signals.json saved.")


SAMPLE_SIGNALS = [
    {
        "ticker": "HOOD", "name": "Robinhood Markets",
        "price": 18.30, "gap": 4.1, "pmVol": "7.8M", "pmVolX": 1.9, "stop": 0.35, "score": 5,
        "conditions": {"catalyst": True, "volume": True, "gap": True, "spy": True, "price": True},
        "news": "SAMPLE — Add your API keys to fetch_signals.py for live data."
    },
    {
        "ticker": "SOFI", "name": "SoFi Technologies",
        "price": 9.20, "gap": 3.6, "pmVol": "5.2M", "pmVolX": 1.6, "stop": 0.25, "score": 5,
        "conditions": {"catalyst": True, "volume": True, "gap": True, "spy": True, "price": True},
        "news": "SAMPLE — Add your API keys to fetch_signals.py for live data."
    },
    {
        "ticker": "MARA", "name": "Marathon Digital Holdings",
        "price": 22.10, "gap": 3.2, "pmVol": "6.1M", "pmVolX": 2.1, "stop": 0.45, "score": 4,
        "conditions": {"catalyst": True, "volume": True, "gap": True, "spy": True, "price": True},
        "news": "SAMPLE — Add your API keys to fetch_signals.py for live data."
    },
    {
        "ticker": "IONQ", "name": "IonQ Inc.",
        "price": 14.80, "gap": 2.4, "pmVol": "3.1M", "pmVolX": 1.5, "stop": 0.30, "score": 3,
        "conditions": {"catalyst": True, "volume": True, "gap": False, "spy": True, "price": True},
        "news": "SAMPLE — Add your API keys to fetch_signals.py for live data."
    },
    {
        "ticker": "OPEN", "name": "Opendoor Technologies",
        "price": 2.85, "gap": 2.1, "pmVol": "4.8M", "pmVolX": 1.3, "stop": 0.12, "score": 2,
        "conditions": {"catalyst": True, "volume": False, "gap": False, "spy": True, "price": True},
        "news": "SAMPLE — Add your API keys to fetch_signals.py for live data."
    }
]


def main():
    print("=" * 50)
    print("ORB Signal Bot")
    print(datetime.now().strftime("%Y-%m-%d %H:%M"))
    print("=" * 50)

    if ALPACA_KEY == "your_alpaca_key_here":
        print("\nNo API key found. Writing sample data.")
        save_signals(SAMPLE_SIGNALS, " (sample)")
        return

    print(f"\nScanning {len(WATCHLIST)} symbols...")

    print("Previous closes...")
    daily = fetch_bars(WATCHLIST, "1Day", 2)
    prev_closes = {}
    for sym, bars in daily.items():
        if bars:
            prev_closes[sym] = bars[-1]["c"]

    print("Pre-market prices...")
    pm_prices = fetch_latest_trades(WATCHLIST)

    print("Intraday volume...")
    intraday = fetch_bars(WATCHLIST, "1Min", 200)
    pm_volumes = {}
    for sym, bars in intraday.items():
        pm_volumes[sym] = sum(b.get("v", 0) for b in bars)

    print("Average volumes...")
    hist = fetch_bars(WATCHLIST, "1Day", 20)
    avg_volumes = {}
    for sym, bars in hist.items():
        if bars:
            avg_volumes[sym] = sum(b.get("v", 0) for b in bars) / len(bars)

    candidates = []
    for sym in WATCHLIST:
        prev  = prev_closes.get(sym, 0)
        price = pm_prices.get(sym, 0)
        pm_v  = pm_volumes.get(sym, 0)
        avg_v = avg_volumes.get(sym, 1)

        if prev <= 0 or price <= 0:
            continue

        gap_pct  = ((price - prev) / prev) * 100
        pm_vol_x = round(pm_v / avg_v, 1) if avg_v > 0 else 0

        if gap_pct < 1.5 or not (2 <= price <= 35):
            continue

        stop = calc_stop(price, gap_pct)
        conds, score = score_conditions(gap_pct, pm_vol_x, False, price, True)

        candidates.append({
            "ticker":     sym,
            "name":       NAMES.get(sym, sym),
            "price":      round(price, 2),
            "gap":        round(gap_pct, 2),
            "pmVol":      fmt_vol(pm_v),
            "pmVolX":     pm_vol_x,
            "stop":       stop,
            "score":      score,
            "conditions": conds,
            "news":       ""
        })

    candidates.sort(key=lambda x: (x["score"], x["gap"]), reverse=True)
    top5 = candidates[:5]

    if not top5:
        print("\nNo movers found. Using sample data.")
        save_signals(SAMPLE_SIGNALS, " (no movers found)")
        return

    print("\nNews headlines...")
    for c in top5:
        news = get_news(c["ticker"])
        c["news"] = news
        has_news = "No headline" not in news and "Add your" not in news
        conds, score = score_conditions(c["gap"], c["pmVolX"], has_news, c["price"], True)
        c["conditions"] = conds
        c["score"] = score
        print(f"  {c['ticker']:6} ${c['price']:.2f}  +{c['gap']:.1f}%  score {c['score']}/5")

    while len(top5) < 5:
        top5.append({
            "ticker": "N/A", "name": "No qualifying stock",
            "price": 0, "gap": 0, "pmVol": "N/A", "pmVolX": 0,
            "stop": 0.20, "score": 0,
            "conditions": {"catalyst": False, "volume": False,
                           "gap": False, "spy": False, "price": False},
            "news": "No qualifying pre-market mover for this slot."
        })

    save_signals(top5)

    print("\nTop signals tonight:")
    for i, c in enumerate(top5, 1):
        if c["ticker"] not in ("N/A", "—"):
            print(f"  {i}. {c['ticker']:6} ${c['price']:.2f}  gap +{c['gap']:.1f}%  score {c['score']}/5")
    print("=" * 50)


if __name__ == "__main__":
    main()
