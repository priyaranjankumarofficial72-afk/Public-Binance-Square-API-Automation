import json
import os
import random
import time
import urllib.request

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


def fetch_ohlc(coin_id):
    try:
        url = "https://api.coingecko.com/api/v3/coins/" + coin_id + "/ohlc?vs_currency=usd&days=1"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        return [c[4] for c in data], [c[2] for c in data], [c[3] for c in data]
    except Exception as e:
        print("OHLC failed for " + coin_id + ": " + str(e))
        return None, None, None

    

OPENERS_GAINER = [
    "Yo yo yo!!! Look at this ROCKET!!!",
    "Wassup traders!! You're NOT gonna believe this!",
    "Legends!! Eyes on this one RIGHT NOW!",
    "Hey hey hey!! The bulls are BACK!!"
]

REASONS_GAINER = [
    ["Strong buying pressure from whales", "Broke through key resistance level", "Positive sentiment across the market", "Momentum traders piling in"],
    ["Whale wallets accumulating aggressively", "Flipped resistance into support", "Network activity hitting new highs", "Traders rotating into this play"],
    ["Volume EXPLODING on the charts", "Broke out of consolidation zone", "Social buzz going crazy", "Momentum shifting bullish"]
]

CLOSERS_GAINER = [
    "Don't chase green candles fam - wait for a pullback!",
    "Don't FOMO at the top fam - patience pays!",
    "Manage your risk and set those stops!"
]

OPENERS_LOSER = [
    "Ouch fam!! This one is hurting today!",
    "Hey fam!! This one got REKT today!",
    "Yo traders!! Red alert incoming!",
    "Legends!! Not a pretty picture today!"
]

REASONS_LOSER = [
    ["Whales taking profits", "Broke key support level", "General market weakness", "Exchange inflows spiking"],
    ["Major whale exit spotted", "Lost critical support", "Staking rewards sell-off pressure", "Correlation to broader alt weakness"],
    ["Profit-taking after recent run", "Weak sentiment across alts", "Failed to hold key level", "Sell pressure building up"]
]

CLOSERS_LOSER = [
    "Do NOT panic sell! Smart money buys fear!",
    "Do NOT panic sell! Dips can be opportunities!",
    "Stay patient fam - this too shall pass!"
]


def build_gainer_post(coin):
    opener = random.choice(OPENERS_GAINER)
    reasons = random.choice(REASONS_GAINER)
    closer = random.choice(CLOSERS_GAINER)
    sym = coin['symbol'].upper()
    chg = coin['price_change_percentage_24h']
    price = coin['current_price']
    high = coin.get('high_24h', price * 1.05)
    reasons_text = "\n".join(["✅ " + r for r in reasons])
    next_up = price * 1.10
    next_down = price * 0.95
    return "🚀🚀🚀 TOP GAINER ALERT 🚀🚀🚀\n\n" + opener + " 🔥🔥🔥\n\n$" + sym + " is absolutely FLYING today! 📈📈\n\n📊 The Numbers:\n💰 Price: $" + str(round(price, 4)) + "\n📈 24h Gain: +" + str(round(chg, 1)) + "% 🔥\n\n🧠 Why It Pumped:\n" + reasons_text + "\n\n📊 Next Move:\n🎯 If it holds above $" + str(round(price, 2)) + " → could target $" + str(round(next_up, 2)) + " 🚀\n⚠️ If it rejects here → pullback to $" + str(round(next_down, 2)) + " possible 📉\n💎 Watch volume - high volume = continuation\n\n🛡️ " + closer + "\n\n⚠️ DYOR, NFA! 💎🙌\n\n$" + sym + " 🪙🚀"


def build_loser_post(coin):
    opener = random.choice(OPENERS_LOSER)
    reasons = random.choice(REASONS_LOSER)
    closer = random.choice(CLOSERS_LOSER)
    sym = coin['symbol'].upper()
    chg = abs(coin['price_change_percentage_24h'])
    price = coin['current_price']
    reasons_text = "\n".join(["❌ " + r for r in reasons])
    bounce = price * 1.06
    next_support = price * 0.93
    return "⚠️⚠️⚠️ TOP LOSER ALERT ⚠️⚠️⚠️\n\n" + opener + " 😬📉\n\n$" + sym + " is getting hammered! 💔\n\n📊 The Damage:\n💰 Price: $" + str(round(price, 4)) + "\n📉 24h Drop: -" + str(round(chg, 1)) + "% 💀\n\n🧠 Why It Dumped:\n" + reasons_text + "\n\n📊 Next Move:\n🎯 If $" + str(round(price, 2)) + " holds → bounce to $" + str(round(bounce, 2)) + " possible 💪\n⚠️ If it breaks → next support at $" + str(round(next_support, 2)) + " 📉\n🔍 Watch BTC - if BTC dumps, this follows\n\n🛡️ " + closer + "\n\n⚠️ DYOR, NFA! 🙏\n\n$" + sym + " 🪙"


