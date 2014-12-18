#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
'''
Created on 2014/12/09

@author: zhumx
'''
import os,sys,inspect
reload(sys)
sys.setdefaultencoding("UTF-8")
import socket
import time
import requests

import Adafruit_DHT
import json
from uuid import getnode as get_mac

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from commons import get_sensor_lists, update_sensors_data

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 60*5

TEMP_SENSOR_TYPE = "temperature"
HUMIDITY_SENSOR_TYPE = "humidity"

# Parse command line parameters.
sensor_args = { '11': Adafruit_DHT.DHT11,
                '22': Adafruit_DHT.DHT22,
                '2302': Adafruit_DHT.AM2302 }
if len(sys.argv) >= 4 and sys.argv[1] in sensor_args:
    sensor = sensor_args[sys.argv[1]]
    pin = sys.argv[2]
    userkey = sys.argv[3]
    try:
        deviceid = sys.argv[4]
    except IndexError:
        deviceid = None
else:
    print 'usage: sudo ./zhyu.py [11|22|2302] GPIOpin# userkey [DeviceId]'
    print 'example: sudo ./zhyu.py 11 4 userkey pi - Read from an DHT11 connected to GPIO #4 then send the data to ZhyuIoT with specified device id'
    sys.exit(1)

print 'Logging sensor measurements to ZhyuIoT every {0} seconds.'.format(FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'

sensor_lists = None
ATTEMPS = 5
while True:
    if sensor_lists == None:
        SENSOR_DESCRIPTIONS = ({'type': TEMP_SENSOR_TYPE, 'typeName': '温度传感器', 'modelName': 'DHT%s' %(sensor), 'unit': u'摄氏度'},
                       {'type': HUMIDITY_SENSOR_TYPE, 'typeName': '湿度传感器', 'modelName': 'DHT%s' %(sensor), 'unit': u'%'})
        sensor_lists = get_sensor_lists(userkey, deviceid, sensor, SENSOR_DESCRIPTIONS)
    # Attempt to get sensor reading.
    humidity, temp = Adafruit_DHT.read(sensor, pin)
    # Skip to the next reading if a valid measurement couldn't be taken.
    # This might happen if the CPU is under a lot of load and the sensor
    # can't be reliably read (timing is critical to read the sensor).
    attemp = 1
    if humidity is None or temp is None:
        if attemp <= ATTEMPS:
            attemp += 1
            time.sleep(2)
            continue
        else:
            print 'Failed to get data from sensor after attempting {0} times.'.format(ATTEMPS)
            sys.exit(1)

    print 'Temperature: {0:0.1f} C'.format(temp)
    print 'Humidity:    {0:0.1f} %'.format(humidity)

    update_sensors_data(sensor_lists, {TEMP_SENSOR_TYPE: temp, HUMIDITY_SENSOR_TYPE: humidity}, userkey)
    time.sleep(FREQUENCY_SECONDS)
