import time
import threading


class ControlSM():
    bomb = None
    state = dict()
    events = dict()

    def __init__(self, bomb, sm_period_s=30, stopping_time_s=120):
        self.sm_period_s = sm_period_s
        self.stopping_time_s = stopping_time_s
        self.bomb = bomb
        self.state['sm_state'] = "init"
        self.state['prev_sm_state'] = ""
        self.update_sensors_data()
        self.events['start'] = False
        self.events['stop'] = True

    def state_machine(self):
        stop_count = 0

        while True:

            self.update_sensors_data()

            if self.events['start']:
                if self.state['sm_state'] not in ['start', 'started']:
                    print("Start event received. Next state: start")
                    self.state['sm_state'] = 'start'
                else:
                    print("Start event received. Already started")

                self.events['start'] = False
                continue

            if self.events['stop']:
                if self.state['sm_state'] not in ['stop', 'stopping', 'stopped']:
                    print("Stop event received. Next state: stop")
                    self.state['sm_state'] = 'stop'
                else:
                    print("Stop event received. Already stopping")
                self.events['stop'] = False
                continue

            if self.state['sm_state'] == 'init':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'init'")
                self.state['sm_state'] = 'stop'
                print("Next State: 'stop'")

            if self.state['sm_state'] == 'start':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'start'")
                self.bomb.start()
                self.state['sm_state'] = 'started'
                print("Next State: 'started'")

            if self.state['sm_state'] == 'started':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'started'")

            if self.state['sm_state'] == 'stop':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'stop'")
                self.bomb.stop()
                stop_count = self.stopping_time_s / self.sm_period_s
                print("Next State: 'stopping'")
                self.state['sm_state'] = 'stopping'

            if self.state['sm_state'] == 'stopping':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'stopping'")
                stop_count = stop_count - 1
                if stop_count == 0:
                    print("Next State: 'stopped'")
                    self.state['sm_state'] = 'stopped'

            if self.state['sm_state'] == 'stopped':
                if self.state['sm_state'] != self.state['prev_sm_state']:
                    print("Entering state: 'stopped'")

            self.state['prev_sm_state'] = self.state['sm_state']
            time.sleep(self.sm_period_s)

    def update_sensors_data(self):
        self.state['pressure'] = self.bomb.get_pressure_psi()
        self.state['current_ph1'] = self.bomb.get_phase1_current_A()
        self.state['current_ph2'] = self.bomb.get_phase1_current_A()

    def start(self):
        self.contro_sm = threading.Thread(target=self.state_machine, args=())
        self.contro_sm.start()

