import time
import paho.mqtt.client as mqtt
import os
from datetime import datetime
import threading
from pprint import pprint
import keyring

from bomb_control.sm import ControlSM
from bomb_control.bombs import BombaModelo

sleeps_per_state = {
    "init": 1,
    "start": 1,
    "started": 1,
    "stop": 5,
    "stopping": 5,
    "stopped": 600
}

# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 8883))
username = os.environ.get('MQTT_USERNAME')
ca_certs_path = os.environ.get('MQTT_CA_CERTS')
actuator_topic = "actuators/bomba"

password = keyring.get_password("MQTT", username)
if not password:
    password = keyring.get_password("MQTT", username)
    print(password)

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")
if not username or not password:
    raise ValueError("MQTT_USERNAME and MQTT_PASSWORD environment variables are required")
if not ca_certs_path:
    raise ValueError("MQTT_CA_CERTS environment variable is required")

bomba = BombaModelo()

sm = ControlSM(bomba)
sm.start()


# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker with SSL")
        client.subscribe(actuator_topic)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    global sm
    payload = msg.payload.decode()
    if payload == "ON":
        sm.events['start'] = True
        print(f"{datetime.now()} Digital signal turned ON")
    elif payload == "OFF":
        sm.events['stop'] = True
        print(f"{datetime.now()} Digital signal turned OFF")


def publish_data(state, sleeps_per_state, client):
    while True:
        pressure = state['pressure']
        payload = f'{{"value": {float(pressure)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-water-pressure"}}'
        client.publish("sensors/bomb/water_pressure", payload)

        cph1 = state['current_ph1']
        payload = f'{{"value": {float(cph1)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph1"}}'
        client.publish("sensors/bomb/current_ph1", payload)

        cph2 = state['current_ph2']
        payload = f'{{"value": {float(cph2)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph2"}}'
        client.publish("sensors/bomb/current_ph1", payload)

        print(f"{datetime.now()} Publishing: {pressure} psi, {cph1} A, {cph2} B")

        for i in range(sleeps_per_state[state['sm_state']]):
            if i > sleeps_per_state[state['sm_state']]:
                break
            time.sleep(1)


# MQTT Client Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Set username and password for authentication
client.username_pw_set(username, password)

# Configure SSL/TLS context (only CA certificate)
client.tls_set(ca_certs=ca_certs_path)

# Connect to MQTT Broker
client.connect(broker_address, broker_port)

publisher = threading.Thread(target=publish_data, args=(sm.state, sleeps_per_state, client))
publisher.start()

# Start the MQTT client's network loop in a separate thread
client.loop_start()

while True:
    pprint(sm.state)
    time.sleep(15)
