import time
import ephem
from datetime import datetime, timedelta
from marvin import config, utils


class IssTracker:
    def __init__(self, marvin, site):
        self.marvin = marvin
        self.site = site
        self.iss_tle = utils.get_iss_tle()
        self.iss = self.find_iss(self.iss_tle)

    def _should_update(self, last_update):
        time_since_update = (datetime.utcnow() - last_update).total_seconds()
        return time_since_update > (20 * 60)

    @property
    def next_pass(self):
        tr, azr, tt, altt, ts, azs = self.site.next_pass(self.iss)

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

    def find_iss(self, iss_tle):
        iss = ephem.readtle(iss_tle[0], iss_tle[1], iss_tle[2])
        self.site.date = datetime.utcnow()
        iss.compute(self.site)
        return iss

    def simulate(self, minutes):
        """Simulates the next few minutes of the ISS trajectory"""
        self.marvin.turn_led_on()
        azOld = 0

        for i in range(0, minutes, config.SIMULATION_SPEED):
            self.site.date = datetime.utcnow() + timedelta(minutes=i)
            self.iss.compute(self.site)

            azDeg = utils.to_deg(self.iss.az)
            steps = int((azDeg - azOld) * config.STEPS_PER_DEGREE)
            azOld = azDeg
            self.marvin.move_stepper(steps)

            altDeg = utils.to_deg(self.iss.alt)
            self.marvin.move_servo(altDeg)
        self.marvin.reset()

    def follow_iss(self):
        self.marvin.turn_led_on()
        azOld = 0
        last_update = datetime.utcnow()
        while True:
            # Get TLE Info only every 20 minutes
            if self._should_update(last_update):
                self.iss_tle = utils.get_iss_tle()
                last_update = datetime.utcnow()
            iss = self.find_iss(self.iss_tle)
            altDeg = utils.to_deg(iss.alt)
            if config.XRAY_VISION or altDeg > int(config.HOR):
                if config.INFO:
                    if altDeg > int(45):
                        print("ISS IS OVERHEAD")
                    else:
                        print("ISS IS VISIBLE")

                azDeg = utils.to_deg(iss.az)
                steps = int((azDeg - azOld) * config.STEPS_PER_DEGREE)
                azOld = azDeg
                self.marvin.move_stepper(steps)
                self.marvin.move_servo(altDeg)
                time.sleep(5)
            else:
                if config.INFO:
                    print("ISS below horizon")
                self.marvin.reset()
                time.sleep(60)


class Pointer:
    def __init__(self, marvin, site):
        self.marvin = marvin
        self.site = site

    def point_to(self, body):
        self.marvin.turn_led_on()
        body_to_point = body
        should_point = True

        while should_point:
            if not hasattr(ephem, body_to_point):
                break

            s = getattr(ephem, body_to_point)()
            s.compute(self.site)
            self.marvin.move_stepper(int(utils.to_deg(s.az) * config.STEPS_PER_DEGREE))
            self.marvin.move_servo(int(utils.to_deg(s.alt)))

            body_to_point = input("Choose another celestial body or 'q' to quit: ")
            self.marvin.reset()
