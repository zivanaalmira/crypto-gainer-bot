import requests
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Settingan - Bisa kamu ubah
MIN_VOLUME_IDR = 1000000000  # Minimal volume 1 Miliar biar ga koin micin
PAIR_WAJIB_SKIP = ['usdt_idr', 'usdc_idr'] # Skip stablecoin

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Telegram token/chat_id kosong. Cek GitHub Secrets.")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        res = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        if res.status_code == 200:
            print("Sukses kirim ke Telegram")
        else:
            print(f"Gagal kirim Telegram: {res.text}")
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def scan_indodax():
    try:
        data = requests.get("https://indodax.com/api/tickers", timeout=10).json()['tickers']
    except Exception as e:
        send_telegram(f"Gagal ambil data Indodax: {e}")
        return

    sinyal_list = []
    total_scan = 0
    
    for pair, d in data.items():
        if not pair.endswith('_idr'): continue
        if pair in PAIR_WAJIB_SKIP: continue
        
        vol_idr = float(d['vol_idr'])
        if vol_idr < MIN_VOLUME_IDR: continue
        total_scan += 1

        harga = float(d['last'])
        high = float(d['high'])
        low = float(d['low'])

        # Rumus sinyal: naik >3.5% dari low 24h + harga udah nempel high 24h
        naik_dari_low = (harga / low - 1) * 100
        jarak_ke_high = (1 - harga / high) * 100

        if naik_dari_low > 3.5 and jarak_ke_high < 1.5:
            coin = pair.replace('_idr','').upper()
            baris = f"{coin} | Price: Rp{harga:,.0f} | Naik: {naik_dari_low:.1f}%".replace('.', ',')
            sinyal_list.append(baris)
        
    # Kirim 1x aja, semua koin dijadiin 1 pesan
    if sinyal_list:
        pesan_final = "\n".join(sinyal_list)
        send_telegram(pesan_final)
        print(f"{datetime.now()}: Scan {total_scan} koin. {len(sinyal_list)} sinyal dikirim.")
    else:
        print(f"{datetime.now()}: Scan {total_scan} koin. Belum ada sinyal.")

scan_indodax()
