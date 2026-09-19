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


def ask_groq(prompt):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print("No GROQ_API_KEY set")
        return None
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": "You are a crypto content writer for Binance Square. Write short viral posts with LOTS of emojis. Never copy headlines. Write your own angle. Max 80 words. End with a cashtag like $BTC or $ETH. Include a disclaimer like 'DYOR, NFA'. Plain text with emojis only, no markdown."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.9
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Authorization': 'Bearer ' + api_key,
        'Content-Type': 'application/json'
    }, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            text = result['choices'][0]['message']['content'].strip()
            print("Groq generated " + str(len(text)) + " chars")
            return text
    except Exception as e:
        print("Groq error: " + str(e))
        if hasattr(e, 'read'):
            print(e.read().decode()[:300])
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
    gains = 0
    losses = 0
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
        print("Breaking news failed: " + str(e))
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
            print("News fetch failed: " + str(e))
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
        print("Trending failed: " + str(e))
        return []


def fetch_ohlc(coin_id):
    try:
        url = "https://api.coingecko.com/api/v3/coins/" + coin_id + "/ohlc?vs_currency=usd&days=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        return [c[4] for c in data], [c[2] for c in data], [c[3] for c in data]
    except Exception:
        return None, None, None


def build_ai_news_post(article):
    title = article.get('title', '')
    coin = extract_coin_from_title(title) or "BTC"
    prompt = "Write a viral crypto news post about this topic: '" + title + "'. Do NOT copy the headline. Write your own angle about how this affects the market. Use LOTS of emojis. End with the cashtag $" + coin + " and a short disclaimer DYOR NFA."
    ai_text = ask_groq(prompt)
    if ai_text:
        return ai_text
    return "CRYPTO NEWS ALERT\n\nHey fam! Something big is happening in the market right now. Stay alert.\n\n- Volatility incoming\n- Watch key levels\n- Stay sharp\n\nDYOR, NFA\n\n$" + coin


def build_ai_trending_post(tier_a, exclude=None):
    topics = fetch_binance_trending()
    if not topics:
        topics = ["Bitcoin", "Ethereum", "CryptoMarket", "Altcoins", "DeFi"]
    hashtags = " ".join(["#" + t.replace(" ", "") for t in topics[:5]])
    prompt = "Write a viral crypto trending post for Binance Square. Today's trending topics: " + ", ".join(topics[:5]) + ". Include these hashtags: " + hashtags + ". Use LOTS of emojis. Friendly tone. End with #Binance #Crypto."
    ai_text = ask_groq(prompt)
    if ai_text:
        return ai_text
    return "BINANCE TRENDING NOW\n\n" + hashtags + "\n\n- Sentiment active\n- Volume picking up\n- Traders positioning\n\n#Binance #Crypto"


def build_gainer_post(coin):
    sym = coin['symbol'].upper()
    chg = coin['price_change_percentage_24h']
    price = coin['current_price']
    prompt = "Write a viral top gainer post about " + coin['name'] + " ($" + sym + ") which is up " + str(round(chg, 1)) + "% in 24 hours, price $" + str(round(price, 4)) + ". Use LOTS of emojis. Explain why it pumped, the market impact, and warn about chasing green candles. End with $" + sym + "."
    ai_text = ask_groq(prompt)
    if ai_text:
        return ai_text
    return "TOP GAINER: $" + sym + " Up " + str(round(chg, 1)) + "%\n\n" + coin['name'] + " is flying - up " + str(round(chg, 1)) + "% in 24h!\n\n- Strong buying volume\n- Breaking resistance\n- Momentum building\n\nCurrent price: $" + str(round(price, 4)) + "\n\nMarket Impact: Watch for a pullback.\n\nDYOR, NFA\n\n$" + sym


