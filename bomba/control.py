import time
import paho.mqtt.client as mqtt
import os
import RPi.GPIO as GPIO
import random
from datetime import datetime
import threading
from pprint import pprint
import keyring

from bomb_control.sm import ControlSM

SETTING_TIME_S = 80

events = {
    'start': False,
    'stop': True,
}

sleeps_per_state = {
    "init": 1,
    "start": 1,
    "started": 1,
    "stop": 5,
    "stopping": 5,
    "stopped": 600
}


class BombaReal():
    started = False
    stopped = False
    start_time = None
    stop_time = None
    client = None
    RELAY_PIN = 4
    last_pressure = 0
    last_current_ph1 = 0
    last_current_ph2 = 0

    def __init__(self):
        # GPIO Setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.RELAY_PIN, GPIO.OUT)

    def get_pressure_psi(self):
        if self.started:
            return 70
        else:
            return 0

    def get_phase1_current_A(self):
        if self.started:
            return 17
        else:
            return 0

    def get_phase2_current_A(self):
        if self.started:
            return 17
        else:
            return 0

    def relay_signal_set(self, value):
        if value:
            GPIO.output(self.RELAY_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.RELAY_PIN, GPIO.LOW)

    def get_run_time(self):
        if self.started:
            return datetime.now() - self.start_time
        else:
            return None

    def start(self):
        self.started = True
        self.stopped = False
        self.relay_signal_set(True)
        self.start_time = datetime.now()

    def stop(self):
        self.last_pressure = self.get_pressure_psi()
        self.last_current_ph1 = self.get_phase1_current_A()
        self.last_current_ph2 = self.get_phase2_current_A()

        self.started = False
        self.stopped = True
        self.relay_signal_set(False)
        self.stop_time = datetime.now()


def model_state_machine(obj):
    current_inc = 17 / SETTING_TIME_S
    pressure_inc = 70 / SETTING_TIME_S
    while True:
        if obj.steady_state:
            obj.pressure = random.uniform(70 *0.95,
                                          70*1.05)
            obj.current_ph1 = random.uniform(17 *0.95,
                                             17*1.05)
            obj.current_ph2 = random.uniform(17 *0.95,
                                             17*1.05)

        if obj.started:
            obj.pressure = obj.pressure + pressure_inc
            obj.current_ph1 = obj.current_ph1 + current_inc
            obj.current_ph2 = obj.current_ph2 + current_inc
            if obj.pressure > 70:
                obj.steady_state = True

        if obj.stopped:
            obj.steady_state = False
            obj.pressure = max(obj.pressure - pressure_inc, 0)
            obj.current_ph1 = max(obj.current_ph1 - current_inc, 0)
            obj.current_ph2 = max(obj.current_ph2 - current_inc, 0)

        time.sleep(1)


class BombaModelo(BombaReal):
    thread = None
    steady_state = False
    pressure = 0
    current_ph1 = 0
    current_ph2 = 0

    def __init__(self) -> None:
        self.thread = threading.Thread(target=model_state_machine, args=(self,))
        self.thread.start()

    def relay_signal_set(self, value):
        pass

    def get_pressure_psi(self):
        return self.pressure

    def get_phase1_current_A(self):
        return self.current_ph1

    def get_phase2_current_A(self):
        return self.current_ph2


# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 8883))
username = os.environ.get('MQTT_USERNAME')
ca_certs_path = os.environ.get('MQTT_CA_CERTS')
actuator_topic = "actuators/bomba"

try:
    password = keyring.get_password("MQTT", username)
    if password:
        print("Password already stored.")
    else:
        password = input("Enter MQTT password: ")
        keyring.set_password("MQTT", username, password)
        print("Password stored successfully.")
except keyring.errors.KeyringError as e:
    print(f"Error accessing keyring: {e}")
    raise e

bomba = BombaModelo()

BOMB_ON_SLEEP_TIME = 5
BOMB_TURNING_OFF_SLEEP_TIME = 10
BOMB_OFF_SLEEP_TIME = 60
SLEEP_TIME = BOMB_OFF_SLEEP_TIME

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")
if not username or not password:
    raise ValueError("MQTT_USERNAME and MQTT_PASSWORD environment variables are required")
if not ca_certs_path:
    raise ValueError("MQTT_CA_CERTS environment variable is required")


# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker with SSL")
        client.subscribe(actuator_topic)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    global events
    payload = msg.payload.decode()
    if payload == "ON":
        events['start'] = True
        print(f"{datetime.now()} Digital signal turned ON")
    elif payload == "OFF":
        events['stop'] = True
        print(f"{datetime.now()} Digital signal turned OFF")


def wait_next_iteration():
    global SLEEP_TIME
    for i in range(SLEEP_TIME):
        time.sleep(1)
        if bomba.started:
            break

    if bomba.stopped:
        SLEEP_TIME = BOMB_OFF_SLEEP_TIME


def publish_data(state, sleeps_per_state, client):
    global SLEEP_TIME

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


sm = ControlSM(bomba)

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
    pprint(state)
    time.sleep(15)
