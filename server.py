"""Server rule-based SmartWake: dua proses: smoothing cahaya dan analisis RMS gerakan."""
import argparse, json, os, time
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from common import client, connect, publish, topic

p = argparse.ArgumentParser()
p.add_argument('--demo', action='store_true', help='Lewati batas jendela bangun untuk demo')
args = p.parse_args()
WINDOW_START = os.getenv('WAKE_WINDOW_START', '05:30')
WINDOW_END = os.getenv('WAKE_WINDOW_END', '06:00')
MOTION_THRESHOLD = float(os.getenv('MOTION_THRESHOLD', '0.7'))
MIN_ACTIVE_SAMPLES = int(os.getenv('MIN_ACTIVE_SAMPLES', '2'))
TZ = ZoneInfo(os.getenv('TIMEZONE', 'Asia/Jakarta'))
light_history = deque(maxlen=5)
active_streak = 0
last_alarm_date = None
last_packet_time = None
last_lux_avg = None

def in_window(hhmm, start, end):
    # Menangani jendela lintas tengah malam
    return start <= hhmm <= end if start <= end else (hhmm >= start or hhmm <= end)

def send_alarm(reason):
    global last_alarm_date
    now = datetime.now(TZ)
    if last_alarm_date == now.date().isoformat():
        return
    payload = {'command': 'ALARM_ON', 'reason': reason, 'issued_at': now.isoformat()}
    publish(mqtt_client, 'commands/hp_b', payload)
    last_alarm_date = now.date().isoformat()
    print('ALARM dikirim:', payload, flush=True)

def on_connect(c, userdata, flags, reason_code, properties):
    if reason_code == 0:
        c.subscribe(topic('telemetry/hp_a'), qos=1)
        c.subscribe(topic('status/hp_b'), qos=1)
        print('Server terhubung dan subscribe.', flush=True)
    else:
        print('MQTT gagal:', reason_code, flush=True)

def on_message(c, userdata, msg):
    global active_streak, last_packet_time, last_lux_avg
    try:
        data = json.loads(msg.payload.decode())
        if msg.topic == topic('status/hp_b'):
            print('Status HP B:', data, flush=True)
            return
        motion = float(data['motion_rms'])
        lux = float(data['light_lux'])
        if not (0 <= motion < 100 and 0 <= lux < 200000):
            return
        last_packet_time = time.monotonic()
        light_history.append(lux)
        last_lux_avg = round(sum(light_history) / len(light_history), 2)
        # Processing 1: klasifikasi aktivitas berdasarkan RMS, 2 sampel berturut-turut.
        active_streak = active_streak + 1 if motion >= MOTION_THRESHOLD else 0
        # Processing 2: smoothing intensitas cahaya (rata-rata bergerak).
        state = 'AKTIF / TERINDIKASI BANYAK GERAK' if motion >= MOTION_THRESHOLD else 'TENANG'
        now = datetime.now(TZ)
        allowed = args.demo or in_window(now.strftime('%H:%M'), WINDOW_START, WINDOW_END)
        print(f'RMS={motion:.2f} lux={lux:.1f} lux_avg={last_lux_avg} '
              f'status={state} streak={active_streak} window={allowed}', flush=True)
        # Data cahaya dipakai untuk konteks dan pelaporan, tidak dijadikan bukti fase tidur.
        if allowed and active_streak >= MIN_ACTIVE_SAMPLES:
            send_alarm('Aktivitas gerakan meningkat dalam jendela bangun')
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print('Data telemetri tidak valid:', exc, flush=True)

mqtt_client = client('server')
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
connect(mqtt_client)
print('SmartWake server aktif. Demo:', args.demo, '| jendela:', WINDOW_START, '-', WINDOW_END, flush=True)
try:
    while True:
        now = datetime.now(TZ)
        # Cadangan: bunyikan alarm di akhir jendela meskipun gerak belum terdeteksi.
        if not args.demo and WINDOW_START <= WINDOW_END:
            end_hour, end_minute = map(int, WINDOW_END.split(':'))
            end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            recent_telemetry = last_packet_time is not None and time.monotonic() - last_packet_time < 120
            if timedelta(0) <= now - end_time <= timedelta(minutes=2) and recent_telemetry:
                send_alarm('Batas akhir waktu bangun tercapai')
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    mqtt_client.loop_stop(); mqtt_client.disconnect()
