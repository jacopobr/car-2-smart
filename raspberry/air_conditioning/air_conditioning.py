#!/usr/bin/python
#import Adafruit_DHT
import adafruit_dht
import RPi.GPIO as GPIO
import requests
import os
import time
from lib.MyMQTT import *
import namegenerator
import board

def switch_led(level="L"):
    """
    Simulate ability to switch off and on the air conditioning using a led
    """
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    PIN = 18
    GPIO.setup(PIN,GPIO.OUT)
    if level=="H":
        GPIO.output(PIN,GPIO.HIGH)
        print("Switch back on")
    else:
        GPIO.output(PIN,GPIO.LOW)
        print("Switch off")


class Temperature_Sensor:
    def __init__(self,sensor_type = "DHT11",gpiopin = 17):
        # Set sensor type : Options are DHT11,DHT22 or AM2302
        self.sensor_name = sensor_type
        if sensor_type == "DHT11":
            self.dhtDevice = adafruit_dht.DHT11(board.D17)
        # Set GPIO sensor is connected to
        self.gpio = gpiopin
        self.sensor_id = "DHT11"

    def measure(self):
        # Use read_retry method. This will retry up to 15 times to
        # get a sensor reading (waiting 2 seconds between each retry).
        try:
            self.humidity = self.dhtDevice.humidity
            self.temperature = self.dhtDevice.temperature

            # Reading the DHT11 is very sensitive to timings and occasionally
            # the Pi might fail to get a valid reading. So check if readings are valid.
            if self.humidity is not None and self.temperature is not None:
                print('Temp={0:0.1f}*C  Humidity={1:0.1f}%'.format(self.temperature, self.humidity))
            return self.humidity,self.temperature
        except Exception as e:
            print('Failed to get reading. Trying again!')
            return None,None

    def register(self,ip_catalog, port_catalog,plate):
        """
        Register sensor on the catalog when first launched
        """
        ac_URL="http://" + ip_catalog + ":" + port_catalog + "/car"
        body = {"plate": plate, "device":"rpi","sensor":self.sensor_name,"measure_type":["temperature","humidity"],
                "sensor_id":self.sensor_id+"-"+plate,"serviceType": "MQTT", "topic":"smart2safe/raspberry/"+plate+"/aircondition"}
        requests.post(ac_URL, data = body)

    def deregistrer(self,ip_catalog, port_catalog,plate):
        """
        Deregister sensor on the catalog
        """
        ac_URL="http://" + ip_catalog + ":" + port_catalog + "/close?plate="+plate+"&sensor_id="+self.sensor_id
        requests.delete(ac_URL)

class Air_conditioning:
    def __init__(self, clientID, topic, broker, port, sensor, ip_catalog='172.20.10.11', port_catalog='9090',plate="AX1245531"):
        self.client=MyMQTT(clientID, broker, port, self)
        self.topic=topic
        self.ip_catalog=ip_catalog
        self.port_catalog=port_catalog
        self.sensor = sensor
        self.plate = plate
    
    def build_message(self,sensor,humidity,temperature,outside_temp):
        """
        build message in senML format ready to be published

        Paramaters 
		------------
			sensor : Microphone object
				sensor object that collect the information
			humidity : float
				value of humidity retrieved from sensor
            temperature: float
                value of temperature retrieved from sensor
            outside_temp: float
                value of outside temperature retrieved from open APIs
        """
        self.msg = {
            "bn":sensor.sensor_name,
            "e":[{
                    "n":"Temperature","u":"Cel","t":time.time(),"v":temperature
                },
                {   
                    "n":"Humidity","u":"%RH","t":time.time(),"v":humidity
                },
                {
                    "n":"Out_Temperature","u":"Cel","t":time.time(),"v":outside_temp
                }
                # {
                #     "n":"Out_Humidity","u":"%RH","t":time.time(),"v":outside_hum
                # }
                ]}
        print(self.msg)

    def retrieve_airconditioning_settings(self):
        """method to retrieve settings from the catalog through
        requests module and get method

        Returns:
            [dict]: returns the json dictionary containing the settings recovered 
                    from the catalog
        """
        ac_URL="http://" + self.ip_catalog + ":" + self.port_catalog + "/ac"
        self.ac_settings=requests.get(ac_URL).json()["ac"] 
        print(self.ac_settings)
        print("Type settings: ",type(self.ac_settings))
        return self.ac_settings

    def apply_corrections(self,temperature):
        """
        Compare measured temperature with threashold values retrieved from the settings.
        If the temperature is outside of the established range switch off the heating/cooling
        """
        if self.status =="heating":
            if temperature > self.ac_settings[self.status]["max_temp"]:
                print("Switch off heating")
                #Turn off ability to use heating
                switch_led("L")
            if temperature < self.ac_settings[self.status]["max_temp"]:
                #Turn on ability to use heating
                print("Switch On heating")
                switch_led("H")
        elif self.status =="cooling":
            if temperature > self.ac_settings[self.status]["min_temp"]:
                #Turn off ability to use cooling
                print("Switch on cooling")
                switch_led("H")
            if temperature < self.ac_settings[self.status]["min_temp"]:
                #Turn on ability to use cooling
                print("Switch off cooling")
                switch_led("L")

    def kelvin2celsius(self,temp):
        """
        Convert Kelvin to Celsius
        """
        return temp - 273.15

    def get_outside_weather(self,city):
        """
        Query the open weather api to retrieve information on current weather in the city
        """
        APIKey = os.environ.get('WEATHER_API_KEY')
        meteo = requests.get(f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={APIKey}").json()
        return self.kelvin2celsius(meteo["main"]["temp"])

    def run(self,status="heating"):
        """
        Main function that runs the service
        Paramaters 
		------------
			status : string
				heating or cooling which is active
        """

        self.client.start()
        self.status =status
        self.retrieve_airconditioning_settings()
        #Register on the catalog
        self.sensor.register(self.ip_catalog,self.port_catalog,self.plate)

        #Run for 10 minutes
        #Start measuring
        
        while True:
            humidity,temperature = self.sensor.measure()
            self.apply_corrections(temperature)
            outside_temp = self.get_outside_weather(os.environ.get("CITY"))
            self.build_message(self.sensor,humidity,temperature,outside_temp)
            self.client.myPublish(self.topic,self.msg)
            time.sleep(30)
            

    def end(self):
        self.sensor.deregistrer(self.ip_catalog,self.port_catalog,self.plate)
        self.client.stop()
