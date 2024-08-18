import time
import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import threading

sleeps_per_state = {
    "init": 30,
    "start": 30,
    "started": 30,
    "stop": 30,
    "stopping": 30,
    "stopped": 600
}

actuator_topic = "actuators/bomba"


# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker with SSL")
        client.subscribe(actuator_topic)
    else:
        print(f"Failed to connect, return code {rc}")


def on_message(client, userdata, msg):
    payload = msg.payload.decode()
    if payload == "ON":
        userdata['scheduler'].schedule_now(timedelta(minutes=5))
        print(f"{datetime.now()} Digital signal turned ON")
    elif payload == "OFF":
        userdata['scheduler'].cancel_scheduled()
        print(f"{datetime.now()} Digital signal turned OFF")


class MQTTController():
    client = None

    def __init__(self, addr, port, username, password, ca_cert, sm, schd):
        self.schd = schd
        self.sm = sm
        self.client = mqtt.Client(userdata={"scheduler": schd})
        self.client.on_connect = on_connect
        self.client.on_message = on_message

        # Set username and password for authentication
        self.client.username_pw_set(username, password)

        # Configure SSL/TLS context (only CA certificate)
        self.client.tls_set(ca_certs=ca_cert)

        # Connect to MQTT Broker
        self.client.connect(addr, port)

        # Start the MQTT client's network loop in a separate thread
        self.client.loop_start()

    def publish_data(self):
        global sleeps_per_state
        while True:
            pressure = self.sm.state['pressure']
            payload = f'{{"value": {float(pressure)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-water-pressure"}}'
            self.client.publish("sensors/bomb/water_pressure", payload)

            cph1 = self.sm.state['current_ph1']
            payload = f'{{"value": {float(cph1)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph1"}}'
            self.client.publish("sensors/bomb/current_ph1", payload)

            cph2 = self.sm.state['current_ph2']
            payload = f'{{"value": {float(cph2)}, "timestamp": {int(time.time())}, "sensor_id": "bomb-current-ph2"}}'
            self.client.publish("sensors/bomb/current_ph2", payload)

            state = self.sm.state['sm_state']
            payload = f'{{"value": "{state}", "timestamp": {int(time.time())}, "sensor_id": "bomb-sm"}}'
            self.client.publish("sm/bomb/bomb_control", payload)

            if self.sm.state['sm_state'] in ['init', 'stop', 'stopped', 'stopping']:
                bomb_status = "OFF"
            else:
                bomb_status = "ON"
            payload = f'{{"value": "{bomb_status}", "timestamp": {int(time.time())}, "sensor_id": "bomb-relay"}}'
            self.client.publish("sensors/bomb/relay", payload)

            print(f"{datetime.now()} Publishing: {pressure} psi, {cph1} A, {cph2} B")

            for i in range(sleeps_per_state[self.sm.state['sm_state']]):
                if i > sleeps_per_state[self.sm.state['sm_state']]:
                    break
                time.sleep(1)

    def start_publisher(self):
        self.publisher = threading.Thread(target=self.publish_data,
                                          args=())
        self.publisher.start()
