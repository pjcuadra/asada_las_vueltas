import time
import random
import paho.mqtt.client as mqtt
import os
import RPi.GPIO as GPIO

# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 1883))
pressure_topic = "sensors/bomb/water_pressure"
actuator_topic = "actuators/bomba"

# GPIO Pin Configuration (adjust to your setup)
GPIO_PIN = 4  # Replace with the actual GPIO pin number

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")

# GPIO Setup
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(GPIO_PIN, GPIO.OUT)

# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code "+str(rc))
    client.subscribe(actuator_topic)  # Subscribe to the actuator topic

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

# Connect to MQTT Broker
client.connect(broker_address, broker_port)

# Start the MQTT client's network loop in a separate thread
client.loop_start()  # Non-blocking loop

while True:
    pressure = get_water_bomb_pressure()
    payload = f"{{'value': {pressure}, 'timestamp': {int(time.time())}, 'sensor_id': 'bomb-water-pressure'}}"
    client.publish(pressure_topic, payload)
    print(f"Published pressure: {pressure} psi")
    time.sleep(5)  # Sleep for 5 seconds

# Cleanup GPIO on exit (optional, but good practice)
GPIO.cleanup()