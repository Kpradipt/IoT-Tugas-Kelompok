"""HP B virtual untuk Windows: menerima perintah alarm dan membunyikan suara."""

import json
import time
import winsound

from common import client, connect, publish, topic


def on_connect(c, userdata, flags, reason_code, properties):
    if reason_code == 0:
        c.subscribe(topic('commands/hp_b'), qos=1)
        print('HP B siap menerima alarm.', flush=True)
    else:
        print('MQTT gagal:', reason_code, flush=True)


def on_message(c, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        if data.get('command') != 'ALARM_ON':
            return

        print('\n' + '!' * 44, flush=True)
        print('SMARTWAKE: WAKTUNYA BANGUN!', data.get('reason', ''), flush=True)
        print('!' * 44 + '\n', flush=True)

        # Bunyi alarm dari speaker laptop
        for _ in range(5):
            winsound.Beep(1200, 700)
            time.sleep(0.2)

        publish(c, 'status/hp_b', {
            'status': 'ALARM_RECEIVED',
            'issued_at': data.get('issued_at')
        })

    except Exception as exc:
        print('Gagal menangani alarm:', exc, flush=True)


c = client('hpb')
c.on_connect = on_connect
c.on_message = on_message

connect(c)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('\nHP B dihentikan.', flush=True)
finally:
    c.loop_stop()
    c.disconnect()