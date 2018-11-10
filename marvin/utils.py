import math
from urllib.request import urlopen

from marvin import config


def get_iss_tle():
    try:
        resp = urlopen(config.TLE)
        iss_tle = resp.read().decode('utf-8').split('\n')
        if config.DEBUG:
            print(iss_tle)
        return iss_tle
    except Exception:
        print("ERROR: Cannot retrieve coordinate data, retrying...")


def to_deg(radians):
    """Converts radians to degrees"""
    return radians * 180.0 / math.pi


def print_body_info(body):
    print("CURRENT LOCATION:")
    print("Latitude : %s" % body.sublat)
    print("Longitude: %s" % body.sublong)
    print("Azimuth  : %s" % int(to_deg(body.alt)))
    print("Altitude : %s" % int(to_deg(body.az)))
