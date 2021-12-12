#!/usr/bin/env python3

import sys
import json
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pygazpar.enum import Frequency
import datetime
import argparse
import logging
import re
import decimal
from decimal import Decimal
import pygazpar
import os
import paho.mqtt.client as mqtt
import urllib.parse as urlparse

url_influxdb = os.environ['PYGAZPAR_INFLUXDB2_HOST']
bucket_influxdb = os.environ['PYGAZPAR_INFLUXDB2_BUCKET']
token_influxdb = os.environ['PYGAZPAR_INFLUXDB2_TOKEN']
org_influxdb = os.environ['PYGAZPAR_INFLUXDB2_ORG']

login_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_LOGIN']
password_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_PASSWORD']
pce_pygazpar = os.environ['PYGAZPAR_PCE_IDENTIFIER']
pce_lastNDays = int(os.environ['PYGAZPAR_LASTNDAY'])

url_mqtt = os.environ['PYGAZPAR_MQTT_URL']
url_username = os.environ['PYGAZPAR_MQTT_LOGIN']
url_password = os.environ['PYGAZPAR_MQTT_PASSWORD']
#xxxxxxxxxxxx = os.environ['PYGAZPAR_XXXXXXXXXXXXXXX']

parser = argparse.ArgumentParser()

parser.add_argument("--source", help="Source ('json' file must be named data.json. 'pygazpar' asks to pygazpar to retrieve data)", dest="SOURCE", default="pygazpar")

parser.add_argument("-v", "--verbose", dest="verbose_count", action="count", default=0, help="increases log verbosity")

args = parser.parse_args()
log = logging.getLogger()
logging.basicConfig(stream=sys.stderr, level=logging.WARNING,
                    format='%(name)s (%(levelname)s): %(message)s')
log.setLevel(max(3 - args.verbose_count, 0) * 10)


influxclient = InfluxDBClient(url=url_influxdb, token=token_influxdb, org=org_influxdb)


write_api = influxclient.write_api(write_options=SYNCHRONOUS)

#------------------------------------------------- 
        
client = pygazpar.Client(username=login_pygazpar, password=password_pygazpar, pceIdentifier=pce_pygazpar, meterReadingFrequency=Frequency.DAILY, lastNDays=pce_lastNDays, tmpDirectory='/tmp')

log.debug('Starting to update pygazpar data')
client.update()
log.debug('End update pygazpar data')

data = client.data()

jsonInflux = []

for measure in data:
    print(measure)
    date_time_obj = datetime.datetime.strptime(measure['time_period'], '%d/%m/%Y')
    if 'start_index_m3' in measure:
      jsonInflux.append({
        "measurement": "gazpar_consumption_per_day",
        "tags": {
        },
        "time": date_time_obj.strftime('%Y-%m-%dT%H:%M:%S'),
        "fields": {
            "value": measure['volume_m3'],
            "start_index_m3": measure['start_index_m3'],
            "end_index_m3": measure['end_index_m3'],
            "volume_m3": measure['volume_m3'],
            "energy_kwh": measure['energy_kwh'],
            "converter_factor_kwh/m3": measure['converter_factor_kwh/m3'],
            "type": measure['type'],
        }
    })
    else:
      print('No measure')

write_api.write(bucket=bucket_influxdb, record=jsonInflux)


#############################################################################################################################

# Copyright (c) 2010,2011 Roger Light <roger@atchoo.org>
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
# 3. Neither the name of mosquitto nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.






# Define event callbacks
def on_connect(client, userdata, flags, rc):
    print("rc: " + str(rc))

def on_message(client, obj, msg):
    print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))

def on_publish(client, obj, mid):
    print("mid: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)

mqttc = mqtt.Client()
# Assign event callbacks
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe

# Uncomment to enable debug messages
mqttc.on_log = on_log

# Parse CLOUDMQTT_URL (or fallback to localhost)
url_str = os.environ.get('url_mqtt:1883')
url = urlparse.urlparse(url_str)
#topic = url.path[1:] or 'test'

# Connect
mqttc.username_pw_set(url_username, url_password)
#mqttc.connect(url.hostname, url.port)
mqttc.connect(url, 1883)

# Start subscribe, with QoS level 0
mqttc.subscribe(topic, 0)

# Publish a message
mqttc.publish(topic, "my message")

# Continue the network loop, exit when an error occurs
rc = 0
while rc == 0:
    rc = mqttc.loop()
print("rc: " + str(rc))