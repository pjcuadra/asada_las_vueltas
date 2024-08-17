import RPi.GPIO as GPIO
import random
from datetime import datetime

SETTING_TIME_S = 300


class BombaReal():
    started = False
    stopped = False
    start_time = None
    stop_time = None
    client = None
    RELAY_PIN = 4

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
        self.started = False
        self.stopped = True
        self.relay_signal_set(False)
        self.stop_time = datetime.now()


class BombaModelo(BombaReal):

    def __init__(self) -> None:
        pass

    def relay_signal_set(self, value):
        pass

    def get_variable(self, steady_state_val):
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
                return steady_state_val * delta_since_started.seconds / SETTING_TIME_S

        if self.stopped:
            delta_since_stopped = now - self.stop_time

            # Steady state
            if delta_since_stopped.seconds > SETTING_TIME_S:
                return 0
            else:
                return steady_state_val - steady_state_val * delta_since_stopped.seconds / SETTING_TIME_S

        return 0

    def get_pressure_psi(self):
        return self.get_variable(70)

    def get_phase1_current_A(self):
        return self.get_variable(17)

    def get_phase2_current_A(self):
        return self.get_variable(17)
