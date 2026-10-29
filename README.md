# SmartWake — MVP IoT (mode simulasi)

Versi awal tanpa sensor fisik. Semua komponen berkomunikasi melalui broker publik MQTT over TLS (port 8883). Terinspirasi dari alur PocketGuard contoh mata kuliah, tetapi implementasi dibuat terpisah.

## Instalasi

Python 3.10+ (disarankan 3.11+) dan internet diperlukan.

```bash
python -m pip install -r requirements.txt
cp .env.example .env
```

Di Windows PowerShell: `Copy-Item .env.example .env`.

**WAJIB** ubah `PROJECT_ID` dalam `.env` menjadi unik, dan samakan di semua perangkat.

Buka tiga terminal, dalam folder yang sama:

1. `python hp_b_alarm.py`
2. `python server.py --demo`
3. `python hp_a_simulator.py --interval 3`

Sekitar sampel aktif kedua, server mengirim alarm (biasanya setelah 15-25 detik). `--demo` mengabaikan jendela alarm, tetapi hanya sekali per hari per proses server. Hentikan dengan Ctrl+C.

## Mode asli (bukan demo)

Jalankan `python server.py` tanpa `--demo`. Ubah jendela bangun di `.env` (format 24 jam). **Catatan:** mekanisme fallback pada versi ini hanya untuk jendela dalam satu hari, tanpa melintasi tengah malam, dan memerlukan sedikitnya satu telemetri diterima. Untuk versi produksi, jadwal, retry, watchdog dan alarm lokal perlu diperkuat.

## Bagian proyek

- `hp_a_simulator.py`: membuat data **sintetis**, bukan pembacaan sensor fisik. Saat sensor tersedia, ganti generator sampel dengan pembacaan accelerometer dan lux.
- `server.py`: proses 1 = klasifikasi aktivitas dari RMS, proses 2 = smoothing lux 5 sampel; rule-based aktivasi alarm.
- `hp_b_alarm.py`: menerima perintah MQTT, berbunyi/getar bila Termux:API tersedia, mengirim ack.
- `common.py`: koneksi MQTT over TLS.

## Catatan keamanan & batasan

Jangan kirim informasi pribadi ke broker MQTT publik. Topic bisa dibaca/ditulis pihak lain. Ini **prototipe edukasi**, bukan alarm yang dapat diandalkan untuk bangun wajib. Jika internet/server berhenti, alarm mungkin tidak aktif. HP B nanti perlu alarm cadangan lokal.

Nilai RMS rendah/tinggi hanyalah indikator aktivitas gerak, **bukan diagnosis fase tidur**. Pemrosesan lux belum mempengaruhi keputusan alarm; tetap merupakan jenis pemrosesan kedua dan ditampilkan di log.
