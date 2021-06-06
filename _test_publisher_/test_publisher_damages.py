import json
from MyMQTT import *
import random

import time
class My_heart_publisher():
    def __init__(self, clientID, topic, broker, port):
        self.topic=topic
        self.client=MyMQTT(clientID, broker, port)
        self.__message={
            "bn":"MQ5_sensor",
            "e":[{"n":"glass_infraction","u":"Bool","t":None,"v":"status"}]}
    def start(self):
        self.client.start()

    def stop(self):
        self.client.stop()

    def publish(self):
        message=self.__message
        status = random.randint(0,1)
        if status == 0:
            message["e"][0]["v"]=False
        else:
            message["e"][0]["v"]=True
        message["e"][0]["t"]=time.time()
        #message = "{\"bn\":\"MQ-5\",\"e\":[{\"n\":\"Blood Alcohol Level\",\"u\":\"/\",\"v\":\"10\"}]}"
        self.client.myPublish(self.topic,message)
        print("Published")

if __name__=="__main__":
    conf=json.load(open("settings.json"))
    broker=conf["broker"]
    port=conf["port"]
    topic="smart2safe/raspberry/window_monitor"
    hrp=My_heart_publisher("HearthRate",topic,broker,port)
    hrp.start()
    t_end=time.time()+60*2
    while True:
        hrp.publish()
        time.sleep(5)
    hrp.stop()