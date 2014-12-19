#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
'''
Created on 2014/12/18

@author: zhumx
'''
import os,sys,inspect
reload(sys)
sys.setdefaultencoding("UTF-8")
import time

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(os.path.dirname(currentdir))
sys.path.insert(0, parentdir)
from commons import get_sensor_lists, update_sensors_data

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 60*5

DUSTER_SENSOR_TYPE = "pm25"

# Parse command line parameters.
if len(sys.argv) >= 2:
    userkey = sys.argv[1]
    try:
        deviceid = sys.argv[2]
    except IndexError:
        deviceid = None
else:
    print 'usage: sudo ./zhyu.py userkey [DeviceId]'
    print 'example: sudo ./zhyu.py userkey pi - Read from optical duster sensor GP2Y10 then send the data to ZhyuIoT with specified device id'
    sys.exit(1)

print 'Logging sensor measurements to ZhyuIoT every {0} seconds.'.format(FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'

sensor_lists = None
ATTEMPS = 5
import ZhyuIoT_GP2Y10
while True:
    if sensor_lists == None:
        SENSOR_DESCRIPTIONS = ({'type': DUSTER_SENSOR_TYPE, 'typeName': '粉尘传感器', 'modelName': 'GP2Y10', 'unit': u'ug/m3'}, )
        sensor_lists = get_sensor_lists(userkey, deviceid, SENSOR_DESCRIPTIONS)
    # Attempt to get sensor reading.
    density = ZhyuIoT_GP2Y10.read(ZhyuIoT_GP2Y10.GP2Y1051A, 5)
    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    attemp = 1
    if density is None:
        if attemp <= ATTEMPS:
            attemp += 1
            time.sleep(2)
            continue
        else:
            print 'Failed to get data from sensor after attempting {0} times.'.format(ATTEMPS)
            sys.exit(1)

    print 'PM 2.5: {0:0.1f} ug/m3'.format(density)

    update_sensors_data(sensor_lists, {DUSTER_SENSOR_TYPE: density}, userkey)
    time.sleep(FREQUENCY_SECONDS)
