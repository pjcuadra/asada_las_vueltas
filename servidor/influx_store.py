import paho.mqtt.client as mqtt
import json
import os
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# MQTT Configuration from Environment Variables
broker_address = os.environ.get('MQTT_BROKER_ADDRESS', 'localhost')
broker_port = int(os.environ.get('MQTT_BROKER_PORT', 1883))
topic = "sensors/bomb/water_pressure"

# InfluxDB Configuration from Environment Variables
influx_url = os.environ.get('INFLUXDB_URL', 'http://localhost:8086')
influx_token = os.environ.get('INFLUXDB_TOKEN')
influx_org = os.environ.get('INFLUXDB_ORG')
influx_bucket = os.environ.get('INFLUXDB_BUCKET', 'telemetry_data')  # Default bucket

# Check if environment variables are set
if not broker_address:
    raise ValueError("MQTT_BROKER_ADDRESS environment variable is not set")
if not influx_token or not influx_org:
    raise ValueError("INFLUXDB_TOKEN and INFLUXDB_ORG environment variables are required")

# InfluxDB Client
client = InfluxDBClient(url=influx_url, token=influx_token, org=influx_org)
write_api = client.write_api(write_options=SYNCHRONOUS)

# MQTT Callback Functions
def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker with result code "+str(rc))
    client.subscribe(topic)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        point = Point("water_pressure") \
            .tag("sensor_id", payload['sensor_id']) \
            .field("value", payload['value']) \
            .time(payload['timestamp'], write_precision='s')  # Assuming timestamp is in seconds

        write_api.write(bucket=influx_bucket, org=influx_org, record=point)
        print(f"Stored data in InfluxDB: {payload}")
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error parsing MQTT message: {e}")

# MQTT Client Setup
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT Broker
client.connect(broker_address, broker_port)

# Start the MQTT client loop (blocking)
client.loop_forever()