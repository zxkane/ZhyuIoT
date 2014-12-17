import common
import Raspberry_Pi_Driver as driver

def read(sensor, sample):
	# Validate sample is a positive integer.
	if sample is None or int(sample) < 0:
		raise ValueError('Sample must be a positive integer.')
	# Get a reading from C driver code.
	result, density = driver.read(sensor, int(sample))
	if result in common.TRANSIENT_ERRORS:
		# Signal no result could be obtained, but the caller can retry.
		return None
	elif result == common.GP2Y10_ERROR_GPIO:
		raise RuntimeError('Error accessing GPIO. Make sure program is run as root with sudo!')
	elif result == common.GP2Y10_ERROR_SERIAL:
		raise RuntimeError('Error accessing serial. Make sure program is run as root with sudo!')	
	elif result != common.GP2Y10_SUCCESS:
		# Some kind of error occured.
		raise RuntimeError('Error calling GP2Y10 test driver read: {0}'.format(result))
	return density
