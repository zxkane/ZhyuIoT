#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
'''
Created on 2014/12/09

@author: zhumx
'''
import sys
reload(sys)
sys.setdefaultencoding("UTF-8")
import socket
import time
import requests

import Adafruit_DHT
import json
from uuid import getnode as get_mac

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 60*5

TEMP_SENSOR_TYPE = "temperature"
HUMIDITY_SENSOR_TYPE = "humidity"

API_BASE_URL = "http://yuiot.cn/api/v1/"

API_RESPONSE_CODE = 'statusCode'
API_RESPONSE_RESULT = 'result'
API_RESPONSE_MESSAGE = 'statusMessage'

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

def addSensor(deviceid, type, name, model, unit, userkey):
    data = {'sensorid': "%s-%s" %(deviceid, type), 'sensorId': "%s-%s" %(deviceid, type), 'type': type, 'name': name, 'model': model, 'unit': unit}
    r = requests.post(API_BASE_URL + "devices/%s/sensors" %(deviceid), data=json.dumps(data), headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        return data
    print "There is no available %s sensor binded to device '%s', and failed to register it." %(type, deviceid)
    sys.exit(2)

def get_sensor_lists_from_device(device, sensorModel, userkey):
    temp_sensors = []
    humi_sensors = []

    r = requests.get(API_BASE_URL + "devices/%s/sensors" %(device['deviceId']), headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        for sensor in r.json()[API_RESPONSE_RESULT]:
            if sensor['type'] == TEMP_SENSOR_TYPE:
                temp_sensors.append(sensor)
            elif sensor['type'] == HUMIDITY_SENSOR_TYPE:
                humi_sensors.append(sensor)

    if len(temp_sensors) == 0 and len(humi_sensors) == 0:
        # add default sensors for our DHT device
        temp_sensors.append(addSensor(device['deviceId'], TEMP_SENSOR_TYPE, u'温度传感器', u'DHT%s' %sensorModel, u'摄氏度', userkey))
        humi_sensors.append(addSensor(device['deviceId'], HUMIDITY_SENSOR_TYPE, u'湿度传感器', u'DHT%s' %sensorModel, u'%', userkey))

    return {TEMP_SENSOR_TYPE: temp_sensors, HUMIDITY_SENSOR_TYPE: humi_sensors, 'deviceId': device['deviceId']}

def get_sensor_lists(userkey, deviceid, sensorModel):
    """Get sensor lists from ZhyuIoT cloud."""
    r = requests.get(API_BASE_URL + "devices", headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        devices = r.json()[API_RESPONSE_RESULT]
        for device in devices:
            if deviceid is not None:
                if deviceid == device['deviceId']:
                    return get_sensor_lists_from_device(device, sensorModel, userkey)
            else:
                return get_sensor_lists_from_device(device, sensorModel, userkey)

        # add a device using given id as device name
        if deviceid is not None:
            data = {'deviceId': deviceid, 'deviceid': deviceid, 'name': socket.gethostname(), 'model': 'raspberry pi', 'macid': get_mac()}
            r = requests.post(API_BASE_URL + "devices", data=json.dumps(data), headers={'token': userkey})
            if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
                return get_sensor_lists_from_device(data, sensorModel, userkey)

        print 'Unable to get the sensor info with specified device \'{0}\'.'.format(deviceid)
        sys.exit(1)
    else:
        print 'Unable to fetch the device info with specified userkey {0}.'.format(userkey)
        sys.exit(1)

def update_sensors_data(sensor_lists, humidity, temp):
    sensors = sensor_lists[TEMP_SENSOR_TYPE] + sensor_lists[HUMIDITY_SENSOR_TYPE]
    if len(sensors) == 0:
        print 'There is no temperature or humidity sensors registered in Lewei with device \'{0}\'.'.format(sensor_lists['deviceId'])
        sys.exit(3)
    else:
        for sensor in sensors:
            data = {'value': temp if sensor['type'] == TEMP_SENSOR_TYPE else humidity}
            r = requests.post(API_BASE_URL + "devices/%s/sensors/%s/data" %(sensor_lists['deviceId'], sensor['sensorId']),
                data=json.dumps(data), headers={'token': userkey})
            if r.status_code == requests.codes.ok:
                result = r.json()
                if result[API_RESPONSE_CODE] == 1:
                    print u'Successfully updated sensor {1} with data {2} to device id {0}.'.format(sensor_lists['deviceId'], sensor['name'], data['value'])
                else:
                    print u'Failed to update sensor {2} with data {3} to device id \'{0}\' with message {1}.'.format(sensor_lists['deviceId'], result[API_RESPONSE_MESSAGE], sensor['name'], data['value'])
            else:
                print u'Failed to update sensor {2} to device id \'{0}\' with http error code {1}.'.format(sensor_lists['deviceId'], r.status_code, sensor['name'])

print 'Logging sensor measurements to ZhyuIoT every {0} seconds.'.format(FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'
sensor_lists = None
ATTEMPS = 5

while True:
    if sensor_lists == None:
        sensor_lists = get_sensor_lists(userkey, deviceid, sensor)
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

    update_sensors_data(sensor_lists, humidity, temp)
    time.sleep(FREQUENCY_SECONDS)
