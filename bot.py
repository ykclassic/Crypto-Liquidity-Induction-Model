import ccxt
import os
import pandas as pd
import requests

# --- CONFIGURATION ---
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def identify_manipulation_move(df):
    # Phase 1: The Build (Lookback 20 candles)
    lookback = 20
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # Phase 2 & 3: The Raid (Price sweeps but closes back inside)
    raided_lows = (df['low'] < df['lowest_prev']) & (df['close'] > df['lowest_prev'])
    raided_highs = (df['high'] > df['highest_prev']) & (df['close'] < df['highest_prev'])
    
    # Phase 4: Displacement (Current candle confirms the reversal)
    # We check the most recent completed candle (index -1)
    displacement_up = raided_lows.shift(1) & (df['close'] > df['high'].shift(1))
    displacement_down = raided_highs.shift(1) & (df['close'] < df['low'].shift(1))

    if displacement_up.iloc[-1]:
        return "🚀 **BULLISH MANIPULATION DETECTED**\nLevel: Liquidity below support cleared.\nStatus: Displacement Up (Retail Trapped)."
    elif displacement_down.iloc[-1]:
        return "⚠️ **BEARISH MANIPULATION DETECTED**\nLevel: Liquidity above resistance cleared.\nStatus: Displacement Down (Retail Trapped)."
    return None

def run_check():
    exchange = ccxt.binance()
    try:
        bars = exchange.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
        
        signal = identify_manipulation_move(df)
        
        if signal:
            payload = {"content": f"**[Market Process Update]**\nAsset: {SYMBOL}\n{signal}"}
            requests.post(DISCORD_WEBHOOK_URL, json=payload)
            print("Signal sent to Discord.")
        else:
            print("No manipulation sequence confirmed at this time.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_check()
