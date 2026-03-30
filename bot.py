import ccxt
import os
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
# Added all requested assets
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 
           'DOGE/USDT', 'SOL/USDT', 'LINK/USDT', 'SUI/USDT', 'POL/USDT']
TIMEFRAMES = ['1h', '4h', '1d']
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
HEARTBEAT_HOUR = 12 

def identify_phases(df, tf, symbol):
    if len(df) < 22: return None
        
    lookback = 20
    # Current structural levels
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # 1. THE BUILD DETECTOR (Equal Highs/Lows within 0.15% range)
    threshold = 0.0015
    is_eql = abs(df['low'].iloc[-1] - df['lowest_prev'].iloc[-1]) < (df['close'].iloc[-1] * threshold)
    is_eqh = abs(df['high'].iloc[-1] - df['highest_prev'].iloc[-1]) < (df['close'].iloc[-1] * threshold)
    
    # 2 & 3. THE RAID
    raided_lows = (df['low'] < df['lowest_prev']) & (df['close'] > df['lowest_prev'])
    raided_highs = (df['high'] > df['highest_prev']) & (df['close'] < df['highest_prev'])
    
    # 4. DISPLACEMENT (Phase 4)
    displacement_up = raided_lows.shift(1) & (df['close'] > df['high'].shift(1))
    displacement_down = raided_highs.shift(1) & (df['close'] < df['low'].shift(1))

    # Return specific alerts based on priority
    if displacement_up.iloc[-1]:
        return f"🔥 **PHASE 4: BULLISH DISPLACEMENT ({tf})**\n{symbol}: Retail trapped. Expansion starting."
    if displacement_down.iloc[-1]:
        return f"🔥 **PHASE 4: BEARISH DISPLACEMENT ({tf})**\n{symbol}: Retail trapped. Expansion starting."
    if is_eql:
        return f"🧱 **PHASE 1: BUILD (EQL) ({tf})**\n{symbol}: Equal Lows forming. Liquidity is being engineered here."
    if is_eqh:
        return f"🧱 **PHASE 1: BUILD (EQH) ({tf})**\n{symbol}: Equal Highs forming. Liquidity is being engineered here."
    
    return None

def send_to_discord(content, is_heartbeat=False):
    payload = {"username": "Omni-Manipulation Bot"}
    if is_heartbeat:
        payload["embeds"] = [content]
    else:
        payload["content"] = content
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Discord Error: {e}")

def run_check():
    # Multi-exchange pool
    exchanges = [
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.bitget({'enableRateLimit': True}),
        ccxt.gateio({'enableRateLimit': True}),
        ccxt.kraken({'enableRateLimit': True})
    ]
    
    # Heartbeat
    if datetime.utcnow().hour == HEARTBEAT_HOUR:
        send_to_discord({
            "title": "💓 System Heartbeat",
            "description": f"Scanning {len(SYMBOLS)} assets across {len(TIMEFRAMES)} timeframes.",
            "color": 3447003
        }, is_heartbeat=True)

    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            for exchange in exchanges:
                try:
                    # Specific handling for Kraken's symbol naming
                    clean_symbol = symbol if exchange.id != 'kraken' else symbol.replace('USDT', 'USD')
                    
                    bars = exchange.fetch_ohlcv(clean_symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                    
                    alert = identify_phases(df, tf, symbol)
                    if alert:
                        send_to_discord(f"**[Market Update]**\nSource: {exchange.id}\n{alert}")
                    
                    break # Success on this symbol/tf, move to next
                except Exception:
                    continue # Try next exchange if this one fails
            time.sleep(1) # Regulatory pause

if __name__ == "__main__":
    run_check()    # Return specific alerts based on priority
    if displacement_up.iloc[-1]:
        return f"🔥 **PHASE 4: BULLISH DISPLACEMENT ({tf})**\n{symbol}: Retail trapped. Expansion starting."
    if displacement_down.iloc[-1]:
        return f"🔥 **PHASE 4: BEARISH DISPLACEMENT ({tf})**\n{symbol}: Retail trapped. Expansion starting."
    if is_eql:
        return f"🧱 **PHASE 1: BUILD (EQL) ({tf})**\n{symbol}: Equal Lows forming. Liquidity is being engineered here."
    if is_eqh:
        return f"🧱 **PHASE 1: BUILD (EQH) ({tf})**\n{symbol}: Equal Highs forming. Liquidity is being engineered here."
    
    return None

def send_to_discord(content, is_heartbeat=False):
    payload = {"username": "Omni-Manipulation Bot"}
    if is_heartbeat:
        payload["embeds"] = [content]
    else:
        payload["content"] = content
    
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload)
    except Exception as e:
        print(f"Discord Error: {e}")

def run_check():
    # Multi-exchange pool
    exchanges = [
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.bitget({'enableRateLimit': True}),
        ccxt.gateio({'enableRateLimit': True}),
        ccxt.kraken({'enableRateLimit': True})
    ]
    
    # Heartbeat
    if datetime.utcnow().hour == HEARTBEAT_HOUR:
        send_to_discord({
            "title": "💓 System Heartbeat",
            "description": f"Scanning {len(SYMBOLS)} assets across {len(TIMEFRAMES)} timeframes.",
            "color": 3447003
        }, is_heartbeat=True)

    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            for exchange in exchanges:
                try:
                    # Specific handling for Kraken's symbol naming
                    clean_symbol = symbol if exchange.id != 'kraken' else symbol.replace('USDT', 'USD')
                    
                    bars = exchange.fetch_ohlcv(clean_symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                    
                    alert = identify_phases(df, tf, symbol)
                    if alert:
                        send_to_discord(f"**[Market Update]**\nSource: {exchange.id}\n{alert}")
                    
                    break # Success on this symbol/tf, move to next
                except Exception:
                    continue # Try next exchange if this one fails
            time.sleep(1) # Regulatory pause

if __name__ == "__main__":
    run_check()