def build_loser_post(coin):
    sym = coin['symbol'].upper()
    chg = abs(coin['price_change_percentage_24h'])
    price = coin['current_price']
    prompt = "Write a viral top loser post about " + coin['name'] + " ($" + sym + ") which is down " + str(round(chg, 1)) + "% in 24 hours, price $" + str(round(price, 4)) + ". Use LOTS of emojis. Explain why it dumped, recovery outlook, and reassure not to panic sell. End with $" + sym + "."
    ai_text = ask_groq(prompt)
    if ai_text:
        return ai_text
    return "TOP LOSER: $" + sym + " Down " + str(round(chg, 1)) + "%\n\n" + coin['name'] + " dropped " + str(round(chg, 1)) + "% in 24h.\n\n- Whales taking profits\n- Weak sentiment\n- Broke support\n\nPrice: $" + str(round(price, 4)) + "\n\nMarket Impact: Watch support. Don't panic sell.\n\nDYOR, NFA\n\n$" + sym


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
            reasons.append("EMA20 above EMA50 - bullish trend")
        else:
            score -= 1
            reasons.append("EMA20 below EMA50 - bearish trend")
    if r14 is not None:
        if r14 > 70:
            score -= 1
            reasons.append("RSI " + str(round(r14, 1)) + " overbought")
        elif r14 < 30:
            score += 1
            reasons.append("RSI " + str(round(r14, 1)) + " oversold")
        elif r14 > 50:
            score += 1
            reasons.append("RSI " + str(round(r14, 1)) + " bullish")
        else:
            score -= 1
            reasons.append("RSI " + str(round(r14, 1)) + " bearish")
    if m is not None and s is not None:
        if m > s:
            score += 1
            reasons.append("MACD bullish crossover")
        else:
            score -= 1
            reasons.append("MACD bearish crossover")
    if bu and bl:
        if price > bu:
            score -= 1
            reasons.append("Above upper Bollinger Band - overextended")
        elif price < bl:
            score += 1
            reasons.append("Below lower Bollinger Band - oversold")
        else:
            reasons.append("Inside Bollinger Bands - neutral")
    if score >= 3:
        signal = "STRONG BUY"
        direction = "BUY"
    elif score >= 1:
        signal = "BUY"
        direction = "BUY"
    elif score <= -3:
        signal = "STRONG SELL"
        direction = "SELL"
    elif score <= -1:
        signal = "SELL"
        direction = "SELL"
    else:
        signal = "HOLD"
        direction = "HOLD"
    trade_section = "No trade setup at the moment"
    if direction in ["BUY", "SELL"] and a:
        if direction == "BUY":
            entry = price
            sl = max(entry - 1.5*a, min(lows[-10:]) * 0.99 if len(lows) >= 10 else entry * 0.95)
            risk = entry - sl
            tp1 = entry + risk*1.5
            tp2 = entry + risk*2.5
            tp3 = entry + risk*4.0
        else:
            entry = price
            sl = min(entry + 1.5*a, max(highs[-10:]) * 1.01 if len(highs) >= 10 else entry * 1.05)
            risk = sl - entry
            tp1 = entry - risk*1.5
            tp2 = entry - risk*2.5
            tp3 = entry - risk*4.0
        if risk > 0:
            trade_section = "Entry: $" + str(round(entry, 4)) + "\nStop Loss: $" + str(round(sl, 4)) + " (" + str(round((risk/entry)*100, 1)) + "% risk)\nTP1: $" + str(round(tp1, 4)) + " (RR 1.5x)\nTP2: $" + str(round(tp2, 4)) + " (RR 2.5x)\nTP3: $" + str(round(tp3, 4)) + " (RR 4.0x)"
    prompt = "Write a viral AI analysis post for " + coin['name'] + " ($" + sym + "). Price $" + str(round(price, 4)) + ", 24h change " + str(round(change, 1)) + "%. Signal: " + signal + ". Indicators: " + ", ".join(reasons) + ". Trade setup: " + trade_section + ". Use LOTS of emojis. Include a disclaimer. End with $" + sym + "."
    ai_text = ask_groq(prompt)
    if ai_text:
        return ai_text
    return "AI ANALYSIS: $" + sym + "\n\n" + coin['name'] + "\nPrice: $" + str(round(price, 4)) + "\n24h: " + str(round(change, 1)) + "%\n\nIndicators:\n" + "\n".join(reasons) + "\n\nSignal: " + signal + "\n\nTrade Setup:\n" + trade_section + "\n\nNFA, DYOR, use stop loss!\n\n$" + sym

    

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
            print("POST SUCCESS: " + r.read().decode()[:200])
            return True
    except Exception as e:
        print("POST ERROR: " + str(e))
        if hasattr(e, 'read'):
            print(e.read().decode()[:300])
        return False


def main():
    api_key = os.environ.get("BINANCE_KEY")
    if not api_key:
        raise Exception("BINANCE_KEY secret is missing")
    coins = fetch_market()
    tier_a = [c for c in coins if c['id'] in BINANCE_TIER_A and c.get('price_change_percentage_24h') is not None]
    tier_b = [c for c in coins if c['id'] in BINANCE_TIER_B and c.get('price_change_percentage_24h') is not None]
    tier_a.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    tier_b.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    print("Tier A: " + str(len(tier_a)) + " | Tier B: " + str(len(tier_b)))
    if len(tier_a) < 5:
        raise Exception("Not enough Binance Tier A coins found")
    news = fetch_breaking_news()
    print("News fetched: " + str(len(news)))
    posts = []
    used_coin_ids = set()
    if len(news) >= 1:
        posts.append(build_ai_news_post(news[0]))
        print("Post 1: AI News")
    else:
        posts.append(build_ai_trending_post(tier_a))
        print("Post 1: AI Trending")
    if len(news) >= 2:
        posts.append(build_ai_news_post(news[1]))
        print("Post 2: AI News")
    else:
        posts.append(build_ai_trending_post(tier_a))
        print("Post 2: AI Trending")
    gainer = next((c for c in tier_a if c['id'] not in used_coin_ids), tier_a[0])
    posts.append(build_gainer_post(gainer))
    used_coin_ids.add(gainer['id'])
    print("Post 3: Gainer " + gainer['symbol'].upper())
    loser = next((c for c in reversed(tier_a) if c['id'] not in used_coin_ids), tier_a[-1])
    posts.append(build_loser_post(loser))
    used_coin_ids.add(loser['id'])
    print("Post 4: Loser " + loser['symbol'].upper())
    potential = [c for c in tier_b if c.get('total_volume', 0) > 5000000 and c['id'] not in used_coin_ids]
    random.shuffle(potential)
    for candidate in potential[:8]:
        print("Analysis try: " + candidate['name'])
        closes, highs, lows = fetch_ohlc(candidate['id'])
        if closes and len(closes) >= 20:
            posts.append(build_analysis_post(candidate, closes, highs, lows))
            print("Post 5: Analysis " + candidate['symbol'].upper())
            break
        time.sleep(1)
    for i, text in enumerate(posts, 1):
        print("\n=== Post " + str(i) + "/" + str(len(posts)) + " ===")
        post_to_binance(text, api_key)
        if i < len(posts):
            time.sleep(5)
    print("\nAll " + str(len(posts)) + " posts completed")


if __name__ == "__main__":
    main()
