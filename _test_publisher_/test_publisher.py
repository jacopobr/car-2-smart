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
            "e":[{"n":"Internal Car Temperature","u":"/","t":None,"v":None},
                {"n":"Humidity","u":"/","t":None,"v":None},
                {"n":"Outside temperature","u":"/","t":None,"v":None},
                {"n":"Outside humidity","u":"/","t":None,"v":None}]}
    def start(self):
        self.client.start()
    
    def stop(self):
        self.client.stop()

    def publish(self):
        message=self.__message
        message["e"][0]["v"]=random.randint(20,30) #measured temperature inside car
        message["e"][0]["t"]=time.time()
        message["e"][1]["v"]=random.randint(1,100) #measured humidity inside car
        message["e"][1]["t"]=time.time()
        message["e"][2]["v"]=random.randint(20,30) # temperature outside
        message["e"][2]["t"]=time.time()
        message["e"][3]["v"]=random.randint(1,100) # homidity outside
        message["e"][3]["t"]=time.time()
        self.client.myPublish(self.topic,message)
        print("Published")

if __name__=="__main__":
    conf=json.load(open("settings.json"))
    broker=conf["broker"]
    port=conf["port"]
    #topic="smart2safe/arduino/alcohol_test"
    topic="smart2safe/raspberry/aircondition"
    hrp=My_heart_publisher("HearthRate",topic,broker,port)
    hrp.start()
    t_end=time.time()+60*2
    while True:
        hrp.publish()
        time.sleep(5)
    hrp.stop()