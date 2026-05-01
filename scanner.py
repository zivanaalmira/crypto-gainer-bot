import requests
import time
import pandas as pd
from datetime import datetime
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')  # Ambil dari GitHub Secrets
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

def get_all_symbols():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    data = requests.get(url).json()
    symbols = [d['symbol'] for d in data if 'USDT' in d['symbol'] 
               and d['symbol'] not in ['USDCUSDT','BUSDUSDT','TUSDUSDT','FDUSDUSDT']
               and float(d['quoteVolume']) > 2000000]
    return symbols, data

def scan_gainers():
    symbols, data_24h = get_all_symbols()
    candidates = []
    for symbol in symbols[:80]: # Limit biar ga timeout di GitHub
        try:
            klines = requests.get(f"https://api.binance.com/api/v3/klines",
                                  params={"symbol": symbol, "interval": "5m", "limit": 13}).json()
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','volume','c','q','t','tb','tq','ig'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            last_vol = df['volume'].iloc[-1]
            avg_vol = df['volume'].iloc[-12:-1].mean()
            price_change_5m = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
            
            if last_vol > avg_vol * 4 and price_change_5m > 2:
                info = next((d for d in data_24h if d['symbol'] == symbol), None)
                msg = f"🚀 *{symbol}*\nHarga: `${float(df['close'].iloc[-1]):.4f}`\nNaik 5m: `{price_change_5m:.2f}%`\nVol Spike: `{last_vol/avg_vol:.1f}x`\nCek Ajaib: `{symbol.replace('USDT','')}`"
                send_telegram(msg)
                candidates.append(symbol)
        except Exception as e: 
            print(f"Error {symbol}: {e}")
        time.sleep(0.2)
    
    if not candidates:
        print(f"{datetime.now()}: Tidak ada sinyal")
    
scan_gainers()
