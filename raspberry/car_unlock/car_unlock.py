# Author: Francesco Conforte s277683
# Academic year: 2020-21

import json
import requests
from lib.MyMQTT import *


class Car_Unlock():
    def __init__(self, clientID, topic, broker, port, ip_catalog, port_catalog,ip_bot, port_bot,plate):
        self.client=MyMQTT(clientID, broker, port, self)
        self.topic=topic
        self.ip_catalog=ip_catalog
        self.port_catalog=port_catalog
        self.ip_bot = ip_bot
        self.port_bot = port_bot
        self.plate = plate

    def run(self):
        self.client.start()
        self.client.mySubscribe(self.topic)
        
        # decomment if you don't want to shut down this microservice when the car can start
        while True:
            a=0
            #time.sleep(3)


    def end(self):
        self.client.stop()

    #Assume the message is in SenML format coming from MQ5 sensor

    #{"bn":"MQ5",
    # "e":[
    #       {
    #           "n":"Tasso Alcolemico",
    #           "u":"ppm",
    #           "v":"a value"
    #       }
    # ]
    #} 
    def notify(self,topic,msg):
        # Read the incoming message
        payload=json.loads(msg)
        print("Message received from alcohol test")
        
        # Transform from ppm to g/L the incoming value of alcohol level
        alcohol_value_ppm=payload["e"][0]["v"]
        alcohol_value_g_l=alcohol_value_ppm*1e-3 #1ppm=0.001 g/L
        print("alcohol value received: ",alcohol_value_g_l)
        
        # Retrieve threasholds from catalog
        thresholds=self.get_threasholds_alcohol()
        
        # Access to retrieved threasholds
        ths = thresholds["thresholds_alcohol"]
        
        # Discover what is the belonging range of the user according to the Italian Law and 
        # retrieve the message to send to the telegram bot and to publish on InfluxDB
        message, bot = self.check_limits_alcohol(alcohol_value_g_l,ths)
        
        # Send message containing values to the bot if necessary by making a HTTP POST
        if bot: 
            bot_url = "http://" + self.ip_bot + ":" + self.port_bot + "/alcoholTest"
            print("message to bot: ",message)
            status = requests.post(bot_url, json=message)
            print("Message sent to Telegram Bot", status)
            
        # Publish message on broker for InfluxDB
        topic_where_to_pub = "smart2safe/raspberry/"+self.plate+"/alcohol_test"
        self.client.myPublish(topic_where_to_pub, message)   
        print("Message for Dashboard has been published") 
        

    def get_threasholds_alcohol(self):
        """method to retrieve threasholds of alcohol from the catalog through
        requests module and get method

        Returns:
            threashold (dict): the json dictionary containing the threasholds recovered 
                    from the catalog
        """
        th_URL="http://" + self.ip_catalog + ":" + self.port_catalog + "/th_alc"
        thre_alco=requests.get(th_URL)
        threasholds = thre_alco.json() 
        threasholds = threasholds["th_alc"]  
        return threasholds


    def check_limits_alcohol(self, alc_value,ths):
        """method to check the levels of alcohol and check which is the belonging 
        range according to Italian Law. 

        Args:
            alc_value (float): value measured from the alcohol test
            ths (dict): json dictionary containing the threasholds
        
        Returns: 
            msg (dict or tuple): json dictionary containing data for Telegram bot or tuple with a string
                                saying that the car can start and the measured value
            bot (bool): True if the message is for the Telegram bot;
                        False if the message is not for the Telegram bot
        """
        print("CONTROLLO LIMITE ALCOHOL")
        ths_2000 = ths["alcohol_test_2000"]
        ths_3200 = ths["alcohol_test_3200"]
        ths_6000 = ths["alcohol_test_3200"]

        if 0 <= alc_value < ths_2000[0]: #0-0.5 g/L
            
            # Sign the message that the car can start 
            print("Alcohol test successful, car unlocked")
            print("level:",alc_value)
            print("threashold",ths_2000[0])
            msg = self.set_message_for_bot(alc_value, n=0)
            bot = True

        elif ths_2000[0] <= alc_value < ths_2000[1]: #0.5-0.8g/l
            msg = self.set_message_for_bot(alc_value, n=1)
            bot = True
            
        elif ths_3200[0] <= alc_value < ths_3200[1]: #0.8-1.5g/l
            msg = self.set_message_for_bot(alc_value, n=2)
            bot = True

        elif alc_value >= ths_6000[0]: #over 1.5g/l
            msg = self.set_message_for_bot(alc_value, n=3)
            bot = True

        #remove the presence of the MQ-5 sensor from the network
        url = "http://" + self.ip_catalog + ":" + self.port_catalog + "/start?plate=" + self.plate
        requests.delete(url)
        # self.stop = False

        return msg, bot


    def set_message_for_bot(self, alc_value, n):
        """method to set the values useful to compile the message for the 
        telegram bot and save the values in a json file.

        Args:
            alc_value (float): value measured from the alcohol test
            n (int): from 0 to 3:
                        if 0 the range for the alcohol level is 0 - 0.5 g/L;
                        if 1 the range for the alcohol level is 0.5-0.8 g/L;
                        if 2 the range for the alcohol level is 0.8-1.5 g/L;
                        if 3 the range for the alcohol level is over 1.5 g/L
        Returns:
            message (dict): dictionary containing information for the Telegram bot
        """

        message = {
                    "general_comment":"message for the telegram bot",
                    "_comment":"fine is the 'multa', prisons is the years of prison, impounding is sequestro",
                    "alcohol_value": None,
                    "fine": None, 
                    "prisons": None,
                    "license_suspension": None,
                    "impounding": None,
                    "plate" : self.plate,
                    "failed": False
                }
        
        if n==1:
            message["alcohol_value"]=alc_value
            message["fine"]=[500,2000] # Multa che si rischia in euro
            message["prisons"]=0 # Prigione in mesi
            message["license_suspension"]=[3,6] # Sospensione patente in mesi
            message["impounding"]=False # Sequestro del mezzo
            message["failed"]=True 
        elif n==2: 
            message["alcohol_value"]=alc_value
            message["fine"]=[800,3200] # Multa che si rischia in euro
            message["prisons"]=3 # Prigione in mesi
            message["license_suspension"]=[6,12] # Sospensione patente in mesi
            message["impounding"]=False #Sequestro del mezzo
            message["failed"]=True
        elif n==3: 
            message["alcohol_value"]=alc_value
            message["fine"]=[1500,6000] # Multa che si rischia in euro
            message["prisons"]=[6,12] # Prigione in mesi
            message["license_suspension"]=[12,24] # Sospensione patente in mesi
            message["impounding"]=True # Sequestro del mezzo
            message["failed"]=True

        elif n==0: 
            message["alcohol_value"] = alc_value



        return message


        