DEBUG = False

# Display ephemeris info
INFO = False

# Your Latitude (+N) deg
LAT = -23.51397

# Your Longitude (+E) deg
LON = -47.48727

# Elevation at your location (meters)
ELV = 600

# IP Address of YOUR ESP8266 AltAZ Pointer
STEPIP = "192.168.0.69"

# Replace with your stepper (steps per one revolution)
STEPS = 2048

STEPS_PER_DEGREE = STEPS / 360.0

# Default to 10 degrees above horizon before being "visible"
HOR = 10.0

# A two-line element set (TLE) is a data format encoding a list of
# orbital elements of an Earth-orbiting object for a given point in time
TLE = "https://api.wheretheiss.at/v1/satellites/25544/tles?format=text"

# Point to ISS when following it, even if it wouldn't be visible
XRAY_VISION = True

# Step size in minutes. Increase for long trajectory simulations
SIMULATION_SPEED = 10
