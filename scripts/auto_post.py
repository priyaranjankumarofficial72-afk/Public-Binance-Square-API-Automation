import json
import os
import random
import time
import urllib.request
import mimetypes
import uuid
import pandas as pd
import mplfinance as mpf

# ==========================================
# CONFIG — FALLBACK TOKENS (used if API fails)
# ==========================================
FALLBACK_SYMBOLS = [
    "BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "TRX", "AVAX", "LINK",
    "DOT", "MATIC", "SHIB", "LTC", "UNI", "ATOM", "NEAR", "APT", "ARB", "OP",
    "INJ", "SUI", "SEI", "TIA", "FIL", "GRT", "AAVE", "MKR", "PEPE", "RNDR",
    "FET", "IMX", "WLD", "JUP", "PYTH", "BONK", "WIF", "FLOKI", "SAND", "MANA"
]
INTERVALS = ["1h", "4h", "1d"]
BINANCE_DATA_API = "https://data-api.binance.vision"

# ==========================================
# FETCH TOP GAINERS & LOSERS
# ==========================================
def fetch_gainers_losers():
    try:
        url = f"{BINANCE_DATA_API}/api/v3/ticker/24hr"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())

        usdt_pairs = [
            t for t in data
            if t['symbol'].endswith('USDT') and float(t.get('quoteVolume', 0)) > 5000000
        ]

        sorted_pairs = sorted(usdt_pairs, key=lambda x: float(x['priceChangePercent']), reverse=True)

        stablecoins = {'USDC', 'FDUSD', 'TUSD', 'BUSD', 'DAI', 'USDP'}
        gainers = [t['symbol'].replace('USDT', '') for t in sorted_pairs[:15]]
        losers = [t['symbol'].replace('USDT', '') for t in sorted_pairs[-15:]]
        gainers = [g for g in gainers if g not in stablecoins]
        losers = [l for l in losers if l not in stablecoins]

        print(f"📈 Top Gainers: {gainers}")
        print(f"📉 Top Losers: {losers}")
        return gainers, losers
    except Exception as e:
        print(f"⚠️ Failed to fetch gainers/losers: {e}")
        return [], []

# ==========================================
# NEW LISTINGS (Manual Fallback)
# ==========================================
def fetch_new_listings():
    new_listings = ["WIF", "BONK", "JUP", "PYTH", "STRK", "DYM", "MANTA", "ALT", "PIXEL", "PORTAL"]
    print(f"🆕 New Listings (manual): {new_listings}")
    return new_listings

# ==========================================
# SMA CALCULATOR
# ==========================================
def calc_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def get_sma_insight(closes):
    sma20 = calc_sma(closes, 20) if len(closes) >= 20 else None
    sma50 = calc_sma(closes, 50) if len(closes) >= 50 else None
    sma200 = calc_sma(closes, 200) if len(closes) >= 200 else None
    price = closes[-1]

    insights = []
    if sma20 and sma50:
        insights.append("SMA20 > SMA50 — bullish crossover 📈" if sma20 > sma50 else "SMA20 < SMA50 — bearish crossover 📉")
    if sma50 and sma200:
        insights.append("Golden cross confirmed 🥇" if sma50 > sma200 else "Death cross active ⚰️")
    if sma20:
        insights.append(f"price above SMA20 (${round(sma20, 4)}) 🟢" if price > sma20 else f"price below SMA20 (${round(sma20, 4)}) 🔴")
    if sma50:
        insights.append(f"holding above SMA50 (${round(sma50, 4)}) 🛡️" if price > sma50 else f"rejected at SMA50 (${round(sma50, 4)}) ⚠️")
    if sma200:
        insights.append(f"above SMA200 (${round(sma200, 4)}) — long-term bullish 🚀" if price > sma200 else f"below SMA200 (${round(sma200, 4)}) — long-term bearish 📉")

    return random.choice(insights) if insights else "watching key levels 👀"

