import time
import random
import paho.mqtt.client as mqtt
import os

# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 1883))  # Default to 1883 if not set
topic = "sensors/bomb/water_pressure"

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")

# Connect to MQTT Broker
client = mqtt.Client()
client.connect(broker_address, broker_port)

def get_water_bomb_pressure():
    """Simulates getting pressure from a sensor (replace with actual sensor reading)"""
    # Randomly fluctuate pressure between 100 and 120 psi
    return random.uniform(100, 120)

while True:
    pressure = get_water_bomb_pressure()
    payload = f"{{'value': {pressure}, 'timestamp': {int(time.time())}, 'sensor_id': 'bomb-water-pressure'}}"
    client.publish(topic, payload)
    print(f"Published pressure: {pressure} psi")
    time.sleep(60)  # Wait for 1 minute

# Disconnect from MQTT Broker (This line will never be reached due to the endless loop)
client.disconnect()