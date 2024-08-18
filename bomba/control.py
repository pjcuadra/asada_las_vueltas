from time import sleep
import os
from pprint import pprint
import keyring
from getpass import getpass
from datetime import timedelta, time

from bomb_control.sm import ControlSM
from bomb_control.bombs import BombaModelo
from bomb_control.mqtt import MQTTController
from bomb_control.sched import BombScheduler


# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 8883))
username = os.environ.get('MQTT_USERNAME')
ca_certs_path = os.environ.get('MQTT_CA_CERTS')
actuator_topic = "actuators/bomba"

password = keyring.get_password("MQTT", username)
if not password:
    password = getpass()
    keyring.set_password("MQTT", username, password)

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")
if not username or not password:
    raise ValueError("MQTT_USERNAME and MQTT_PASSWORD environment variables are required")
if not ca_certs_path:
    raise ValueError("MQTT_CA_CERTS environment variable is required")

bomba = BombaModelo()
schd = BombScheduler()

sm = ControlSM(bomba, schd)
sm.start()

mqtt_contrl = MQTTController(broker_address,
                             broker_port,
                             username,
                             password,
                             ca_certs_path,
                             sm,
                             schd)
mqtt_contrl.start_publisher()

schd.schedule_at(time(hour=12, minute=1, second=0), timedelta(minutes=5))

while True:
    pprint(sm.state)
    sleep(15)
