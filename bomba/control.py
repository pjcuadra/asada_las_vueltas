import time
import random
import paho.mqtt.client as mqtt
import os
import RPi.GPIO as GPIO
import ssl

# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 8883))
username = os.environ.get('MQTT_USERNAME')
password = os.environ.get('MQTT_PASSWORD')
ca_certs_path = os.environ.get('MQTT_CA_CERTS')
pressure_topic = "sensors/bomb/water_pressure"
actuator_topic = "actuators/bomba"

# GPIO Pin Configuration
GPIO_PIN = 4

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")
if not username or not password:
    raise ValueError("MQTT_USERNAME and MQTT_PASSWORD environment variables are required")
if not ca_certs_path:
    raise ValueError("MQTT_CA_CERTS environment variable is required")

# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

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
        GPIO.output(GPIO_PIN, GPIO.HIGH)
        print("Digital signal turned ON")
    elif payload == "OFF":
        GPIO.output(GPIO_PIN, GPIO.LOW)
        print("Digital signal turned OFF")

def get_water_bomb_pressure():
    """Simulates getting pressure from a sensor (replace with actual sensor reading)"""
    return random.uniform(100, 120)

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
    pressure = get_water_bomb_pressure()
    payload = f'{{"value": {pressure}, "timestamp": {int(time.time())}, "sensor_id": "bomb-water-pressure"}}'
    client.publish(pressure_topic, payload)
    print(f"Published pressure: {pressure} psi")
    time.sleep(5)

# Cleanup GPIO on exit
GPIO.cleanup()