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
import schedule
import time
from dotenv import load_dotenv

load_dotenv()
url_influxdb = os.environ['PYGAZPAR_INFLUXDB2_HOST']
bucket_influxdb = os.environ['PYGAZPAR_INFLUXDB2_BUCKET']
token_influxdb = os.environ['PYGAZPAR_INFLUXDB2_TOKEN']
org_influxdb = os.environ['PYGAZPAR_INFLUXDB2_ORG']

login_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_LOGIN']
password_pygazpar = os.environ['PYGAZPAR_PYGAZPAR_PASSWORD']
pce_pygazpar = os.environ['PYGAZPAR_PCE_IDENTIFIER']
pce_lastNDays = int(os.environ['PYGAZPAR_LASTNDAY'])


parser = argparse.ArgumentParser()

parser.add_argument("--source", help="Source ('json' file must be named data.json. 'pygazpar' asks to pygazpar to retrieve data)", dest="SOURCE", default="pygazpar")

parser.add_argument("-v", "--verbose", dest="verbose_count", action="count", default=0, help="increases log verbosity")

args = parser.parse_args()
log = logging.getLogger()
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG,
                    format='%(name)s (%(levelname)s): %(message)s')
log.setLevel(max(3 - args.verbose_count, 0) * 10)


influxclient = InfluxDBClient(url=url_influxdb, token=token_influxdb, org=org_influxdb)


write_api = influxclient.write_api(write_options=SYNCHRONOUS)

#------------------------------------------------- 
 
def g2i():
  log.debug('Entering Function')

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

schedule.every().day.at("01:00").do(g2i)

while True:
   schedule.run_pending()
time.sleep()

