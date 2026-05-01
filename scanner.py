import requests
import os
import json
from datetime import datetime
from pathlib import Path

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Settingan
MIN_VOLUME_IDR = 1000000000 # Minimal volume 1 Miliar
PAIR_WAJIB_SKIP = ['usdt_idr', 'usdc_idr']
NAIK_PERSEN_ALERT = 1.0 # Alert kalau naik >1% per 5 menit
HARGA_FILE = "harga_sebelumnya.json" # File buat nyimpen harga terakhir

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

def load_harga_lama():
    if Path(HARGA_FILE).exists():
        with open(HARGA_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_harga_baru(data_harga):
    with open(HARGA_FILE, 'w') as f:
        json.dump(data_harga, f)

def scan_indodax():
    try:
        data = requests.get("https://indodax.com/api/tickers", timeout=10).json()['tickers']
    except Exception as e:
        send_telegram(f"Gagal ambil data Indodax: {e}")
        return

    harga_lama = load_harga_lama()
    harga_baru = {}
    sinyal_top_gainer = []
    sinyal_fast_mover = []
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
        coin = pair.replace('_idr','').upper()

        # Simpan harga sekarang buat dibandingin 5 menit lagi
        harga_baru[pair] = harga

        # --- MODE 1: SCAN TOP GAINER ---
        naik_dari_low = (harga / low - 1) * 100
        jarak_ke_high = (1 - harga / high) * 100
        if naik_dari_low > 3.5 and jarak_ke_high < 5:
            baris = f"{coin} | Price: Rp{harga:,.0f} | Naik: {naik_dari_low:.1f}%".replace('.', ',')
            sinyal_top_gainer.append(baris)

        # --- MODE 2: SCAN FAST MOVER 5 MENIT ---
        if pair in harga_lama:
            harga_5_menit_lalu = harga_lama[pair]
            naik_5_menit = (harga / harga_5_menit_lalu - 1) * 100
            if naik_5_menit >= NAIK_PERSEN_ALERT:
                baris = f"{coin} | Rp{harga_5_menit_lalu:,.0f} → Rp{harga:,.0f} | +{naik_5_menit:.1f}% / 5m".replace('.', ',')
                sinyal_fast_mover.append(baris)

    # Simpan harga baru ke file
    save_harga_baru(harga_baru)

    # Gabungin semua sinyal jadi 1 pesan
    semua_pesan = []
    if sinyal_top_gainer:
        semua_pesan.append("ZIVANA NEW ACTION | 🚀 *SCAN TOP GAINER*")
        semua_pesan.extend(sinyal_top_gainer)

    if sinyal_fast_mover:
        if semua_pesan: semua_pesan.append("") # Kasih spasi
        semua_pesan.append("ZIVANA NEW ACTION | ⚡ *FAST MOVER 5 MENIT*")
        semua_pesan.extend(sinyal_fast_mover)

    if semua_pesan:
        pesan_final = "\n".join(semua_pesan)
        send_telegram(pesan_final)
        print(f"{datetime.now()}: Scan {total_scan} koin. {len(sinyal_top_gainer)} top gainer, {len(sinyal_fast_mover)} fast mover.")
    else:
        print(f"{datetime.now()}: Scan {total_scan} koin. Belum ada sinyal.")

scan_indodax()
