import time
import random
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter


# Set up OpenTelemetry metrics
resource = Resource.create(attributes={"service.name": "water_bomb_monitor"})
provider = MeterProvider(resource=resource)
metrics.set_meter_provider(provider)
meter = metrics.get_meter(__name__)
exporter = OTLPMetricExporter(endpoint="http://localhost:4317", insecure=True)  # Adjust endpoint if needed

# Create a gauge to record pressure
pressure_gauge = meter.create_observable_gauge(
    "water_bomb_pressure",
    unit="psi",
    description="Pressure of the water bomb",
)

def get_water_bomb_pressure():
    """Simulates getting pressure from a sensor (replace with actual sensor reading)"""
    # Randomly fluctuate pressure between 100 and 120 psi
    return random.uniform(100, 120)

while True:
    pressure = get_water_bomb_pressure()
    pressure_gauge.record(pressure)
    print(f"Published pressure: {pressure} psi")

    # Export metrics to the collector
    provider.get_meter("water_bomb_monitor").collect()
    exporter.export(provider.get_meter("water_bomb_monitor").collect())

    time.sleep(60)  # Wait for 1 minute