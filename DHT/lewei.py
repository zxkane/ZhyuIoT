#!/usr/bin/python
# -*- coding: utf-8 -*-
# encoding: utf-8
'''
Created on 2014/11/24

@author: zhumx
'''
import sys
import time
import requests

import Adafruit_DHT
import json

# How long to wait (in seconds) between measurements.
FREQUENCY_SECONDS      = 60*5

TEMP_SENSOR_TYPE = "TEMP"
HUMIDITY_SENSOR_TYPE = "HUMI"

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
    print 'usage: sudo ./lewei.py [11|22|2302] GPIOpin# LeweiUserkey [LeweiDeviceId]'
    print 'example: sudo ./lewei.py 11 4 userkey pi - Read from an DHT11 connected to GPIO #4 then send the data to Leiwei with specified device id'
    sys.exit(1)


def get_sensor_lists_from_device(device):
    temp_sensors = []
    humi_sensors = []
    for sensor in device['sensors']:
        if sensor['type'] == TEMP_SENSOR_TYPE:
            temp_sensors.append(sensor['idName'])
        elif sensor['type'] == HUMIDITY_SENSOR_TYPE:
            humi_sensors.append(sensor['idName'])
    
    return {TEMP_SENSOR_TYPE: temp_sensors, HUMIDITY_SENSOR_TYPE: humi_sensors, 'deviceid': device['idName']}

def get_sensor_lists(userkey, deviceid):
    """Get sensor lists from Lewei cloud."""
    r = requests.get("http://www.lewei50.com/api/V1/user/getSensorsWithGateway", headers={'userkey': userkey})
    if r.status_code == requests.codes.ok:
        devices = r.json()
        for device in devices:
            if deviceid is not None:
                if deviceid == device['idName']:
                    return get_sensor_lists_from_device(device)
            else:
                return get_sensor_lists_from_device(device)
            
        print 'Unable to get the sensor info with specified device \'{0}\'.'.format(deviceid)
        sys.exit(1)
    else:
        print 'Unable to fetch the device info with specified userkey {0}.'.format(userkey)
        sys.exit(1)
        
def update_sensors_data(sensor_lists, humidity, temp):
    def create_data(sensors, value):
        datas = []
        for sensorid in sensors:
		datas.append({'Name': sensorid, 'Value': value})
        return datas
    data_list = create_data(sensor_lists[TEMP_SENSOR_TYPE], temp) + create_data(sensor_lists[HUMIDITY_SENSOR_TYPE], humidity)
    if len(data_list) == 0:
        print 'There is no temperature or humidity sensors registered in Lewei with device \'{0}\'.'.format(sensor_lists['deviceid'])
        sys.exit(1)
    else:
        r = requests.post("http://www.lewei50.com/api/V1/gateway/UpdateSensors/" + sensor_lists['deviceid'], data=json.dumps(data_list), headers={'userkey': userkey})
        if r.status_code == requests.codes.ok:
            result = r.json()
            if result['Successful']:
                print 'Successfully updated sensor data to device id {0}.'.format(sensor_lists['deviceid'])
            else:
                print 'Failed to update sensor data to device id \'{0}\' with message {1}.'.format(sensor_lists['deviceid'], result['Message'])    
        else:
            print 'Failed to update sensor data to device id \'{0}\' with http error code {1}.'.format(sensor_lists['deviceid'], r.status_code)

print 'Logging sensor measurements to lewei every {0} seconds.'.format(FREQUENCY_SECONDS)
print 'Press Ctrl-C to quit.'
sensor_lists = None
ATTEMPS = 5

while True:
    if sensor_lists == None:
        sensor_lists = get_sensor_lists(userkey, deviceid)
    
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
