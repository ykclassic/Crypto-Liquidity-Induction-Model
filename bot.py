import ccxt
import os
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 
           'DOGE/USDT', 'SOL/USDT', 'LINK/USDT', 'SUI/USDT', 'POL/USDT']
TIMEFRAMES = ['1h', '4h', '1d']
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
HEARTBEAT_HOUR = 12 

def identify_phases(df, tf, symbol):
    """
    Analyzes the 4-Phase Manipulation Model:
    1. Build (Equal Levels)
    2. Induction
    3. Raid (Stop Run)
    4. Displacement (Trend Start)
    """
    if len(df) < 25: 
        return None
        
    lookback = 20
    # Establish the structural "Levels"
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # 1. THE BUILD DETECTOR (Sensitivity: 0.15%)
    threshold = 0.0015
    current_low = df['low'].iloc[-1]
    current_high = df['high'].iloc[-1]
    last_close = df['close'].iloc[-1]
    
    is_eql = abs(current_low - df['lowest_prev'].iloc[-1]) < (last_close * threshold)
    is_eqh = abs(current_high - df['highest_prev'].iloc[-1]) < (last_close * threshold)
    
    # 2 & 3. THE RAID (Look at the PREVIOUS candle for the sweep)
    # Price dipped below/above and closed back inside
    raided_lows = (df['low'] < df['lowest_prev']) & (df['close'] > df['lowest_prev'])
    raided_highs = (df['high'] > df['highest_prev']) & (df['close'] < df['highest_prev'])
    
    # 4. DISPLACEMENT (The current candle confirms the move)
    displacement_up = raided_lows.shift(1) & (df['close'] > df['high'].shift(1))
    displacement_down = raided_highs.shift(1) & (df['close'] < df['low'].shift(1))

    # Logic Priority: Displacement > Build
    if displacement_up.iloc[-1]:
        return f"🔥 **PHASE 4: BULLISH DISPLACEMENT ({tf})**\nAsset: {symbol}\nStatus: Retail trapped below support. Smart money is buying the raid."
    if displacement_down.iloc[-1]:
        return f"🔥 **PHASE 4: BEARISH DISPLACEMENT ({tf})**\nAsset: {symbol}\nStatus: Retail trapped above resistance. Smart money is selling the raid."
    if is_eql:
        return f"🧱 **PHASE 1: BUILD (Equal Lows) ({tf})**\nAsset: {symbol}\nStatus: Liquidity is being engineered. Expect a raid below this level soon."
    if is_eqh:
        return f"🧱 **PHASE 1: BUILD (Equal Highs) ({tf})**\nAsset: {symbol}\nStatus: Liquidity is being engineered. Expect a raid above this level soon."
    
    return None

def send_to_discord(content, is_heartbeat=False):
    payload = {"username": "Omni-Manipulation Bot"}
    if is_heartbeat:
        payload["embeds"] = [content]
    else:
        payload["content"] = content
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Discord Error: {e}")

def run_check():
    # Multi-exchange rotation to handle regional blocks
    exchanges = [
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.bitget({'enableRateLimit': True}),
        ccxt.gateio({'enableRateLimit': True}),
        ccxt.kraken({'enableRateLimit': True})
    ]
    
    # Send Heartbeat at scheduled hour
    if datetime.utcnow().hour == HEARTBEAT_HOUR:
        send_to_discord({
            "title": "💓 System Heartbeat",
            "description": f"Successfully scanning {len(SYMBOLS)} assets.",
            "color": 3447003,
            "fields": [{"name": "Mode", "value": "Institutional Process Tracking", "inline": True}]
        }, is_heartbeat=True)

    for symbol in SYMBOLS:
        print(f"--- Scanning {symbol} ---")
        for tf in TIMEFRAMES:
            success = False
            for exchange in exchanges:
                try:
                    # Sync symbol for Kraken
                    target_symbol = symbol if exchange.id != 'kraken' else symbol.replace('USDT', 'USD')
                    
                    bars = exchange.fetch_ohlcv(target_symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                    
                    alert = identify_phases(df, tf, symbol)
                    if alert:
                        send_to_discord(f"**[Market Update]**\n{alert}")
                    
                    success = True
                    break # Success, move to next timeframe
                except Exception as e:
                    print(f"Exchange {exchange.id} failed for {symbol}: {e}")
                    continue
            
            # Anti-Rate Limit: 1.5 second pause between timeframes
            time.sleep(1.5)

if __name__ == "__main__":
    run_check()
