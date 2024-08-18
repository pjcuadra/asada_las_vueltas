import threading
import time
from datetime import timedelta, datetime


MAX_RUN_TIME = 12


class BombScheduler():
    start_time = None
    end_time = None
    running_time = None
    running = False
    cronjobs = list()

    def __init__(self):
        self.contro_sm = threading.Thread(target=self.tick, args=())
        self.contro_sm.start()

    def should_run(self):
        return self.running

    def schedule_now(self, delta):
        if delta > timedelta(hours=12):
            return False

        self.start_time = datetime.now()
        self.stop_time = self.start_time + delta
        self.running_time = timedelta()
        self.running = True

        print(f'{datetime.now()} Scheduling: start {self.start_time } delta {delta} end {self.stop_time}')

        return True

    def cancel_scheduled(self):
        self.start_time = None
        self.stop_time = None
        self.running_time = None
        self.running = False
        print(f'{datetime.now()} Canceling Current schedule: start {self.start_time } end {self.stop_time}')

    def schedule_at(self, start, delta):
        if delta > timedelta(hours=12):
            return False

        print(f'{datetime.now()} Adding to cronjob: start {start } delta {delta} end {start + delta}')

        self.cronjobs.append({
            "start": start,
            "end": start + delta
        })

        return True

    def stop_running(self):
        self.start_time = None
        self.stop_time = None
        self.running_time = None
        self.running = False

    def check_cronjob_schedule(self, now):
        for job in self.cronjobs:
            if now > job['start'] and now < job['end']:
                self.start_time = job['start']
                self.stop_time = job['end']
                self.running_time = timedelta()
                self.running = True
                break

    def tick(self):
        while True:
            now = datetime.now()
            if self.start_time is None:
                time.sleep(5)
                self.check_cronjob_schedule(now)
                continue

            if now > self.stop_time:
                self.stop_running()
                continue

            self.running_time = datetime.now() - self.start_time
            print(f'{datetime.now()} Run Time: {self.running_time}')

            time.sleep(5)