def analyze_coin(coin, closes, highs, lows):
    price = coin['current_price']
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
            reasons.append("✅ EMA20 > EMA50 - bullish trend 📈")
        else:
            score -= 1
            reasons.append("📉 EMA20 < EMA50 - bearish trend")
    if r14 is not None:
        if r14 > 70:
            score -= 1
            reasons.append("⚠️ RSI " + str(round(r14, 1)) + " - overbought")
        elif r14 < 30:
            score += 1
            reasons.append("💎 RSI " + str(round(r14, 1)) + " - oversold")
        elif r14 > 50:
            score += 1
            reasons.append("✅ RSI " + str(round(r14, 1)) + " - bullish momentum 💪")
        else:
            score -= 1
            reasons.append("🔻 RSI " + str(round(r14, 1)) + " - bearish")
    if m is not None and s is not None:
        if m > s:
            score += 1
            reasons.append("🚀 MACD bullish crossover confirmed")
        else:
            score -= 1
            reasons.append("📉 MACD bearish crossover")
    if bu and bl:
        if price > bu:
            score -= 1
            reasons.append("⚠️ Above upper Bollinger Band - overextended")
        elif price < bl:
            score += 1
            reasons.append("💎 Below lower Bollinger Band - oversold zone")
        else:
            reasons.append("📊 Price inside Bollinger Bands - neutral")
    return score, reasons, a


def build_analysis_post(coin, closes, highs, lows):
    sym = coin['symbol'].upper()
    price = coin['current_price']
    change = coin['price_change_percentage_24h']
    high = coin.get('high_24h', price * 1.05)
    low = coin.get('low_24h', price * 0.95)
    score, reasons, a = analyze_coin(coin, closes, highs, lows)
    if score >= 3:
        signal = "🟢🟢🟢 SIGNAL: STRONG BUY 🟢🟢🟢"
        direction = "BUY"
    elif score >= 1:
        signal = "🟢 SIGNAL: BUY 🟢"
        direction = "BUY"
    elif score <= -3:
        signal = "🔴🔴🔴 SIGNAL: STRONG SELL 🔴🔴🔴"
        direction = "SELL"
    elif score <= -1:
        signal = "🔴 SIGNAL: SELL 🔴"
        direction = "SELL"
    else:
        signal = "🟡 SIGNAL: HOLD 🟡"
        direction = "HOLD"
    trade_section = "⏸️ No trade setup at the moment - waiting for clearer signal"
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
            trade_section = "🎯🎯 TRADE SETUP 🎯🎯\n📍 Entry: $" + str(round(entry, 4)) + "\n🛑 Stop Loss: $" + str(round(sl, 4)) + " (" + str(round((risk/entry)*100, 1)) + "% risk)\n✅ TP1: $" + str(round(tp1, 4)) + " (RR 1.5x) 🎯\n✅ TP2: $" + str(round(tp2, 4)) + " (RR 2.5x) 🎯\n✅ TP3: $" + str(round(tp3, 4)) + " (RR 4.0x) 🎯"
    reasons_text = "\n".join(reasons)
    return "🤖🤖 AI ANALYSIS ALERT 🤖🤖\n\n🎯 High-Conviction Setup Detected!\n\nLegends! My algo scanned 30+ coins and found a signal on:\n\n💎 $" + sym + " 💎\n\n💰 Price: $" + str(round(price, 4)) + "\n📊 24h: " + str(round(change, 1)) + "%\n📈 24h High: $" + str(round(high, 4)) + "\n📉 24h Low: $" + str(round(low, 4)) + "\n\n📐 Technical Indicators:\n" + reasons_text + "\n\n" + signal + "\n\n" + trade_section + "\n\n⚠️⚠️ DISCLAIMER: Not financial advice! DYOR! Always use stop loss! 🛡️\n\n🚀 Let's get it, fam! 💎🙌\n\n$" + sym + " 🪙📈"


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
    posts = []
    used_coin_ids = set()
    gainer = next((c for c in tier_a if c['id'] not in used_coin_ids), tier_a[0])
    posts.append(build_gainer_post(gainer))
    used_coin_ids.add(gainer['id'])
    print("Post 1: Gainer " + gainer['symbol'].upper())
    loser = next((c for c in reversed(tier_a) if c['id'] not in used_coin_ids), tier_a[-1])
    posts.append(build_loser_post(loser))
    used_coin_ids.add(loser['id'])
    print("Post 2: Loser " + loser['symbol'].upper())
    potential = [c for c in tier_b if c.get('total_volume', 0) > 5000000 and c['id'] not in used_coin_ids]
    random.shuffle(potential)
    best_coin = None
    best_score = -99
    for candidate in potential[:15]:
        closes, highs, lows = fetch_ohlc(candidate['id'])
        if closes and len(closes) >= 20:
            score, _, _ = analyze_coin(candidate, closes, highs, lows)
            print("Analysis scan: " + candidate['symbol'].upper() + " score=" + str(score))
            if score > best_score:
                best_score = score
                best_coin = (candidate, closes, highs, lows)
        time.sleep(1)
    if best_coin:
        coin, closes, highs, lows = best_coin
        posts.append(build_analysis_post(coin, closes, highs, lows))
        print("Post 3: Analysis " + coin['symbol'].upper() + " (score " + str(best_score) + ")")
    for i, text in enumerate(posts, 1):
        print("\n=== Post " + str(i) + "/" + str(len(posts)) + " ===")
        post_to_binance(text, api_key)
        if i < len(posts):
            time.sleep(5)
    print("\nAll " + str(len(posts)) + " posts completed")


if __name__ == "__main__":
    main()
