import ccxt
import os
import pandas as pd
import requests
import time

# --- CONFIGURATION ---
SYMBOL = 'BTC/USDT'
TIMEFRAMES = ['1h', '4h', '1d']  # Added higher timeframes
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def identify_manipulation_move(df, tf):
    # Phase 1: The Build (Lookback 20 units of the current timeframe)
    lookback = 20
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # Phase 2 & 3: The Raid (Sweeping EQL/EQH)
    raided_lows = (df['low'] < df['lowest_prev']) & (df['close'] > df['lowest_prev'])
    raided_highs = (df['high'] > df['highest_prev']) & (df['close'] < df['highest_prev'])
    
    # Phase 4: Displacement (Confirmation candle)
    displacement_up = raided_lows.shift(1) & (df['close'] > df['high'].shift(1))
    displacement_down = raided_highs.shift(1) & (df['close'] < df['low'].shift(1))

    if displacement_up.iloc[-1]:
        return f"🚀 **BULLISH MANIPULATION ({tf})**\nStructure: Liquidity Sweep + Displacement Up.\nAction: Look for long entries on the retest."
    elif displacement_down.iloc[-1]:
        return f"⚠️ **BEARISH MANIPULATION ({tf})**\nStructure: Liquidity Sweep + Displacement Down.\nAction: Look for short entries on the retest."
    return None

def run_check():
    # Use Kraken as primary for GitHub compatibility, fallback to KuCoin
    exchanges = [ccxt.kraken(), ccxt.kucoin()]
    
    for tf in TIMEFRAMES:
        success = False
        for exchange in exchanges:
            try:
                # Adjust symbol for Kraken
                target_symbol = SYMBOL if exchange.id != 'kraken' else 'BTC/USD'
                
                # Fetch more bars to ensure lookback is populated
                bars = exchange.fetch_ohlcv(target_symbol, timeframe=tf, limit=100)
                df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                
                signal = identify_manipulation_move(df, tf)
                
                if signal:
                    payload = {
                        "username": "Manipulation Bot",
                        "content": f"**[HTF Process Signal]**\nAsset: {target_symbol}\n{signal}"
                    }
                    requests.post(DISCORD_WEBHOOK_URL, json=payload)
                    print(f"Signal sent for {tf} via {exchange.id}")
                else:
                    print(f"Checked {tf} on {exchange.id}: No sequence found.")
                
                success = True
                break 
            except Exception as e:
                print(f"Error checking {tf} on {exchange.id}: {e}")
                continue
        
        # Small delay between timeframe checks to avoid rate limits
        time.sleep(2)

if __name__ == "__main__":
    run_check()
