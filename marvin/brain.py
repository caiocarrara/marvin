import ephem
import datetime
import time
import socket
import signal
from sys import exit, argv
from urllib.request import urlopen
from marvin import config, sky


def handler(a, b):
    print("\nResetting...")
    marvin.reset()
    exit("Exiting.")


signal.signal(signal.SIGINT, handler)


class MarvinBrain:
    LED_STATE_ON = 'on'
    LED_STATE_OFF = 'off'

    def __init__(self, marvin_ip):
        self._ip = marvin_ip
        self.all_steps = 0

    @property
    def url_led(self):
        return 'http://{}/led/'.format(self._ip)

    @property
    def url_servo(self):
        return 'http://{}/servoR/value?'.format(self._ip)

    @property
    def url_stepper(self):
        return 'http://{}/stepper/'.format(self._ip)

    def _do_request(self, cmd_url):
        try:
            resp = urlopen(cmd_url)
            if config.DEBUG:
                print(cmd_url)
                print(resp.read().decode('utf-8'))
            resp.close()
            time.sleep(0.5)  # keep from overflowing ESP wifi buffer
        except Exception:
            print("ERROR: comm failure")

    def _turn_led(self, color, state):
        cmd_url = '{}{}/{}'.format(self.url_led, color, state)
        self._do_request(cmd_url)

    def turn_led_on(self, color='green'):
        self._turn_led(color, self.LED_STATE_ON)

    def turn_led_off(self, color='green'):
        self._turn_led(color, self.LED_STATE_OFF)

    def move_servo(self, angle):
        if angle > 90:
            angle = 90
        cmd_url = self.url_servo + str(angle)
        self._do_request(cmd_url)

    def _start_stepper(self):
        self._do_request(self.url_stepper + 'start')

    def _stop_stepper(self):
        self._do_request(self.url_stepper + 'stop')

    def _set_stepper_rpm(self, rpm=10):
        self._do_request(self.url_stepper + 'rpm?' + str(rpm))

    def move_stepper(self, steps):
        if steps == 0:
            return
        self._start_stepper()
        self._set_stepper_rpm()
        self._do_request(self.url_stepper + 'steps?' + str(steps))
        self._stop_stepper()
        self.all_steps += steps

    def reset(self):
        self.move_servo(-90)
        steps_to_reset = self.all_steps * -1
        self.move_stepper(steps_to_reset)
        self.all_steps = 0
        self.turn_led_off()


def build_site():
    site = ephem.Observer()
    site.date = datetime.datetime.utcnow()
    site.lat = str(config.LAT)
    site.lon = str(config.LON)
    site.horizon = str(config.HOR)
    site.elevation = config.ELV
    site.pressure = 0
    return site


if __name__ == '__main__':
    OPTIONS = """
    s: Simulates the next few minutes of the ISS trajectory
    p: Point to specific celestial body
    f: Follow ISS if visible
    n: Print time of next ISS flyover
    """

    if len(argv) == 1:
        exit(OPTIONS)
    flag = argv[1]

    socket.setdefaulttimeout(10)  # In seconds
    marvin = MarvinBrain(config.STEPIP)
    site = build_site()
    iss_tracker = sky.IssTracker(marvin, site)

    print("Current UTC time  : %s" % site.date)
    print("Current Local time: %s" % ephem.localtime(site.date))

    if flag == "s":
        minutes = int(input("How many minutes? "))
        iss_tracker.simulate(minutes)
    elif flag == "p":
        pointer = sky.Pointer(marvin, site)
        pointer.point_to(input("Choose a celestial body: "))
    elif flag == "f":
        iss_tracker.follow_iss()
    elif flag == "n":
        iss_tracker.next_pass
    else:
        exit(OPTIONS)
