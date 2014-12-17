#!/usr/bin/python
import sys

import ZhyuIoT_GP2Y10


# Parse command line parameters.
if len(sys.argv) == 1:
  sensor = ZhyuIoT_GP2Y10.GP2Y1051A
elif len(sys.argv) == 2 and sys.argv[1] in ZhyuIoT_GP2Y10.SENSORS:
    sensor = sensor_args[sys.argv[1]]
else:
    print 'usage: sudo ./ZhyuIoT_GP2Y10.py [51]'
    print 'example: sudo ./ZhyuIoT_GP2Y10.py - Read from a GP2Y10 51A'
    sys.exit(1)

# Try to grab a sensor reading.
density = ZhyuIoT_GP2Y10.read(sensor, 5)

if density is not None:
    print '{0:0.1f} ug/m3'.format(density)
else:
    print 'Failed to get reading. Try again!'