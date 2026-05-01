import requests
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# GANTI BAGIAN INI
MIN_VOLUME_IDR = 1000000000  # Minimal 1 Miliar biar ga koin micin
PAIR_WAJIB_SKIP = ['usdt_idr', 'usdc_idr'] # Koin stable, skip aja

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID: return
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", 
                  json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)

def scan_indodax():
    try:
        data = requests.get("https://indodax.com/api/tickers", timeout=10).json()['tickers']
    except Exception as e:
        send_telegram(f"Gagal ambil data Indodax: {e}")
        return

    sinyal_ditemukan = 0
    # Loop semua koin IDR, ga perlu tulis manual
    for pair, d in data.items():
        if not pair.endswith('_idr'): continue
        if pair in PAIR_WAJIB_SKIP: continue
        
        vol_idr = float(d['vol_idr'])
        if vol_idr < MIN_VOLUME_IDR: continue # Skip koin sepi

        harga = float(d['last'])
        high = float(d['high'])
        low = float(d['low'])

        naik_dari_low = (harga / low - 1) * 100
        jarak_ke_high = (1 - harga / high) * 100

        if naik_dari_low > 3.5 and jarak_ke_high < 1.5:
            coin = pair.replace('_idr','').upper()
            msg = f"🚀 *{coin}/IDR*\nHarga: `Rp{harga:,.0f}`\nNaik dari Low: `{naik_dari_low:.1f}%`\nSisa ke High: `{jarak_ke_high:.1f}%`\nVol: `Rp{vol_idr/1e9:.1f}M`"
            send_telegram(msg)
            sinyal_ditemukan += 1
        
    print(f"{datetime.now()}: Scan {len(data)} pair. {sinyal_ditemukan} sinyal dikirim.")

scan_indodax()
