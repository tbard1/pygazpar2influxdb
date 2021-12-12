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
from paho.mqtt import client as mqtt_client
import urllib.parse as urlparse
import random
import time

url_influxdb = os.environ['PYGAZPAR_INFLUXDB2_HOST']
bucket_influxdb = os.environ['PYGAZPAR_INFLUXDB2_BUCKET']
token_influxdb = os.environ['PYGAZPAR_INFLUXDB2_TOKEN']
org_influxdb = os.environ['PYGAZPAR_INFLUXDB2_ORG']

login_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_LOGIN']
password_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_PASSWORD']
pce_pygazpar = os.environ['PYGAZPAR_PCE_IDENTIFIER']
pce_lastNDays = int(os.environ['PYGAZPAR_LASTNDAY'])

broker = os.environ['PYGAZPAR_MQTT_URL']
port = 1883
username = os.environ['PYGAZPAR_MQTT_LOGIN']
password = os.environ['PYGAZPAR_MQTT_PASSWORD']
#xxxxxxxxxxxx = os.environ['PYGAZPAR_XXXXXXXXXXXXXXX']
topic = "/python/mqtt"
client_id = f'python-mqtt-{random.randint(0, 1000)}'



topic = "/python/mqtt"
client_id = f'python-mqtt-{random.randint(0, 1000)}'


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

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client):
    msg_count = 0
    while True:
        time.sleep(1)
        msg = f"messages: {msg_count}"
        result = client.publish(topic, msg)
        # result: [0, 1]
        status = result[0]
        if status == 0:
            print(f"Send `{msg}` to topic `{topic}`")
        else:
            print(f"Failed to send message to topic {topic}")
        msg_count += 1


def run():
    client = connect_mqtt()
    client.loop_start()
    publish(client)


if __name__ == '__main__':
    run()