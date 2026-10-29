"""Simulator HP A: data sintetis untuk pengembangan TANPA sensor fisik."""
import argparse, random, time
from datetime import datetime, timezone
from common import client, connect, publish

p = argparse.ArgumentParser()
p.add_argument('--interval', type=float, default=3)
p.add_argument('--seed', type=int, default=7)
args = p.parse_args()
random.seed(args.seed)
c = client('hpa')
connect(c)
print('HP A simulator terhubung; Ctrl+C untuk berhenti.')
sequence = 0
try:
    while True:
        # 4 sampel tenang, lalu 4 sampel banyak gerakan; data lux sintetis
        phase = (sequence // 4) % 2
        motion_rms = round(random.uniform(0.06, 0.20) if phase == 0 else random.uniform(0.85, 1.50), 3)
        lux = round(random.uniform(1, 5) if phase == 0 else random.uniform(8, 22), 2)
        packet = {'device_id': 'hp_a', 'sequence': sequence, 'motion_rms': motion_rms,
                  'light_lux': lux, 'simulation': True, 'sent_at': datetime.now(timezone.utc).isoformat()}
        publish(c, 'telemetry/hp_a', packet)
        print('Kirim:', packet)
        sequence += 1
        time.sleep(args.interval)
except KeyboardInterrupt:
    pass
finally:
    c.loop_stop(); c.disconnect()
