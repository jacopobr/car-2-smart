# Author: Francesco Conforte s277683
# Academic year: 2020-21

import json
import requests
import time
from influxdb_dashboard import InfluxUploader


# IP of catalog
#catalog_IP = '172.20.10.11'
catalog_IP = 'bfcf5bd7b7d2.ngrok.io'
# port of catalog
catalog_port = '80'

# URL of catalog to retrieve IP and PORT for the broker
broker_url = "http://" + catalog_IP + ":" + catalog_port + "/broker"
# the broker IP and port are requested to the catalog
r = requests.get(broker_url)
obj = r.json()
broker = obj["broker"]
broker_IP = broker["broker"]
broker_port = broker["port"]

# Subscribe to all topics starting with smart2safe/raspberry/
topic = "smart2safe/raspberry/#"
adaptor = InfluxUploader("Smart2SafeAdaptor", topic, broker_IP, broker_port)
adaptor.run()
while True:
    time.sleep(5)
adaptor.client.unsubscribe()
adaptor.end()