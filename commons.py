# -*- coding: utf-8 -*-
# encoding: utf-8
'''
Created on 2014/12/17

@author: zhumx
'''
import sys
import socket
import time
import requests

import json
from uuid import getnode as get_mac

API_BASE_URL = "http://yuiot.cn/api/v1/"

API_RESPONSE_CODE = 'statusCode'
API_RESPONSE_RESULT = 'result'
API_RESPONSE_MESSAGE = 'statusMessage'

def addSensor(deviceid, type, name, model, unit, userkey):
    data = {'sensorid': "%s-%s" %(deviceid, type), 'sensorId': "%s-%s" %(deviceid, type), 'type': type, 'name': name, 'model': model, 'unit': unit}
    r = requests.post(API_BASE_URL + "devices/%s/sensors" %(deviceid), data=json.dumps(data), headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        return data
    print "There is no available %s sensor binded to device '%s', and failed to register it." %(type, deviceid)
    sys.exit(2)
    
def isMatch(sensor, sensorDescriptions):
    for description in sensorDescriptions:
        if sensor['type'] == description['type']:
            return True
    return False

def get_sensor_lists_from_device(device, sensorModel, userkey, sensorDescriptions):
    sensors = {}
    temp_sensors = []
    humi_sensors = []

    r = requests.get(API_BASE_URL + "devices/%s/sensors" %(device['deviceId']), headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        for sensor in r.json()[API_RESPONSE_RESULT]:
            if isMatch(sensor, sensorDescriptions):
                if sensor['type'] in sensors:
                    sensors[sensor['type']].append(sensor)
                else:
                    sensors[sensor['type']] = [sensor]

    if len(sensors) == 0:
        # add default sensors for our DHT device
        for description in sensorDescriptions:
            sensors[description['type']] = addSensor(device['deviceId'], description['type'], description['typeName'], 
                description['modelName'], description['unit'], userkey)
    
    sensors['deviceId'] = device['deviceId']
    return sensors

def get_sensor_lists(userkey, deviceid, sensorModel, sensorDescriptions):
    """Get sensor lists from ZhyuIoT cloud."""
    r = requests.get(API_BASE_URL + "devices", headers={'token': userkey})
    if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
        devices = r.json()[API_RESPONSE_RESULT]
        for device in devices:
            if deviceid is not None:
                if deviceid == device['deviceId']:
                    return get_sensor_lists_from_device(device, sensorModel, userkey, sensorDescriptions)
            else:
                return get_sensor_lists_from_device(device, sensorModel, userkey, sensorDescriptions)

        # add a device using given id as device name
        if deviceid is not None:
            data = {'deviceId': deviceid, 'deviceid': deviceid, 'name': socket.gethostname(), 'model': 'raspberry pi', 'macid': get_mac()}
            r = requests.post(API_BASE_URL + "devices", data=json.dumps(data), headers={'token': userkey})
            if r.status_code == requests.codes.ok and r.json()[API_RESPONSE_CODE] == 1:
                return get_sensor_lists_from_device(data, sensorModel, userkey, sensorDescriptions)

        print 'Unable to get the sensor info with specified device \'{0}\'.'.format(deviceid)
        sys.exit(1)
    else:
        print 'Unable to fetch the device info with specified userkey {0}.'.format(userkey)
        sys.exit(1)

def update_sensors_data(sensor_lists, values, userkey):
    deviceid = sensor_lists['deviceId']
    sensor_lists.pop('deviceId', None)
    if len(sensor_lists) == 0:
        print 'There is no {1} sensors registered in Lewei with device \'{0}\'.'.format(deviceid, ' or '.join(sensor_lists.keys()))
        sys.exit(3)
    else:
        for sensorType, sensors in sensor_lists.items():
            data = {'value': values[sensorType]}
            for sensor in sensors:
                r = requests.post(API_BASE_URL + "devices/%s/sensors/%s/data" %(deviceid, sensor['sensorId']),
                    data=json.dumps(data), headers={'token': userkey})
                if r.status_code == requests.codes.ok:
                    result = r.json()
                    if result[API_RESPONSE_CODE] == 1:
                        print u'Successfully updated sensor {1} with data {2} to device id {0}.'.format(deviceid, sensor['name'], data['value'])
                    else:
                        print u'Failed to update sensor {2} with data {3} to device id \'{0}\' with message {1}.'.format(deviceid, result[API_RESPONSE_MESSAGE], sensor['name'], data['value'])
                else:
                    print u'Failed to update sensor {2} to device id \'{0}\' with http error code {1}.'.format(deviceid, r.status_code, sensor['name'])