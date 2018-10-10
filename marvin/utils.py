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
