# Author: Francesco Conforte s277683
# Academic year: 2020-21


import os
import time

import requests

from car_unlock import Car_Unlock

# IP of catalog
catalog_IP = '21e80dc8009e.ngrok.io'
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
print(f"Broker IP and port obtained from Catalog. Port: {broker_port}, Host: {broker_IP}")

# URL of catalog to retrieve IP and Port of the bot
bot_url =  "http://" + catalog_IP + ":" + catalog_port + "/bot"
# the broker IP and port are requested to the catalog
r = requests.get(bot_url)
obj = r.json()
bot = obj["bot"]
bot_ip = bot["postAlcoholTest"]
bot_port = str(bot["port"])
print(f"Bot IP and port obtained from Catalog. Port: {bot_port}, Host: {bot_ip}")

# The plate is fixed for the purposes of the project, but it should be sent when the car's getting opened
# plate = "AX1245531"
plate = os.environ.get('PLATE')

# Check if there are published messages at the topic of the MQ-5
out = True
topic_url = "http://" + catalog_IP + ":" + catalog_port + "/arduino?plate=" + plate #retrieve the topic
while out:
    # Loop to check if there are messages
    r = requests.get(topic_url)
    obj = r.json()
    if obj != []:
        out = False
        obj = obj[0]
        topic = obj["servicesDetails"][0]["topic"]
        carUnlock = Car_Unlock("Car Unlock", topic,broker_IP, broker_port,catalog_IP,catalog_port,bot_ip,bot_port,plate)
        carUnlock.run()
    time.sleep(5)

   
carUnlock.client.unsubscribe()
carUnlock.end()

