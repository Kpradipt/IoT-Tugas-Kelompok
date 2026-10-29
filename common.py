import json, os, ssl
from pathlib import Path
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

load_dotenv(Path(__file__).with_name('.env'))
PROJECT = os.getenv('PROJECT_ID', 'smartwake_demo_ganti_id')
HOST = os.getenv('MQTT_HOST', 'broker.hivemq.com')
PORT = int(os.getenv('MQTT_PORT', '8883'))
BASE = f'smartwake/{PROJECT}'

def topic(name):
    return f'{BASE}/{name}'

def client(name):
    c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f'{PROJECT}_{name}_{os.getpid()}')
    c.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    return c

def connect(c):
    c.connect(HOST, PORT, keepalive=60)
    c.loop_start()

def publish(c, name, obj):
    info = c.publish(topic(name), json.dumps(obj), qos=1, retain=False)
    info.wait_for_publish(timeout=5)