# ==========================================
# RANDOM ZOETOSHI TEXT
# ==========================================
def generate_random_text(symbol, price, support, tp, sl, sma_insight):
    templates = [
        f"${symbol} at crucial support 🛡️\n\n{sma_insight}\n\nlonged at cmp. SL ${sl} 🛑 TP ${tp} 🎯\n\nsmall size. nfa. ${symbol}",
        f"${symbol} ending accumulation ⏳\n\n{sma_insight}\n\nspot buy zone: ${support} - ${round(price, 2)} 🟢\n\ntargets: ${tp} then ${round(tp*1.1, 2)} 🎯\n\nnfa. ${symbol}",
        f"Looking at the chart, ${symbol} is setting up 🎯\n\n{sma_insight}\n\nSL ${sl} 🛑 TP ${tp} 🚀\n\nsmall size. nfa.",
        f"Noticing something on ${symbol} 👀\n\n{sma_insight}\n\nentry around ${round(price, 2)} 🎯\n\nSL ${sl} 🛑 TP ${tp} 🚀\n\nnfa.",
        f"Watching ${symbol} closely 📊\n\n{sma_insight}\n\ni am long. SL ${sl} 🛑 TP ${tp} 🎯\n\nnfa.",
        f"Accumulation phase almost over ⏳\n\n{sma_insight}\n\nspot buy zone: ${support} - ${round(price, 2)} 🟢\n\ntargets: ${tp} 🎯\n\nnfa. ${symbol}",
        f"Giga pump incoming 🚀\n\n{sma_insight}\n\nexpecting dip to ${support} first 📉\n\nthen breakout to ${tp} 🎯\n\nnfa. ${symbol}",
        f"Higher lows forming on ${symbol} ✅\n\n{sma_insight}\n\nbuy zone: ${support} - ${round(price, 2)} 🟢\n\ntarget: ${tp} 🎯\n\nnfa.",
        f"Bullish structure intact on ${symbol} 📈\n\n{sma_insight}\n\nlonged at cmp. SL ${sl} 🛑 TP ${tp} 🎯\n\nuse small size. nfa.",
        f"Back at demand zone 💎\n\n${symbol} — {sma_insight}\n\nspot buy: ${support} - ${round(price, 2)} 🟢\n\ntarget: ${tp} 🎯\n\nnfa.",
        f"Setting up nicely 🎯\n\n${symbol} {sma_insight}\n\nbreakout soon → ${tp} 🚀\n\nSL ${sl} 🛑\n\nnfa.",
        f"This one on my radar 👀\n\n${symbol} at key support 🛡️\n\n{sma_insight}\n\nif it holds → ${tp} next 🎯\n\nnfa.",
        f"Primed for a move 🎯\n\nentry on ${symbol}: ${round(price, 2)} 🟢\n\n{sma_insight}\n\nSL ${sl} 🛑 TP ${tp} 🚀\n\nnfa.",
        f"About to explode 💥\n\n${symbol} {sma_insight}\n\nSL ${sl} 🛑 TP ${tp} 🎯\n\nnfa.",
        f"Key level being tested 🚧\n\n${symbol} {sma_insight}\n\nif we break → ${tp} 🚀\n\nSL ${sl} 🛑\n\nnfa."
    ]
    return random.choice(templates)

# ==========================================
# FETCH KLINES
# ==========================================
def fetch_klines(symbol, interval):
    url = f"{BINANCE_DATA_API}/api/v3/klines?symbol={symbol}USDT&interval={interval}&limit=210"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    df = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
    ])
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    df = df[['open', 'high', 'low', 'close', 'volume']].astype(float)
    return df

# ==========================================
# CHART GENERATOR
# ==========================================
def generate_chart(symbol, support, tp, sl, interval):
    try:
        df = fetch_klines(symbol, interval)

        styles = ['nightclouds', 'yahoo', 'charles', 'binance', 'blueskies', 'starsandstripes']
        chosen_style = random.choice(styles)

        my_style = mpf.make_mpf_style(
            base_mpf_style=chosen_style,
            marketcolors=mpf.make_marketcolors(up='#00ff00', down='#ff0000', inherit=True),
            gridstyle='--',
            gridcolor='#333333'
        )

        hlines_config = dict(
            hlines=[support, tp, sl],
            colors=['green', 'blue', 'red'],
            linestyle='--',
            linewidths=1.5,
            alpha=0.8
        )

        sma20 = df['close'].rolling(20).mean()
        sma50 = df['close'].rolling(50).mean()

        adds = [
            mpf.make_addplot(sma20, color='yellow', width=1, label='SMA20'),
            mpf.make_addplot(sma50, color='orange', width=1, label='SMA50'),
        ]

        filename = f"{symbol}_chart_{random.randint(1, 9999)}.png"
        mpf.plot(
            df, type='candle', style=my_style,
            title=f"\n{symbol}/USDT - {interval}",
            ylabel='Price', volume=True,
            hlines=hlines_config,
            addplot=adds,
            savefig=dict(fname=filename, dpi=100, bbox_inches='tight')
        )
        print(f"📈 Chart saved: {filename} (style: {chosen_style}, interval: {interval})")
        return filename
    except Exception as e:
        print(f"❌ Chart failed for {symbol}: {e}")
        return None

