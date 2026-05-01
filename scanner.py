import requests
import time
import pandas as pd
from datetime import datetime
import os

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token/chat_id kosong")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def get_all_symbols():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    headers = {'User-Agent': 'Mozilla/5.0'}  # Penting: biar ga dikira bot
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        # Cek kalau Binance ngasih error
        if isinstance(data, dict) and 'code' in data:
            send_telegram(f"Binance Error: {data.get('msg', 'Unknown')}")
            return [], []
            
        if not isinstance(data, list):
            send_telegram("Binance response bukan list. Mungkin IP diblokir.")
            return [], []
            
        symbols = [d['symbol'] for d in data if 'USDT' in d['symbol'] 
                   and d['symbol'] not in ['USDCUSDT','BUSDUSDT','TUSDUSDT','FDUSDUSDT']
                   and float(d.get('quoteVolume', 0)) > 2000000]
        return symbols, data
    except Exception as e:
        print(f"Error get_all_symbols: {e}")
        send_telegram(f"Gagal ambil data Binance: {e}")
        return [], []

def scan_gainers():
    symbols, data_24h = get_all_symbols()
    if not symbols:
        print("Tidak ada symbol yang didapat. Skip scan.")
        return
        
    candidates = []
    for symbol in symbols[:60]:  # Kurangi jadi 60 biar ga timeout
        try:
            url = "https://api.binance.com/api/v3/klines"
            headers = {'User-Agent': 'Mozilla/5.0'}
            params = {"symbol": symbol, "interval": "5m", "limit": 13}
            r = requests.get(url, headers=headers, params=params, timeout=10)
            klines = r.json()
            
            if not isinstance(klines, list):
                continue
                
            df = pd.DataFrame(klines, columns=['time','open','high','low','close','volume','c','q','t','tb','tq','ig'])
            df['close'] = df['close'].astype(float)
            df['volume'] = df['volume'].astype(float)
            
            last_vol = df['volume'].iloc[-1]
            avg_vol = df['volume'].iloc[-12:-1].mean()
            if avg_vol == 0: continue
            
            price_change_5m = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
            
            if last_vol > avg_vol * 4 and price_change_5m > 2:
                info = next((d for d in data_24h if d['symbol'] == symbol), {})
                msg = f"🚀 *{symbol}*\nHarga: `${float(df['close'].iloc[-1]):.4f}`\nNaik 5m: `{price_change_5m:.2f}%`\nVol Spike: `{last_vol/avg_vol:.1f}x`\nCek Ajaib: `{symbol.replace('USDT','')}`"
                send_telegram(msg)
                candidates.append(symbol)
        except Exception as e: 
            print(f"Error {symbol}: {e}")
        time.sleep(0.3)  # Naikin delay biar aman dari rate limit
    
    if not candidates:
        print(f"{datetime.now()}: Tidak ada sinyal")
    
scan_gainers()
