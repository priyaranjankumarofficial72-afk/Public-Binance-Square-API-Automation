import json
import os
import random
import time
import urllib.request

COUNTER_FILE = "counter.txt"

BINANCE_TIER_A = {
    "bitcoin", "ethereum", "binancecoin", "solana", "ripple", "cardano",
    "dogecoin", "tron", "avalanche-2", "chainlink", "polkadot", "matic-network",
    "shiba-inu", "litecoin", "uniswap", "stellar", "cosmos", "near",
    "aptos", "arbitrum", "optimism", "injective-protocol", "sui", "sei-network",
    "celestia", "filecoin", "the-graph", "aave", "maker", "pepe"
}

BINANCE_TIER_B = BINANCE_TIER_A | {
    "render-token", "fetch-ai", "immutable-x", "worldcoin-wld",
    "jupiter-exchange-solana", "pyth-network", "bonk", "dogwifcoin",
    "floki", "the-sandbox", "decentraland", "axie-infinity", "gala",
    "enjincoin", "chiliz", "curve-dao-token", "compound-governance-token",
    "synthetix-network-token", "pancakeswap-token", "lido-dao", "rocket-pool",
    "frax-share", "convex-finance", "pax-gold", "tether-gold", "havven",
    "dydx-chain", "gmx", "loopring", "uma", "band-protocol", "ankr",
    "ocean-protocol", "numeraire", "balancer", "storj", "ravencoin",
    "horizen", "wax", "iostoken", "kucoin-shares", "bitcoin-cash",
    "bitcoin-cash-sv", "ethereum-classic", "zcash", "dash", "monero",
    "neo", "ontology", "qtum", "waves", "iota", "algorand", "flow",
    "mina-protocol", "klay-token", "osmosis", "kava", "celo", "cronos",
    "fantom", "harmony", "zilliqa", "icp", "kaspa", "jito-governance-token",
    "ethena", "pendle", "ondo-finance", "stargate-finance"
}

CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain", "defi",
    "nft", "altcoin", "token", "coin", "binance", "coinbase", "solana",
    "sol", "xrp", "ripple", "cardano", "ada", "dogecoin", "doge", "shiba",
    "polygon", "matic", "avalanche", "avax", "chainlink", "link", "polkadot",
    "dot", "uniswap", "uni", "tron", "trx", "litecoin", "ltc", "pepe",
    "memecoin", "stablecoin", "usdt", "usdc", "exchange", "wallet",
    "mining", "halving", "whale", "bull", "bear", "market", "trading",
    "sec", "etf", "regulation", "web3", "layer", "l2", "rollup", "dex",
    "cex", "staking", "yield", "airdrop", "mainnet", "testnet", "fork"
]

NON_CRYPTO_KEYWORDS = [
    "stock", "nasdaq", "s&p", "dow jones", "forex", "oil", "gold price",
    "real estate", "mortgage", "inflation report", "fed chair", "earnings",
    "sports", "football", "basketball", "soccer", "movie", "celebrity",
    "weather", "politics", "election", "war"
]

VIRAL_KEYWORDS = [
    "breaking", "surge", "crash", "record", "hack", "etf", "sec", "halving",
    "all-time", "ath", "dump", "pump", "skyrocket", "plunge", "soar", "rally",
    "explode", "crashes", "announces", "approves", "rejects", "bans", "legal"
]


def is_crypto_news(title):
    t = title.lower()
    if any(k in t for k in NON_CRYPTO_KEYWORDS):
        return False
    return any(k in t for k in CRYPTO_KEYWORDS)


def is_viral(title):
    t = title.lower()
    return any(k in t for k in VIRAL_KEYWORDS)


def extract_coin_from_title(title):
    coin_map = {
        "bitcoin": "BTC", "btc": "BTC", "ethereum": "ETH", "eth": "ETH",
        "solana": "SOL", "sol": "SOL", "xrp": "XRP", "ripple": "XRP",
        "binance": "BNB", "bnb": "BNB", "dogecoin": "DOGE", "doge": "DOGE",
        "cardano": "ADA", "ada": "ADA", "avalanche": "AVAX", "avax": "AVAX",
        "chainlink": "LINK", "link": "LINK", "polkadot": "DOT", "dot": "DOT",
        "polygon": "MATIC", "matic": "MATIC", "shiba": "SHIB", "shib": "SHIB",
        "litecoin": "LTC", "ltc": "LTC", "uniswap": "UNI", "uni": "UNI",
        "tron": "TRX", "trx": "TRX", "pepe": "PEPE"
    }
    t = title.lower()
    for keyword, symbol in coin_map.items():
        if keyword in t:
            return symbol
    return None


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
    e12 = ema(prices, 12)
    e26 = ema(prices, 26)
    if e12 is None or e26 is None:
        return None, None, None
    macd_line = e12 - e26
    series = []
    for i in range(26, len(prices)):
        a = ema(prices[:i+1], 12)
        b = ema(prices[:i+1], 26)
        if a and b:
            series.append(a - b)
    if len(series) < 9:
        return macd_line, None, None
    sig = ema(series, 9)
    if sig is None:
        return macd_line, None, None
    return macd_line, sig, macd_line - sig


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
        trs.append(max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1])))
    if len(trs) < period:
        return None
    val = sum(trs[:period]) / period
    for tr in trs[period:]:
        val = (val * (period - 1) + tr) / period
    return val

