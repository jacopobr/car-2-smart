import time
import requests
import json
import os
from windows_monitorer import *

# Address of catalog
#catalog_IP = '192.168.1.18'
catalog_IP = 'expose-catalog'
# port of catalog
catalog_port = '9090'
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

# URL of catalog to retrieve IP and Port of the bot
bot_url =  "http://" + catalog_IP + ":" + catalog_port + "/bot"
# the broker IP and port are requested to the catalog
r = requests.get(bot_url)
obj = r.json()
bot = obj["bot"]
bot_ip = bot["postAlcoholTest"]
bot_port = str(bot["port"])
print(f"Bot IP and port obtained from Catalog. Port: {bot_port}, Host: {bot_ip}")

plate = os.environ.get('PLATE')

#Instantiate the sensors
sensor = Microphone(plate)
windows_monitor = Glass_break("Window Monitor", "/smart2safe/raspberry/"+plate+"/windows_monitor",broker_IP, broker_port,sensor,catalog_IP,catalog_port,plate=plate)
#Start monitorer
windows_monitor.run(bot_IP = bot_ip, use_mic=False) # If false read existing files
windows_monitor.end()
