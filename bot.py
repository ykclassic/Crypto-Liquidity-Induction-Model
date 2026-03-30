import ccxt
import os
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 
    'DOGE/USDT', 'SOL/USDT', 'LINK/USDT', 'SUI/USDT', 'POL/USDT'
]
TIMEFRAMES = ['1h', '4h', '1d']
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')
HEARTBEAT_HOUR = 12  # UTC hour for daily status update

# --- TRADING LOGIC FUNCTIONS ---

def is_killzone():
    """Checks if current time is within high-probability institutional windows (UTC)."""
    now_utc = datetime.utcnow().hour
    # London Open (07:00-10:00) | NY Open (13:00-16:00)
    return (7 <= now_utc <= 10) or (13 <= now_utc <= 16)

def identify_phases(df, tf, symbol):
    """
    Core Manipulation Model:
    Phase 1: Build (Engineered Liquidity)
    Phase 2/3: Induction & Raid (The Trap)
    Phase 4: Displacement (Institutional Entry)
    """
    if len(df) < 30:
        return None
        
    # Technical Data
    df['avg_vol'] = df['vol'].rolling(window=10).mean()
    lookback = 20
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # 1. PHASE 1: BUILD DETECTOR (Equal Levels)
    # Sensitivity threshold for 'Equal' (0.15%)
    threshold = 0.0015
    last_close = df['close'].iloc[-1]
    is_eql = abs(df['low'].iloc[-1] - df['lowest_prev'].iloc[-1]) < (last_close * threshold)
    is_eqh = abs(df['high'].iloc[-1] - df['highest_prev'].iloc[-1]) < (last_close * threshold)
    
    # 2 & 3. PHASE 2/3: THE RAID (Detected on the previous candle)
    prev_low = df['low'].iloc[-2]
    prev_high = df['high'].iloc[-2]
    prev_close = df['close'].iloc[-2]
    
    raided_low = (prev_low < df['lowest_prev'].iloc[-2]) and (prev_close > df['lowest_prev'].iloc[-2])
    raided_high = (prev_high > df['highest_prev'].iloc[-2]) and (prev_close < df['highest_prev'].iloc[-2])
    
    # 4. PHASE 4: DISPLACEMENT (Current Candle Confirmation)
    vol_confirmation = df['vol'].iloc[-1] > (df['avg_vol'].iloc[-1] * 1.3)
    killzone_active = is_killzone()
    
    # BULLISH SIGNAL GENERATION
    if raided_low and df['close'].iloc[-1] > df['high'].iloc[-2]:
        entry = df['high'].iloc[-2]
        sl = prev_low - (entry * 0.0005) # SL slightly below raid wick
        tp = df['highest_prev'].iloc[-1] # Target opposite liquidity
        rrr = abs(tp - entry) / abs(entry - sl) if abs(entry - sl) != 0 else 0
        
        return {
            "type": "LONG",
            "msg": (f"🚀 **INSTITUTIONAL BUY SIGNAL ({tf})**\n"
                    f"Asset: **{symbol}**\n"
                    f"--- TRADE PLAN ---\n"
                    f"🔹 **Entry:** {entry:.4f}\n"
                    f"🚩 **Stop Loss:** {sl:.4f}\n"
                    f"🎯 **Take Profit:** {tp:.4f}\n"
                    f"⚖️ **RRR:** {rrr:.2f}\n\n"
                    f"{'✅' if vol_confirmation else '❌'} Volume Confirmation\n"
                    f"{'✅' if killzone_active else '❌'} Killzone Timing")
        }

    # BEARISH SIGNAL GENERATION
    if raided_high and df['close'].iloc[-1] < df['low'].iloc[-2]:
        entry = df['low'].iloc[-2]
        sl = prev_high + (entry * 0.0005)
        tp = df['lowest_prev'].iloc[-1]
        rrr = abs(entry - tp) / abs(sl - entry) if abs(sl - entry) != 0 else 0
        
        return {
            "type": "SHORT",
            "msg": (f"⚠️ **INSTITUTIONAL SELL SIGNAL ({tf})**\n"
                    f"Asset: **{symbol}**\n"
                    f"--- TRADE PLAN ---\n"
                    f"🔹 **Entry:** {entry:.4f}\n"
                    f"🚩 **Stop Loss:** {sl:.4f}\n"
                    f"🎯 **Take Profit:** {tp:.4f}\n"
                    f"⚖️ **RRR:** {rrr:.2f}\n\n"
                    f"{'✅' if vol_confirmation else '❌'} Volume Confirmation\n"
                    f"{'✅' if killzone_active else '❌'} Killzone Timing")
        }

    # BUILD WARNING (Lower Priority than a Signal)
    if is_eql or is_eqh:
        side = "Support (EQL)" if is_eql else "Resistance (EQH)"
        return {
            "type": "BUILD",
            "msg": f"🧱 **PHASE 1: BUILD ({tf})**\nAsset: **{symbol}**\nStatus: Engineered {side} detected. Liquidity is being baiting retail. Expect a raid soon."
        }
    
    return None

# --- UTILITY FUNCTIONS ---

def send_to_discord(content, is_embed=False):
    """Sends messages or embeds to Discord."""
    payload = {"username": "Omni-Manipulation Bot"}
    if is_embed:
        payload["embeds"] = [content]
    else:
        payload["content"] = content
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except Exception as e:
        print(f"Discord Error: {e}")

def run_check():
    """Main execution loop for all symbols and timeframes."""
    # List of exchanges for geo-redundancy
    exchanges = [
        ccxt.bybit({'enableRateLimit': True}),
        ccxt.bitget({'enableRateLimit': True}),
        ccxt.gateio({'enableRateLimit': True}),
        ccxt.kraken({'enableRateLimit': True})
    ]
    
    # Send Heartbeat
    if datetime.utcnow().hour == HEARTBEAT_HOUR:
        send_to_discord({
            "title": "💓 System Heartbeat",
            "description": "The Liquidity Induction Model is fully operational.",
            "color": 3447003,
            "fields": [
                {"name": "Assets", "value": f"{len(SYMBOLS)} Pairs", "inline": True},
                {"name": "Status", "value": "Scanning Traps", "inline": True}
            ]
        }, is_embed=True)

    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            success = False
            for exchange in exchanges:
                try:
                    # Sync symbol for Kraken (USD vs USDT)
                    target_symbol = symbol if exchange.id != 'kraken' else symbol.replace('USDT', 'USD')
                    
                    print(f"Checking {symbol} on {tf} via {exchange.id}...")
                    bars = exchange.fetch_ohlcv(target_symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                    
                    result = identify_phases(df, tf, symbol)
                    if result:
                        send_to_discord(result['msg'])
                    
                    success = True
                    break # Success on this symbol/tf, move to next
                except Exception as e:
                    print(f"Error on {exchange.id}: {e}")
                    continue
            
            # Anti-Rate Limit pause
            time.sleep(1.2)

if __name__ == "__main__":
    run_check()
