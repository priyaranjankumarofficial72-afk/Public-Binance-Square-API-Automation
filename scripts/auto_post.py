import json
import os
import random
import time
import urllib.request

COUNTER_FILE = "counter.txt"

# ============================================================
# TECHNICAL INDICATORS
# ============================================================

def ema(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    val = sum(prices[:period]) / period
    for p in prices[period:]:
        val = p * k + val * (1 - k)
    return val

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = 0, 0
    for i in range(1, period + 1):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi_val = 100 - (100 / (1 + rs))
    for i in range(period + 1, len(prices)):
        diff = prices[i] - prices[i-1]
        gain = diff if diff > 0 else 0
        loss = abs(diff) if diff < 0 else 0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        if avg_loss == 0:
            rsi_val = 100
        else:
            rs = avg_gain / avg_loss
            rsi_val = 100 - (100 / (1 + rs))
    return rsi_val

def macd(prices):
    if len(prices) < 35:
        return None, None, None
    ema12 = ema(prices, 12)
    ema26 = ema(prices, 26)
    if ema12 is None or ema26 is None:
        return None, None, None
    macd_line = ema12 - ema26
    series = []
    for i in range(26, len(prices)):
        e12 = ema(prices[:i+1], 12)
        e26 = ema(prices[:i+1], 26)
        if e12 and e26:
            series.append(e12 - e26)
    if len(series) < 9:
        return macd_line, None, None
    signal_line = ema(series, 9)
    if signal_line is None:
        return macd_line, None, None
    return macd_line, signal_line, macd_line - signal_line

def bollinger(prices, period=20, sd=2):
    if len(prices) < period:
        return None, None, None
    recent = prices[-period:]
    sma = sum(recent) / period
    var = sum((p - sma) ** 2 for p in recent) / period
    std = var ** 0.5
    return sma + sd*std, sma, sma - sd*std

def atr(highs, lows, closes, period=14):
    if len(closes) < period + 1:
        return None
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return None
    val = sum(trs[:period]) / period
    for tr in trs[period:]:
        val = (val * (period - 1) + tr) / period
    return val

# ============================================================
# FETCH DATA
# ============================================================

def fetch_market():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def fetch_news():
    try:
        url = "https://cryptocurrency.cv/api/news?limit=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        return data.get('articles', [])[:5]
    except Exception as e:
        print(f"News fetch failed: {e}")
        return []

def fetch_ohlc(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        closes = [c[4] for c in data]
        highs = [c[2] for c in data]
        lows = [c[3] for c in data]
        return closes, highs, lows
    except Exception as e:
        print(f"OHLC failed for {coin_id}: {e}")
        return None, None, None

# ============================================================
# RANDOM ELEMENTS
# ============================================================

OPENERS_GAINER = [
    "Yo yo yo! 🔥 Look at this rocket!",
    "Hey hey hey! 💪 The bulls are back!",
    "Legends! 👋 Eyes here!",
    "Wassup traders! 🚀 Green candles incoming!",
]

REASONS_GAINER = [
    ["✅ Strong buying volume", "✅ Breaking resistance levels", "✅ Momentum building"],
    ["🚀 Whale accumulation spotted", "🔥 Sentiment flipping bullish", "💪 Support holding firm"],
    ["✅ Volume spike confirmed", "🔥 Social buzz rising", "💪 Trend reversing up"],
]

CLOSERS_GAINER = [
    "Don't chase green candles, fam! 🧠",
    "Stay smart out there! 💎🙌",
    "Manage your risk! 🎯",
]

OPENERS_LOSER = [
    "Ouch fam! 😬 This one is hurting today.",
    "Hey fam! 😐 Rough day for this one.",
    "Yo traders! 👋 Dip alert incoming!",
]

REASONS_LOSER = [
    ["❌ Whales taking profits", "❌ Weak market sentiment", "❌ Broke key support"],
    ["❌ Profit-taking after a run", "❌ General market weakness", "❌ Lost a key level"],
    ["❌ Exchange inflows spiking", "❌ Sentiment turning bearish", "❌ Trendline broken"],
]

CLOSERS_LOSER = [
    "Don't panic sell! 💎🙌",
    "Watch for a bounce! 🔍",
    "Stay patient, fam! 💪",
]

OPENERS_NEWS = [
    "Hey fam! 👋 Big news just dropped!",
    "Legends! 🚨 Breaking story incoming!",
    "Wassup traders! 👀 You need to see this!",
]

CLOSERS_NEWS = [
    "Stay sharp out there! 💎🙌",
    "Watch this one closely! 👀",
    "DYOR always! 🧠",
]

OPENERS_ANALYSIS = [
    "Hey fam! 🤖 Time for my algo read!",
    "Traders! 👋 Let's analyze this one!",
    "Legends! 📊 My indicators just finished!",
]

# ============================================================
# POST BUILDERS
# ============================================================

def build_gainer_post(coin):
    opener = random.choice(OPENERS_GAINER)
    reasons = "\n".join(random.choice(REASONS_GAINER))
    closer = random.choice(CLOSERS_GAINER)
    sym = coin['symbol'].upper()
    chg = coin['price_change_percentage_24h']
    return f"""🚀 **TOP GAINER: ${sym} Up {chg:.1f}%!** 🚀

{opener}

**{coin['name']} is absolutely flying** — up **{chg:.1f}% in 24h!** 📈

Why the pump? 🤔

{reasons}

💰 Current price: **${coin['current_price']:,.4f}**

📊 **Market Impact:** Momentum traders may pile in. Watch for a pullback after the pump.

{closer}

**${sym}**"""

def build_loser_post(coin):
    opener = random.choice(OPENERS_LOSER)
    reasons = "\n".join(random.choice(REASONS_LOSER))
    closer = random.choice(CLOSERS_LOSER)
    sym = coin['symbol'].upper()
    chg = abs(coin['price_change_percentage_24h'])
    return f"""⚠️ **TOP LOSER: ${sym} Down {chg:.1f}%!** ⚠️

{opener}

**{coin['name']} dropped {chg:.1f}%** in 24h. 📉

Why the dump? 🤔

{reasons}

💰 Price: **${coin['current_price']:,.4f}**

📊 **Market Impact:** Weak hands may exit, creating more downside. Watch support closely.

{closer}

**${sym}**"""

def build_news_post(article):
    title = article.get('title', 'Crypto Update')[:80]
    source = article.get('source', 'cryptocurrency.cv')
    opener = random.choice(OPENERS_NEWS)
    closer = random.choice(CLOSERS_NEWS)
    coin_tag = ""
    for c in ["BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX"]:
        if c.lower() in title.lower():
            coin_tag = f"\n\n**${c}**"
            break
    return f"""📰 **NEWS: {title}** 📰

{opener}

📌 Source: {source}

📊 **Market Impact:** Watch for short-term volatility. Sentiment will decide direction.

{closer}{coin_tag}"""

def build_analysis_post(coin, closes, highs, lows):
    sym = coin['symbol'].upper()
    price = coin['current_price']
    change = coin['price_change_percentage_24h']

    e20 = ema(closes, 20) if len(closes) >= 20 else None
    e50 = ema(closes, 50) if len(closes) >= 50 else None
    r14 = rsi(closes, 14) if len(closes) >= 15 else None
    m, s, h = macd(closes)
    bu, bm, bl = bollinger(closes) if len(closes) >= 20 else (None, None, None)
    a = atr(highs, lows, closes, 14)

    score = 0
    reasons = []

    if e20 and e50:
        if e20 > e50:
            score += 1
            reasons.append("📈 EMA20 > EMA50 — bullish trend")
        else:
            score -= 1
            reasons.append("📉 EMA20 < EMA50 — bearish trend")

    if r14 is not None:
        if r14 > 70:
            score -= 1
            reasons.append(f"⚠️ RSI {r14:.1f} — overbought")
        elif r14 < 30:
            score += 1
            reasons.append(f"💎 RSI {r14:.1f} — oversold")
        elif r14 > 50:
            score += 1
            reasons.append(f"✅ RSI {r14:.1f} — bullish")
        else:
            score -= 1
            reasons.append(f"🔻 RSI {r14:.1f} — bearish")

    if m is not None and s is not None:
        if m > s:
            score += 1
            reasons.append(f"🚀 MACD bullish (hist {h:.4f})")
        else:
            score -= 1
            reasons.append(f"📉 MACD bearish (hist {h:.4f})")

    if bu and bl:
        if price > bu:
            score -= 1
            reasons.append("⚠️ Above upper Bollinger Band")
        elif price < bl:
            score += 1
            reasons.append("💎 Below lower Bollinger Band")
        else:
            reasons.append("📊 Inside Bollinger Bands")

    if score >= 3:
        signal = "🟢 **STRONG BUY**"
        direction = "BUY"
        outlook = "Multiple indicators aligned bullish — high conviction."
    elif score >= 1:
        signal = "🟢 **BUY**"
        direction = "BUY"
        outlook = "Mild bullish bias — watch for confirmation."
    elif score <= -3:
        signal = "🔴 **STRONG SELL**"
        direction = "SELL"
        outlook = "Multiple indicators aligned bearish."
    elif score <= -1:
        signal = "🔴 **SELL**"
        direction = "SELL"
        outlook = "Mild bearish bias — reduce exposure."
    else:
        signal = "🟡 **HOLD**"
        direction = "HOLD"
        outlook = "Mixed signals — wait for clarity."

    trade_section = "⏸️ **No trade setup** — wait for clearer signal."
    if direction in ["BUY", "SELL"] and a:
        if direction == "BUY":
            entry = price
            sl_atr = entry - (1.5 * a)
            sl = max(sl_atr, min(lows[-10:]) * 0.99 if len(lows) >= 10 else entry * 0.95)
            risk = entry - sl
            tp1 = entry + risk * 1.5
            tp2 = entry + risk * 2.5
            tp3 = entry + risk * 4.0
        else:
            entry = price
            sl_atr = entry + (1.5 * a)
            sl = min(sl_atr, max(highs[-10:]) * 1.01 if len(highs) >= 10 else entry * 1.05)
            risk = sl - entry
            tp1 = entry - risk * 1.5
            tp2 = entry - risk * 2.5
            tp3 = entry - risk * 4.0

        if risk > 0:
            trade_section = f"""🎯 **Trade Setup:**
📍 Entry: **${entry:,.4f}**
🛑 Stop Loss: **${sl:,.4f}** ({(risk/entry)*100:.1f}% risk)
✅ TP1: **${tp1:,.4f}** (RR 1.5x)
✅ TP2: **${tp2:,.4f}** (RR 2.5x)
✅ TP3: **${tp3:,.4f}** (RR 4.0x)"""

    opener = random.choice(OPENERS_ANALYSIS)
    return f"""🤖 **AI ANALYSIS: ${sym}** 🤖

{opener}

**{coin['name']}** — Technical read:
💰 **Price:** ${price:,.4f}
📊 **24h:** {change:+.1f}%

📐 **Indicators:**
{chr(10).join(reasons)}

{signal}

{trade_section}

💡 **Outlook:** {outlook}

⚠️ *Not financial advice. DYOR. Always use stop loss!*

**${sym}**"""

# ============================================================
# POST TO BINANCE
# ============================================================

def post_to_binance(text, api_key):
    payload = json.dumps({"bodyTextOnly": text}).encode('utf-8')
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
            print("POST SUCCESS:", r.read().decode()[:200])
            return True
    except Exception as e:
        print("POST ERROR:", e)
        if hasattr(e, 'read'):
            print(e.read().decode()[:300])
        return False

# ============================================================
# MAIN
# ============================================================

def main():
    api_key = os.environ.get("BINANCE_KEY")
    if not api_key:
        raise Exception("BINANCE_KEY secret is missing!")

    coins = fetch_market()
    top_gainers = coins[:5]
    top_losers = coins[-5:]

    EXCLUDE = {"tether", "usd-coin", "dai", "first-digital-usd", "ethena-usde",
               "wrapped-bitcoin", "wrapped-steth", "staked-ether", "binance-usd",
               "true-usd", "usds", "paypal-usd", "usd1-wlfi"}

    potential = [c for c in coins if c['id'] not in EXCLUDE
                 and c.get('market_cap', 0) > 100_000_000
                 and c.get('total_volume', 0) > 5_000_000][:80]

    news = fetch_news()
    print(f"Fetched {len(news)} news articles")

    posts = []

    if news:
        posts.append(build_news_post(news[0]))
    else:
        posts.append(build_gainer_post(top_gainers[0]))

    if len(news) > 1:
        posts.append(build_news_post(news[1]))
    else:
        posts.append(build_gainer_post(top_gainers[1]))

    posts.append(build_gainer_post(top_gainers[0]))
    posts.append(build_loser_post(top_losers[-1]))

    # Analysis: try up to 5 random potential coins
    random.shuffle(potential)
    for candidate in potential[:5]:
        print(f"Trying analysis on: {candidate['name']}")
        closes, highs, lows = fetch_ohlc(candidate['id'])
        if closes and len(closes) >= 20:
            analysis = build_analysis_post(candidate, closes, highs, lows)
            posts.append(analysis)
            print(f"✅ Analysis ready for {candidate['name']}")
            break
        time.sleep(1)

    for i, text in enumerate(posts, 1):
        print(f"\n=== Post {i}/{len(posts)} ===")
        print(text[:300] + "...")
        post_to_binance(text, api_key)
        if i < len(posts):
            time.sleep(5)

    print(f"\n✅ All {len(posts)} posts completed!")

if __name__ == "__main__":
    main()
