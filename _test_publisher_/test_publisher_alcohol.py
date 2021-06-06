import json
from MyMQTT import *
import random

import time
class My_heart_publisher():
    def __init__(self, clientID, topic, broker, port):
        self.topic=topic
        self.client=MyMQTT(clientID, broker, port)

    def start(self):
        self.client.start()
    
    def stop(self):
        self.client.stop()

    def publish(self):
        message = {
            "alcohol_value": random.choice([0.4, 0.5, 0.2, 0.0, 0.8,0.7])
        }
        self.client.myPublish(self.topic,message)
        print("Published")

if __name__=="__main__":
    conf=json.load(open("settings.json"))
    broker=conf["broker"]
    port=conf["port"]
    #topic="smart2safe/arduino/alcohol_test"
    topic="smart2safe/raspberry/alcohol_test"
    hrp=My_heart_publisher("HearthRate",topic,broker,port)
    hrp.start()
    t_end=time.time()+60*2
    while True:
        hrp.publish()
        time.sleep(5)
    hrp.stop()