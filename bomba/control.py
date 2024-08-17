import time
import paho.mqtt.client as mqtt
import os
import RPi.GPIO as GPIO
import random
from datetime import datetime

SETTING_TIME_S = 80


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


class BombaModelo(BombaReal):

    def __init__(self) -> None:
        pass

    def relay_signal_set(self, value):
        pass

    def get_variable(self, steady_state_val, last_val):
        global SETTING_TIME_S
        # Calculate the time delta
        now = datetime.now()

        if self.started:
            delta_since_started = now - self.start_time

            # Steady state
            if delta_since_started.seconds > SETTING_TIME_S:
                return random.uniform(steady_state_val*0.95,
                                      steady_state_val*1.05)
            else:
                last_val = last_val + steady_state_val * delta_since_started.seconds / SETTING_TIME_S
                if last_val > steady_state_val:
                    last_val = random.uniform(steady_state_val*0.95,
                                              steady_state_val*1.05)
                return last_val

        if self.stopped:
            delta_since_stopped = now - self.stop_time

            # Steady state
            if delta_since_stopped.seconds > SETTING_TIME_S:
                return 0
            else:
                last_val = last_val - steady_state_val * delta_since_stopped.seconds / SETTING_TIME_S
                if last_val < 0:
                    last_val = 0
                return last_val

        return 0

    def get_pressure_psi(self):
        self.last_pressure = self.get_variable(70, self.last_pressure)
        return self.last_pressure

    def get_phase1_current_A(self):
        return self.get_variable(17, self.last_current_ph1)

    def get_phase2_current_A(self):
        return self.get_variable(17, self.last_current_ph2)


# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 8883))
username = os.environ.get('MQTT_USERNAME')
password = os.environ.get('MQTT_PASSWORD')
ca_certs_path = os.environ.get('MQTT_CA_CERTS')
actuator_topic = "actuators/bomba"

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
    global SLEEP_TIME
    payload = msg.payload.decode()
    if payload == "ON":
        bomba.start()
        SLEEP_TIME = BOMB_ON_SLEEP_TIME
        print(f"{datetime.now()} Digital signal turned ON")
    elif payload == "OFF":
        bomba.stop()
        SLEEP_TIME = BOMB_TURNING_OFF_SLEEP_TIME
        print(f"{datetime.now()} Digital signal turned OFF")


def wait_next_iteration():
    global SLEEP_TIME
    for i in range(SLEEP_TIME):
        time.sleep(1)
        print(f"{datetime.now()} Sleeping")
        if bomba.started:
            break

    if bomba.stopped:
        SLEEP_TIME = BOMB_OFF_SLEEP_TIME


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

# Start the MQTT client's network loop in a separate thread
client.loop_start()

while True:
    pressure = bomba.get_pressure_psi()
    payload = f'{{"value": {float(pressure)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-water-pressure"}}'
    client.publish("sensors/bomb/water_pressure", payload)

    cph1 = bomba.get_phase1_current_A()
    payload = f'{{"value": {float(cph1)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph1"}}'
    client.publish("sensors/bomb/current_ph1", payload)

    cph2 = bomba.get_phase1_current_A()
    payload = f'{{"value": {float(cph2)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph2"}}'
    client.publish("sensors/bomb/current_ph1", payload)

    print(f"{datetime.now()} Publishing: {pressure} psi, {cph1} A, {cph2} B")
    wait_next_iteration()