def fetch_market():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def fetch_breaking_news():
    articles = []
    try:
        url = "https://cryptocurrency.cv/api/breaking"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        raw = data.get('articles', data) if isinstance(data, dict) else data
        articles = [a for a in raw if isinstance(a, dict) and is_crypto_news(a.get('title', ''))]
    except Exception as e:
        print(f"Breaking news failed: {e}")
    if len(articles) < 2:
        try:
            url = "https://cryptocurrency.cv/api/news?limit=40"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as r:
                data = json.loads(r.read())
            raw = data.get('articles', []) if isinstance(data, dict) else data
            more = [a for a in raw if isinstance(a, dict) and is_crypto_news(a.get('title', ''))]
            articles.extend(more)
        except Exception as e:
            print(f"News fetch failed: {e}")
    articles.sort(key=lambda a: is_viral(a.get('title', '')), reverse=True)
    return articles[:10]


def fetch_binance_trending():
    try:
        url = "https://www.binance.com/bapi/composite/v1/public/composite/hotTopic/list"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        topics = data.get('data', [])
        return [t.get('topic', '') for t in topics[:5] if t.get('topic')]
    except Exception as e:
        print(f"Trending fetch failed: {e}")
        return []


def fetch_ohlc(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc?vs_currency=usd&days=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        return [c[4] for c in data], [c[2] for c in data], [c[3] for c in data]
    except Exception:
        return None, None, None


OPENERS_GAINER = [
    "Yo yo yo! Look at this rocket!",
    "Hey hey hey! The bulls are back!",
    "Legends! Eyes here!",
    "Wassup traders! Green candles incoming!"
]

REASONS_GAINER = [
    ["Strong buying volume", "Breaking resistance levels", "Momentum building"],
    ["Whale accumulation spotted", "Sentiment flipping bullish", "Support holding firm"],
    ["Volume spike confirmed", "Social buzz rising", "Trend reversing up"]
]

CLOSERS_GAINER = ["Don't chase green candles, fam!", "Stay smart out there!", "Manage your risk!"]

OPENERS_LOSER = [
    "Ouch fam! This one is hurting today.",
    "Hey fam! Rough day for this one.",
    "Yo traders! Dip alert incoming!"
]

REASONS_LOSER = [
    ["Whales taking profits", "Weak market sentiment", "Broke key support"],
    ["Profit-taking after a run", "General market weakness", "Lost a key level"],
    ["Exchange inflows spiking", "Sentiment turning bearish", "Trendline broken"]
]

CLOSERS_LOSER = ["Don't panic sell!", "Watch for a bounce!", "Stay patient, fam!"]

OPENERS_ANALYSIS = [
    "Hey fam! Time for my algo read!",
    "Traders! Let's analyze this one!",
    "Legends! My indicators just finished!"
]


def build_gainer_post(coin):
    opener = random.choice(OPENERS_GAINER)
    reasons = "\n".join(random.choice(REASONS_GAINER))
    closer = random.choice(CLOSERS_GAINER)
    sym = coin['symbol'].upper()
    chg = coin['price_change_percentage_24h']
    return f"TOP GAINER: ${sym} Up {chg:.1f}%\n\n{opener}\n\n{coin['name']} is flying - up {chg:.1f}% in 24h!\n\nWhy the pump?\n\n{reasons}\n\nCurrent price: ${coin['current_price']:,.4f}\n\nMarket Impact: Momentum traders may pile in. Watch for a pullback.\n\n{closer}\n\n${sym}"


def build_loser_post(coin):
    opener = random.choice(OPENERS_LOSER)
    reasons = "\n".join(random.choice(REASONS_LOSER))
    closer = random.choice(CLOSERS_LOSER)
    sym = coin['symbol'].upper()
    chg = abs(coin['price_change_percentage_24h'])
    return f"TOP LOSER: ${sym} Down {chg:.1f}%\n\n{opener}\n\n{coin['name']} dropped {chg:.1f}% in 24h.\n\nWhy the dump?\n\n{reasons}\n\nPrice: ${coin['current_price']:,.4f}\n\nMarket Impact: Weak hands may exit. Watch support closely.\n\n{closer}\n\n${sym}"


def build_news_post(article, used_designs):
    title = article.get('title', '')
    coin = extract_coin_from_title(title) or "GENERIC"
    if coin == "BTC":
        templates = ["BTC ALERT - Something's Moving\n\nHey fam! Big money is shifting right now.\n\nWhat this means:\n- Volatility incoming\n- Watch key levels\n- Stay alert\n\nDYOR\n\n$BTC",
                     "BITCOIN - MOMENTUM BUILDING\n\nLegends! BTC in the spotlight today.\n\n- Sentiment shifting\n- Traders positioning\n- Watch altcoins\n\nStay sharp!\n\n$BTC"]
    elif coin == "ETH":
        templates = ["ETH MOVES - EYES HERE\n\nEthereum is making headlines.\n\n- Volatility up\n- Watch support\n- Follow-through matters\n\n$ETH",
                     "ETHEREUM ALERT\n\nSomething's stirring with ETH.\n\n- Big players active\n- Sentiment shifting\n- Position carefully\n\n$ETH"]
    elif coin == "SOL":
        templates = ["SOLANA BREWING\n\nSolana is trending hard.\n\n- Network spiking\n- Traders piling in\n- Volatility incoming\n\n$SOL",
                     "SOL ALERT - HOT TOPIC\n\nSOL is talk of the town.\n\n- Sentiment strong\n- Volume picking up\n- Stay alert\n\n$SOL"]
    else:
        templates = ["CRYPTO MARKET - BIG MOVES INCOMING\n\nBig things brewing today.\n\n- Volatility on horizon\n- Sentiment shifting\n- Watch majors\n\nDYOR",
                     "MARKET ALERT - HEADS UP\n\nSomething significant is happening.\n\n- Big moves possible\n- Watch volume\n- Position smart",
                     "CRYPTO FLASH\n\nCrypto is buzzing today.\n\n- Sharp moves\n- Sentiment shifts\n- Follow-through\n\nDYOR"]
    available = [t for t in templates if t not in used_designs]
    if not available:
        available = templates
    design = random.choice(available)
    used_designs.append(design)
    return design


def build_trending_post(tier_a, exclude=None):
    live_topics = fetch_binance_trending()
    print(f"Live trending topics: {live_topics}")
    if not live_topics:
        live_topics = ["Bitcoin", "Ethereum", "CryptoMarket", "Altcoins", "DeFi"]
    hashtags = " ".join([f"#{t.replace(' ', '')}" for t in live_topics[:5]])
    headline = live_topics[0]
    templates = [
        f"BINANCE TRENDING NOW\n\nHere's what's hot on Binance Square:\n\n{hashtags}\n\n- Sentiment active\n- Volume picking up\n- Traders positioning\n\n#Binance #Crypto",
        f"HOT ON BINANCE SQUARE\n\nWhat's trending today:\n\n{hashtags}\n\n- Attention focused here\n- Big players active\n- Volatility incoming\n\n#BinanceSquare #Crypto",
        f"TRENDING: {headline}\n\nThe crypto world is buzzing.\n\n{hashtags}\n\n- Momentum building\n- Watch majors\n- Stay informed\n\n#Binance #Crypto",
        f"WHAT'S TRENDING ON BINANCE\n\n{hashtags}\n\n- Volume spiking\n- Sentiment active\n- Watch follow-through\n\n#Binance #Crypto",
        f"MARKET BUZZ - BINANCE SQUARE\n\n{hashtags}\n\n- Sharp moves possible\n- Sentiment shifting\n- Position carefully\n\n#Crypto #BinanceSquare"
    ]
    available = [t for t in templates if t != exclude]
    if not available:
        available = templates
    return random.choice(available)


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
            reasons.append("EMA20 > EMA50 - bullish")
        else:
            score -= 1
            reasons.append("EMA20 < EMA50 - bearish")
    if r14 is not None:
        if r14 > 70:
            score -= 1
            reasons.append(f"RSI {r14:.1f} - overbought")
        elif r14 < 30:
            score += 1
            reasons.append(f"RSI {r14:.1f} - oversold")
        elif r14 > 50:
            score += 1
            reasons.append(f"RSI {r14:.1f} - bullish")
        else:
            score -= 1
            reasons.append(f"RSI {r14:.1f} - bearish")
    if m is not None and s is not None:
        if m > s:
            score += 1
            reasons.append(f"MACD bullish (hist {h:.4f})")
        else:
            score -= 1
            reasons.append(f"MACD bearish (hist {h:.4f})")
    if bu and bl:
        if price > bu:
            score -= 1
            reasons.append("Above upper Bollinger Band")
        elif price < bl:
            score += 1
            reasons.append("Below lower Bollinger Band")
        else:
            reasons.append("Inside Bollinger Bands")
    if score >= 3:
        signal = "STRONG BUY"
        direction = "BUY"
        outlook = "High-conviction bullish setup."
    elif score >= 1:
        signal = "BUY"
        direction = "BUY"
        outlook = "Mild bullish bias."
    elif score <= -3:
        signal = "STRONG SELL"
        direction = "SELL"
        outlook = "High-conviction bearish setup."
    elif score <= -1:
        signal = "SELL"
        direction = "SELL"
        outlook = "Mild bearish bias."
    else:
        signal = "HOLD"
        direction = "HOLD"
        outlook = "Mixed signals - wait."
    trade_section = "No trade setup - wait."
    if direction in ["BUY", "SELL"] and a:
        if direction == "BUY":
            entry = price
            sl = max(entry - 1.5*a, min(lows[-10:]) * 0.99 if len(lows) >= 10 else entry * 0.95)
            risk = entry - sl
            tp1, tp2, tp3 = entry + risk*1.5, entry + risk*2.5, entry + risk*4.0
        else:
            entry = price
            sl = min(entry + 1.5*a, max(highs[-10:]) * 1.01 if len(highs) >= 10 else entry * 1.05)
            risk = sl - entry
            tp1, tp2, tp3 = entry - risk*1.5, entry - risk*2.5, entry - risk*4.0
        if risk > 0:
            trade_section = f"Trade Setup:\nEntry: ${entry:,.4f}\nStop Loss: ${sl:,.4f} ({(risk/entry)*100:.1f}% risk)\nTP1: ${tp1:,.4f} (RR 1.5x)\nTP2: ${tp2:,.4f} (RR 2.5x)\nTP3: ${tp3:,.4f} (RR 4.0x)"
    opener = random.choice(OPENERS_ANALYSIS)
    return f"AI ANALYSIS: ${sym}\n\n{opener}\n\n{coin['name']}:\nPrice: ${price:,.4f}\n24h: {change:+.1f}%\n\nIndicators:\n{chr(10).join(reasons)}\n\nSignal: {signal}\n\n{trade_section}\n\nOutlook: {outlook}\n\nNFA. DYOR. Use stop loss!\n\n${sym}"


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


def main():
    api_key = os.environ.get("BINANCE_KEY")
    if not api_key:
        raise Exception("BINANCE_KEY secret is missing!")
    coins = fetch_market()
    tier_a = [c for c in coins if c['id'] in BINANCE_TIER_A and c.get('price_change_percentage_24h') is not None]
    tier_b = [c for c in coins if c['id'] in BINANCE_TIER_B and c.get('price_change_percentage_24h') is not None]
    tier_a.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    tier_b.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    print(f"Tier A: {len(tier_a)} | Tier B: {len(tier_b)}")
    if len(tier_a) < 5:
        raise Exception("Not enough Tier A coins")
    news = fetch_breaking_news()
    print(f"Fetched {len(news)} news articles")
    posts = []
    used_news_designs = []
    used_coin_ids = set()
    if len(news) >= 1:
        posts.append(build_news_post(news[0], used_news_designs))
        print("Post 1: News")
    else:
        posts.append(build_trending_post(tier_a))
        print("Post 1: Trending")
    if len(news) >= 2:
        posts.append(build_news_post(news[1], used_news_designs))
        print("Post 2: News")
    else:
        posts.append(build_trending_post(tier_a, exclude=posts[0]))
        print("Post 2: Trending")
    gainer = next((c for c in tier_a if c['id'] not in used_coin_ids), tier_a[0])
    posts.append(build_gainer_post(gainer))
    used_coin_ids.add(gainer['id'])
    loser = next((c for c in reversed(tier_a) if c['id'] not in used_coin_ids), tier_a[-1])
    posts.append(build_loser_post(loser))
    used_coin_ids.add(loser['id'])
    potential = [c for c in tier_b if c.get('total_volume', 0) > 5_000_000 and c['id'] not in used_coin_ids]
    random.shuffle(potential)
    for candidate in potential[:8]:
        print(f"Trying analysis on: {candidate['name']}")
        closes, highs, lows = fetch_ohlc(candidate['id'])
        if closes and len(closes) >= 20:
            posts.append(build_analysis_post(candidate, closes, highs, lows))
            print(f"Analysis ready: {candidate['name']}")
            break
        time.sleep(1)
    for i, text in enumerate(posts, 1):
        print(f"\n=== Post {i}/{len(posts)} ===")
        post_to_binance(text, api_key)
        if i < len(posts):
            time.sleep(5)
    print(f"\nAll {len(posts)} posts done!")


if __name__ == "__main__":
    main()
