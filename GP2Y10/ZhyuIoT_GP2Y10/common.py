import time

# Define error constants.
GP2Y10_SUCCESS        =  0
GP2Y10_ERROR_TIMEOUT  = -1
GP2Y10_ERROR_CHECKSUM = -2
GP2Y10_ERROR_ARGUMENT = -3
GP2Y10_ERROR_GPIO     = -4
GP2Y10_ERROR_SERIAL     = -5
TRANSIENT_ERRORS = [GP2Y10_ERROR_CHECKSUM, GP2Y10_ERROR_TIMEOUT]

GP2Y1051A  = 51

SENSORS = [GP2Y1051A]

def get_platform():
	"""Return a GP2Y10 platform interface for the currently detected platform.
	Raspberry pi only right now.
	"""
	import Raspberry_Pi
	return Raspberry_Pi

def read(sensor = GP2Y1051A, sample=5, platform=None):
	"""Read GP2Y10 sensor of specified sensor type (GP2Y1051A) with specified sample 
	attempts and return a value of duster (as a floating point value in mg/m3).
	"""
	if sensor not in SENSORS:
		raise ValueError('Expected GP2Y1051A sensor value.')
	if platform is None:
		platform = get_platform()
	return platform.read(sensor, sample)
