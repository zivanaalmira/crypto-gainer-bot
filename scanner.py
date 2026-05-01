import requests
import time
import os
from datetime import datetime

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# List koin yang ada di Ajaib per Okt 2025. Update manual kalau ada listing baru
KOIN_AJAIB = [
    'btc_idr', 'eth_idr', 'bnb_idr', 'sol_idr', 'usdt_idr', 'xrp_idr', 'doge_idr',
    'pepe_idr', 'shib_idr', 'avax_idr', 'dot_idr', 'link_idr', 'matic_idr', 'ada_idr',
    'atom_idr', 'near_idr', 'arb_idr', 'op_idr', 'sui_idr', 'sei_idr', 'wld_idr', 'ton_idr'
]

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram token/chat_id kosong")
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        res = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        if res.status_code == 200:
            print("Sukses kirim ke Telegram")
        else:
            print(f"Gagal kirim Telegram: {res.text}")
    except Exception as e:
        print(f"Gagal kirim Telegram: {e}")

def scan_indodax():
    url = "https://indodax.com/api/tickers"
    try:
        r = requests.get(url, timeout=10)
        data = r.json()['tickers']
    except Exception as e:
        send_telegram(f"Gagal ambil data Indodax: {e}")
        return

    sinyal_ditemukan = 0
    for pair in KOIN_AJAIB:
        if pair not in data: continue

        d = data[pair]
        try:
            harga = float(d['last'])
            high = float(d['high'])
            low = float(d['low'])
            vol_idr = float(d['vol_idr'])

            # Skip koin sepi. Minimal volume 500jt biar gampang jual-beli di Ajaib
            if vol_idr < 500000000: continue

            naik_dari_low = (harga / low - 1) * 100
            jarak_ke_high = (1 - harga / high) * 100

            # Sinyal: Naik >3.5% dari low 24h + harga udah nempel high 24h
            # Artinya koin ini lagi breakout dan berpotensi lanjut jadi top gainer
            if naik_dari_low > 3.5 and jarak_ke_high < 1.5:
                coin = pair.replace('_idr','').upper()
                msg = f"🚀 *{coin}/IDR*\nHarga: `Rp{harga:,.0f}`\nNaik dari Low: `{naik_dari_low:.1f}%`\nSisa ke High 24h: `{jarak_ke_high:.1f}%`\nVol 24h: `Rp{vol_idr/1e9:.1f}M`\n\n*Potensi breakout. Cek Ajaib sekarang!*"
                send_telegram(msg)
                sinyal_ditemukan += 1

        except Exception as e:
            print(f"Error {pair}: {e}")
        time.sleep(0.1)

    if sinyal_ditemukan == 0:
        print(f"{datetime.now()}: Scan selesai. Belum ada sinyal breakout.")
    else:
        print(f"{datetime.now()}: Scan selesai. {sinyal_ditemukan} sinyal dikirim.")

scan_indodax()
