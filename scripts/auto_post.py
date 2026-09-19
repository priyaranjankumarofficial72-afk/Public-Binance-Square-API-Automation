import json
import os
import urllib.request

COUNTER_FILE = "counter.txt"

TEMPLATES = [
    """🚀 **TOP GAINER: ${symbol} Up {change:.1f}%!** 🚀

Yo yo yo! 🔥 Look at this rocket!

**{name} is absolutely flying** — up **{change:.1f}% in 24h!** 📈

Why the pump? 🤔
✅ Strong buying volume
✅ Breaking resistance levels
✅ Market momentum building

Current price: **${price:,.4f}** 💰

Don't chase green candles, fam! 🧠

**${symbol}**""",

    """⚠️ **TOP LOSER: ${symbol} Down {change:.1f}%!** ⚠️

Ouch fam! 😬 {name} is hurting today.

**{name} dropped {abs(change):.1f}%** in 24h. 📉

Why the dump? 🤔
❌ Whales taking profits
❌ Weak market sentiment
❌ Broke key support

**Recovery check:** 🔍
Watch for a bounce — if volume returns, bulls could step back in. 💪

Don't panic sell! 💎🙌

**${symbol}**"""
]

def get_next_index():
    if not os.path.exists(COUNTER_FILE):
        return 0
    with open(COUNTER_FILE, "r") as f:
        try:
            idx = int(f.read().strip())
        except:
            idx = 0
    return idx % len(TEMPLATES)

def save_next_index(idx):
    with open(COUNTER_FILE, "w") as f:
        f.write(str(idx))

def fetch_market():
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&price_change_percentage=24h"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    valid = [c for c in data if c.get('price_change_percentage_24h') is not None]
    valid.sort(key=lambda x: x['price_change_percentage_24h'], reverse=True)
    return valid[0], valid[-1]

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
            print("POST SUCCESS:", r.read().decode())
    except Exception as e:
        print("POST ERROR:", e)
        if hasattr(e, 'read'):
            print(e.read().decode())
        raise

def main():
    api_key = os.environ.get("BINANCE_KEY")
    if not api_key:
        raise Exception("BINANCE_KEY secret is missing!")

    idx = get_next_index()
    print(f"Using template index: {idx}")

    gainer, loser = fetch_market()
    print(f"Top gainer: {gainer['name']}")
    print(f"Top loser: {loser['name']}")

    coin = gainer if idx == 0 else loser

    post_text = TEMPLATES[idx].format(
        name=coin['name'],
        symbol=coin['symbol'].upper(),
        change=coin['price_change_percentage_24h'],
        price=coin['current_price']
    )

    print("=== Generated Post ===")
    print(post_text)
    print("======================")

    post_to_binance(post_text, api_key)

    save_next_index((idx + 1) % len(TEMPLATES))
    print(f"Counter updated to: {(idx + 1) % len(TEMPLATES)}")

if __name__ == "__main__":
    main()
