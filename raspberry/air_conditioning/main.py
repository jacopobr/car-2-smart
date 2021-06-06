# Author: Francesco Conforte s277683
# Academic year: 2020-21

import time
import requests
import json
from air_conditioning import *
import os

# IP of catalog
catalog_IP = 'expose-catalog'
# port of catalog
catalog_port = '80'
# URL of catalog 
broker_url = "http://" + catalog_IP + ":" + catalog_port + "/broker"
# the broker IP and port are requested to the catalog
r = requests.get(broker_url)
print("Broker IP and port obtained from Catalog")
obj = r.json()
print(obj)
broker = obj["broker"]
broker_IP = broker["broker"]
broker_port = broker["port"]
plate =  os.environ.get('PLATE')
sensor = Temperature_Sensor()
air_conditioning = Air_conditioning("Air Conditioning", "/smart2safe/raspberry/"+plate+"/aircondition",broker_IP, broker_port,sensor,catalog_IP,catalog_port,plate=plate)
air_conditioning.run()
air_conditioning.end()
