import ccxt
import os
import pandas as pd
import requests
import time
from datetime import datetime
import numpy as np

# --- CONFIGURATION ---
SYMBOLS = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'XRP/USDT', 'ADA/USDT', 
           'DOGE/USDT', 'SOL/USDT', 'LINK/USDT', 'SUI/USDT', 'POL/USDT']
TIMEFRAMES = ['1h', '4h', '1d']
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

def get_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def is_killzone():
    """Checks if the current UTC time falls within London or NY Open"""
    now_utc = datetime.utcnow().hour
    # London Open (07:00-10:00 UTC) | NY Open (13:00-16:00 UTC)
    return (7 <= now_utc <= 10) or (13 <= now_utc <= 16)

def identify_phases(df, tf, symbol):
    if len(df) < 30: return None
    
    # Technical Indicators
    df['rsi'] = get_rsi(df['close'])
    df['avg_vol'] = df['vol'].rolling(window=10).mean()
    
    lookback = 20
    df['lowest_prev'] = df['low'].shift(1).rolling(window=lookback).min()
    df['highest_prev'] = df['high'].shift(1).rolling(window=lookback).max()
    
    # 1. THE BUILD (Phase 1)
    threshold = 0.0015
    is_eql = abs(df['low'].iloc[-1] - df['lowest_prev'].iloc[-1]) < (df['close'].iloc[-1] * threshold)
    is_eqh = abs(df['high'].iloc[-1] - df['highest_prev'].iloc[-1]) < (df['close'].iloc[-1] * threshold)
    
    # 2 & 3. THE RAID (Phase 2/3)
    # Check if the previous candle performed the raid
    raided_low = (df['low'].iloc[-2] < df['lowest_prev'].iloc[-2]) and (df['close'].iloc[-2] > df['lowest_prev'].iloc[-2])
    raided_high = (df['high'].iloc[-2] > df['highest_prev'].iloc[-2]) and (df['close'].iloc[-2] < df['highest_prev'].iloc[-2])
    
    # 4. DISPLACEMENT (Phase 4) + UPGRADES
    # Logic: Raid happened + Price breaks high/low + High Volume + Killzone
    vol_confirmation = df['vol'].iloc[-1] > (df['avg_vol'].iloc[-1] * 1.3)
    active_timing = is_killzone()
    
    # Bullish Displacement
    if raided_low and df['close'].iloc[-1] > df['high'].iloc[-2]:
        msg = f"🚀 **INSTITUTIONAL BUY SIGNAL ({tf})**\nAsset: {symbol}\n"
        if vol_confirmation: msg += "✅ High Volume Commitment\n"
        if active_timing: msg += "✅ Within Session Killzone\n"
        if df['rsi'].iloc[-1] < 40: msg += "✅ Oversold Recovery (Divergence Risk Low)\n"
        return msg

    # Bearish Displacement
    if raided_high and df['close'].iloc[-1] < df['low'].iloc[-2]:
        msg = f"⚠️ **INSTITUTIONAL SELL SIGNAL ({tf})**\nAsset: {symbol}\n"
        if vol_confirmation: msg += "✅ High Volume Commitment\n"
        if active_timing: msg += "✅ Within Session Killzone\n"
        if df['rsi'].iloc[-1] > 60: msg += "✅ Overbought Recovery\n"
        return msg

    # Build Warning
    if is_eql or is_eqh:
        level_type = "Support (EQL)" if is_eql else "Resistance (EQH)"
        return f"🧱 **BUILD DETECTED ({tf})**\nAsset: {symbol}\nLevel: Engineered {level_type}.\n*Action: Stand by for the Raid.*"

    return None

def run_check():
    exchanges = [ccxt.bybit(), ccxt.bitget(), ccxt.kraken()]
    
    for symbol in SYMBOLS:
        for tf in TIMEFRAMES:
            for exchange in exchanges:
                try:
                    target_symbol = symbol if exchange.id != 'kraken' else symbol.replace('USDT', 'USD')
                    bars = exchange.fetch_ohlcv(target_symbol, timeframe=tf, limit=100)
                    df = pd.DataFrame(bars, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
                    
                    alert = identify_phases(df, tf, symbol)
                    if alert:
                        payload = {"username": "OMNI-PRO", "content": alert}
                        requests.post(DISCORD_WEBHOOK_URL, json=payload)
                    break 
                except:
                    continue
            time.sleep(1)

if __name__ == "__main__":
    run_check()
