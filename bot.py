import ccxt
import os
import pandas as pd
import requests

SYMBOL = 'BTC/USDT'
TIMEFRAME = '1h'
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def identify_manipulation_move(df):
    # Phase 1: The Build
    lookback = 20
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # Phase 2 & 3: The Raid
    raided_lows = (df['low'] < df['lowest_prev']) & (df['close'] > df['lowest_prev'])
    raided_highs = (df['high'] > df['highest_prev']) & (df['close'] < df['highest_prev'])
    
    # Phase 4: Displacement
    displacement_up = raided_lows.shift(1) & (df['close'] > df['high'].shift(1))
    displacement_down = raided_highs.shift(1) & (df['close'] < df['low'].shift(1))

    if displacement_up.iloc[-1]:
        return "🚀 **BULLISH MANIPULATION**\nLiquidity below support cleared.\nStatus: Displacement Up."
    elif displacement_down.iloc[-1]:
        return "⚠️ **BEARISH MANIPULATION**\nLiquidity above resistance cleared.\nStatus: Displacement Down."
    return None

def run_check():
    # List of exchanges to try to bypass regional blocks
    exchanges_to_try = [ccxt.kraken(), ccxt.kucoin(), ccxt.gateio()]
    
    success = False
    for exchange in exchanges_to_try:
        try:
            print(f"Attempting to fetch data from {exchange.id}...")
            # Some exchanges use BTC/USDT, others BTC/USD. Kraken prefers BTC/USD.
            target_symbol = SYMBOL if exchange.id != 'kraken' else 'BTC/USD'
            
            bars = exchange.fetch_ohlcv(target_symbol, timeframe=TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
            
            signal = identify_manipulation_move(df)
            
            if signal:
                payload = {"content": f"**[Market Process Update]**\nSource: {exchange.id}\nAsset: {target_symbol}\n{signal}"}
                requests.post(DISCORD_WEBHOOK_URL, json=payload)
                print(f"Signal sent via {exchange.id}")
            else:
                print(f"No manipulation sequence on {exchange.id}.")
            
            success = True
            break # Exit the loop if successful
            
        except Exception as e:
            print(f"Could not connect to {exchange.id}: {e}")
            continue

    if not success:
        print("All exchange attempts failed due to regional restrictions.")

if __name__ == "__main__":
    run_check()