# ==========================================
# BINANCE IMAGE UPLOAD
# ==========================================
def upload_image(image_path, api_key):
    boundary = uuid.uuid4().hex
    with open(image_path, 'rb') as f:
        file_data = f.read()

    filename = os.path.basename(image_path)
    content_type = mimetypes.guess_type(filename)[0] or 'image/png'

    body = []
    body.append(f'--{boundary}'.encode())
    body.append(f'Content-Disposition: form-data; name="file"; filename="{filename}"'.encode())
    body.append(f'Content-Type: {content_type}'.encode())
    body.append(b'')
    body.append(file_data)
    body.append(f'--{boundary}--'.encode())
    body.append(b'')
    payload = b'\r\n'.join(body)

    req = urllib.request.Request(
        'https://www.binance.com/bapi/composite/v1/public/pgc/openApi/image/upload',
        data=payload,
        headers={
            'X-Square-OpenAPI-Key': api_key,
            'Content-Type': f'multipart/form-data; boundary={boundary}',
            'clienttype': 'binanceSkill'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            res = json.loads(r.read())
            url = res.get('data', {}).get('url')
            print(f"✅ Image uploaded: {url}")
            return url
    except Exception as e:
        print("❌ UPLOAD ERROR: " + str(e))
        if hasattr(e, 'read'):
            print(e.read().decode()[:300])
        return None

# ==========================================
# BINANCE POST
# ==========================================
def post_to_binance(text, image_url, api_key):
    payload = json.dumps({
        "bodyTextOnly": text,
        "imageUrl": image_url
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://www.binance.com/bapi/composite/v1/public/pgc/openApi/content/add',
        data=payload,
        headers={
            'X-Square-OpenAPI-Key': api_key,
            'Content-Type': 'application/json',
            'clienttype': 'binanceSkill'
        },
        method='POST'
    )
    try:
        with urllib.request.urlopen(req) as r:
            print("🚀 POST SUCCESS: " + r.read().decode()[:200])
            return True
    except Exception as e:
        print("❌ POST ERROR: " + str(e))
        if hasattr(e, 'read'):
            print(e.read().decode()[:300])
        return False

# ==========================================
# MAIN
# ==========================================
def main():
    api_key = os.environ.get("BINANCE_KEY")
    if not api_key:
        raise Exception("BINANCE_KEY secret is missing")

    print("--- Starting Zoetoshi Automation ---")

    gainers, losers = fetch_gainers_losers()
    new_listings = fetch_new_listings()

    token_pool = list(set(gainers + losers + new_listings + FALLBACK_SYMBOLS))
    token_pool = [t for t in token_pool if t.isalpha() and 2 <= len(t) <= 10]

    print(f"🎯 Token pool size: {len(token_pool)}")
    used_tokens = []

    for i in range(2):
        available = [s for s in token_pool if s not in used_tokens]
        if not available:
            available = FALLBACK_SYMBOLS
        symbol = random.choice(available)
        used_tokens.append(symbol)

        interval = random.choice(INTERVALS)

        try:
            url = f"{BINANCE_DATA_API}/api/v3/ticker/price?symbol={symbol}USDT"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r:
                price = float(json.loads(r.read())['price'])
        except Exception as e:
            print(f"⚠️ Skipping {symbol}: {e}")
            continue

        try:
            df = fetch_klines(symbol, interval)
            closes = df['close'].tolist()
            sma_insight = get_sma_insight(closes)
        except Exception:
            sma_insight = "watching key levels 👀"

        support = round(price * random.uniform(0.88, 0.96), 4)
        tp = round(price * random.uniform(1.08, 1.30), 4)
        sl = round(support * random.uniform(0.96, 0.99), 4)

        print(f"\n--- Post {i+1}/2 for ${symbol} ({interval}) ---")

        text = generate_random_text(symbol, price, support, tp, sl, sma_insight)
        print(text)

        chart = generate_chart(symbol, support, tp, sl, interval)

        if chart:
            image_url = upload_image(chart, api_key)
            if image_url:
                post_to_binance(text, image_url, api_key)

        if i < 1:
            time.sleep(10)

if __name__ == "__main__":
    main()
