import time
import RPi.GPIO as GPIO
import random
from datetime import datetime
import threading


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
    thread = None
    steady_state = False
    pressure = 0
    current_ph1 = 0
    current_ph2 = 0
    setting_time = 0
    op_pressure = 0
    op_current = 0

    def __init__(self, setting_time=80, op_pressure=70, op_current=17) -> None:
        self.setting_time = setting_time
        self.op_current = op_current
        self.op_pressure = op_pressure
        self.thread = threading.Thread(target=self.model_state_machine,
                                       args=(self,))
        self.thread.start()

    def model_state_machine(self):
        current_inc = self.op_current / self.setting_time
        pressure_inc = self.op_pressure / self.setting_time
        while True:
            if self.steady_state:
                rand_val = random.uniform(0.95, 1.05)
                self.pressure = rand_val * self.op_pressure
                rand_val = random.uniform(0.95, 1.05)
                self.current_ph1 = rand_val * self.op_current
                rand_val = random.uniform(0.95, 1.05)
                self.current_ph2 = rand_val * self.op_current

            if self.started:
                self.pressure = self.pressure + pressure_inc
                self.current_ph1 = self.current_ph1 + current_inc
                self.current_ph2 = self.current_ph2 + current_inc
                if self.pressure > 70:
                    self.steady_state = True

            if self.stopped:
                self.steady_state = False
                self.pressure = max(self.pressure - pressure_inc, 0)
                self.current_ph1 = max(self.current_ph1 - current_inc, 0)
                self.current_ph2 = max(self.current_ph2 - current_inc, 0)

            time.sleep(1)

    def relay_signal_set(self, value):
        pass

    def get_pressure_psi(self):
        return self.pressure

    def get_phase1_current_A(self):
        return self.current_ph1

    def get_phase2_current_A(self):
        return self.current_ph2
