import ephem
import datetime
import time
import math
import socket

from urllib.request import urlopen

from . import config, utils


glob_azOld = 0          # used to find diff between old and new AZ


class MarvinBrain:
    LED_STATE_ON = 'on'
    LED_STATE_OFF = 'off'

    def __init__(self, marvin_ip):
        self._ip = marvin_ip
        self.all_steps = 0

    @property
    def url_led(self):
        return '{}/led/'.format(self._ip)

    @property
    def url_servo(self):
        return '{}/servoR/value?'.format(self._ip)

    @property
    def url_stepper(self):
        return '{}/stepper/'.format(self._ip)

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

    def _turn_led(self, state):
        cmd_url = self.url_led + state
        self._do_request(cmd_url)

    def turn_led_on(self):
        self._turn_led(self.LED_STATE_ON)

    def turn_led_off(self):
        self._turn_led(self.LED_STATE_OFF)

    def move_servo(self, angle):
        if angle < 0 and angle != -90:
            angle = 0
        elif angle > 90:
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
        if self.all_steps != 0:
            steps_to_reset = self.all_steps * -1
            self.move_stepper(steps_to_reset)
            self.all_steps = 0
            self.move_servo(-90)
            self.turn_led_off()


if __name__ == '__main__':
    # timeout in seconds
    timeout = 10
    socket.setdefaulttimeout(timeout)
    marvin = MarvinBrain(config.STEPIP)

    # This is to allow getting the TLE after restarts
    pt = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    duration = 0        # Duration of a flyover in seconds

    while True:
        print("\n")
        print("ISS PASS INFO")

        # Get TLE Info only every 20 minutes
        # just left math for clarity, not speed
        ct = datetime.datetime.utcnow()
        next_seconds = int((ct - pt).total_seconds())
        if config.DEBUG:
            print("Seconds since last TLE check: %s" % next_seconds)
        if (next_seconds > (20 * 60)):
            iss_tle = utils.get_iss_tle()
            pt = ct

        iss = ephem.readtle(iss_tle[0], iss_tle[1], iss_tle[2])
        site = ephem.Observer()
        site.date = datetime.datetime.utcnow()
        site.lat = str(config.LAT)
        site.lon = str(config.LON)
        site.horizon = str(config.HOR)
        site.elevation = config.ELV
        site.pressure = 0

        print("Current UTC time  : %s" % site.date)
        print("Current Local time: %s" % ephem.localtime(site.date))

        # FIND NEXT PASS INFO JUST FOR REFERENCE
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

        # FIND THE CURRENT LOCATION OF ISS
        iss.compute(site)
        degrees_per_radian = 180.0 / math.pi

        altDeg = int(iss.alt * degrees_per_radian)
        azDeg = int(iss.az * degrees_per_radian)
        iss.compute(ct)

        if config.INFO:
            print("CURRENT LOCATION:")
            print("Latitude : %s" % iss.sublat)
            print("Longitude: %s" % iss.sublong)
            print("Azimuth  : %s" % azDeg)
            print("Altitude : %s" % altDeg)

            # IS ISS VISIBLE NOW
            if (altDeg > int(config.HOR)):
                if config.INFO:
                    print("ISS IS VISIBLE")

                if (altDeg > int(45)):
                    if config.INFO:
                        print("ISS IS OVERHEAD")

                next_check = 5

                # Send to AltAz Pointer
                marvin.turn_led_on()

                # Point Servo towards ISS
                # Convert AZ deg to 200 steps
                # Find the difference between current location and new location
                azDiff = azDeg - glob_azOld
                glob_azOld = azDeg
                steps = int(float(azDiff) * config.FLOAT_A)
                marvin.move_stepper(steps)
                marvin.move_servo(altDeg)
            else:
                if config.INFO:
                    print("ISS below horizon")
                marvin.reset()
                next_check = 60

            time.sleep(next_check)
