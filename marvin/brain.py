import ephem
import datetime
import time
import math
import socket
import signal
from sys import exit, argv
from urllib.request import urlopen
from marvin import config, utils


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

    def led(self, color, state):
        cmd_url = self.url_led + color + "/" + state
        self._do_request(cmd_url)

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


def simulate(minutes, iss):
    """Simulates the next few minutes of the ISS trajectory"""
    marvin.led("green", "on")
    azOld = 0
    for i in range(0, minutes, config.SIMULATION_SPEED):
        site.date = datetime.datetime.utcnow() + datetime.timedelta(minutes=i)
        iss.compute(site)

        azDeg = deg(iss.az)
        steps = int((azDeg - azOld) * config.STEPS_PER_DEGREE)
        azOld = azDeg
        marvin.move_stepper(steps)

        altDeg = deg(iss.alt)
        marvin.move_servo(altDeg)
    marvin.reset()


def iss_next_pass(iss):
    tr, azr, tt, altt, ts, azs = site.next_pass(iss)

    if (ts > tr):
        duration = int((ts - tr) * 60 * 60 * 24)

    print("Next Pass (Localtime): %s" % ephem.localtime(tr))
    if config.INFO:
        print("UTC Rise Time   : %s" % tr)
        print("UTC Max Alt Time: %s" % tt)
        print("UTC Set Time    : %s" % ts)
        print("Rise Azimuth: %s" % azr)
        print("Set Azimuth : %s" % azs)
        print("Max Altitude: %s" % altt)
        print("Duration    : %s" % duration)


def point_to(body):
    marvin.led("green", "on")
    s = eval(f"ephem.{body}()")
    s.compute(site)
    marvin.move_stepper(int(deg(s.az) * config.STEPS_PER_DEGREE))
    marvin.move_servo(int(deg(s.alt)))
    body = input("Choose another celestial body or \"q\" to quit: ")
    if body == "q":
        marvin.reset()
    else:
        marvin.reset()
        point_to(body)


def follow_iss(iss, iss_tle):
    marvin.led("green", "on")
    azOld = 0
    last_update = datetime.datetime.utcnow()
    while True:
        # Get TLE Info only every 20 minutes
        if should_update(last_update):
            iss_tle = utils.get_iss_tle()
            last_update = datetime.datetime.utcnow()
        iss = find_iss(iss_tle)
        altDeg = deg(iss.alt)
        if config.XRAY_VISION or altDeg > int(config.HOR):
            if config.INFO:
                if altDeg > int(45):
                    print("ISS IS OVERHEAD")
                else:
                    print("ISS IS VISIBLE")

            azDeg = deg(iss.az)
            steps = int((azDeg - azOld) * config.STEPS_PER_DEGREE)
            azOld = azDeg
            marvin.move_stepper(steps)
            marvin.move_servo(altDeg)
            time.sleep(5)
        else:
            if config.INFO:
                print("ISS below horizon")
            marvin.reset()
            time.sleep(60)


def should_update(last_update):
    time_since_update = (datetime.datetime.utcnow() - last_update).total_seconds()
    return time_since_update > (20 * 60)


def find_iss(iss_tle):
    iss = ephem.readtle(iss_tle[0], iss_tle[1], iss_tle[2])
    site.date = datetime.datetime.utcnow()
    iss.compute(site)
    return iss


def body_info(body):
    print("CURRENT LOCATION:")
    print("Latitude : %s" % body.sublat)
    print("Longitude: %s" % body.sublong)
    print("Azimuth  : %s" % int(deg(body.alt)))
    print("Altitude : %s" % int(deg(body.az)))


def deg(radians):
    """Converts radians to degrees"""
    return radians * 180.0 / math.pi


def build_site():
    site = ephem.Observer()
    site.date = datetime.datetime.utcnow()
    site.lat = str(config.LAT)
    site.lon = str(config.LON)
    site.horizon = str(config.HOR)
    site.elevation = config.ELV
    site.pressure = 0
    return site


OPTIONS = """
s: Simulates the next few minutes of the ISS trajectory
p: Point to specific celestial body
f: Follow ISS if visible
n: Print time of next ISS flyover
"""


if __name__ == '__main__':
    if len(argv) == 1:
        exit(OPTIONS)
    flag = argv[1]

    socket.setdefaulttimeout(10)  # In seconds
    marvin = MarvinBrain(config.STEPIP)
    site = build_site()
    iss_tle = utils.get_iss_tle()
    iss = find_iss(iss_tle)

    print("Current UTC time  : %s" % site.date)
    print("Current Local time: %s" % ephem.localtime(site.date))

    if flag == "s":
        simulate(int(input("How many minutes? ")), iss)
    elif flag == "p":
        point_to(input("Choose a celestial body: "))
    elif flag == "f":
        follow_iss(iss, iss_tle)
    elif flag == "n":
        iss_next_pass(iss)
    else:
        exit(OPTIONS)
