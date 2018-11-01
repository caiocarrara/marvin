# 0 off 1 on
DEBUG = False

# Display ephemeris info
INFO = True

# Your Latitude (+N) deg
LAT = -23.51397

# Your Longitude (+E) deg
LON = -47.48727

# Elevation at your location (meters)
ELV = 600

# IP Address of YOUR ESP8266 AltAZ Pointer
STEPIP = "http://192.168.43.20/"

# Replace with your stepper (steps per one revolution)
STEPS = 2048

FLOAT_A = float(STEPS) / 360.0

# Default to 10 degrees above horizon before being "visible"
HOR = 10.0

TLE = "https://api.wheretheiss.at/v1/satellites/25544/tles?format=text"

ALWAYS_ON = True
SIMULATE = False
MINUTES = 90
