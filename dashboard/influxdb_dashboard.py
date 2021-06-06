from MyMQTT import *
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
import json

#InfluxDB settings, add token and org
token = "<token>"
org = "<org>"
bucket = "Car2Safe"
url="https://us-central1-1.gcp.cloud2.influxdata.com"
client = influxdb_client.InfluxDBClient(url=url,token=token,org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)


class InfluxUploader():
    
    def __init__(self, clientID, topic, broker, port, plate=None):
        self.client=MyMQTT(clientID, broker, port, self)
        self.topic=topic
        self.plate = plate

    def run(self):
        self.client.start()
        self.client.mySubscribe(self.topic)

    def end(self):
        self.client.stop()

    def notify(self,topic,msg):
        """
            Function notify: when a message with one of the topic in [aircondition, alcohol_test, window_monitor] is noticed,
            its payload is decomposed and a record in the InfluxDB database is created according to the field of the topic
        """
        payload=json.loads(msg)

        #topic structure smart2safe/raspberry/<plate>/field
        topic_field = topic.split('/')[3] #takes only the last part of the topic

        if topic_field == "aircondition":
            """
                A record with internal,external temperature and humidity is created in the InfluxDB
            """
            temperature = payload["e"][0]["v"]
            humidity = payload["e"][1]["v"]
            outside_temperature = payload["e"][2]["v"]
            outside_humidity = payload["e"][3]["v"]
            p = [influxdb_client.Point("Temperature").field("Internal", temperature),
                influxdb_client.Point("Temperature").field("External", outside_temperature),
                influxdb_client.Point("Humidity").field("Internal", humidity),
                influxdb_client.Point("Humidity").field("External", outside_humidity)
                ]
            write_api.write(bucket=bucket, org=org, record=p)
        
        elif topic_field == "alcohol_test":
            """
                A record with successful or unsuccessful unlock is created in the influxDB 
            """
            alcohol_value = payload["alcohol_value"]
            if alcohol_value < 0.5:
                p = influxdb_client.Point("Unlock").field("Successful", 1)
                write_api.write(bucket=bucket, org=org, record=p)
            elif alcohol_value >= 0.5: 
                p = influxdb_client.Point("Unlock").field("Unsuccessful", 1)
                write_api.write(bucket=bucket, org=org, record=p)

        elif topic_field == "window_monitor":
            """
                A record with the accident is created in the influxDB 
            """
            if payload["e"][0]["v"] == True:
                p = influxdb_client.Point("Damages").field("Damages", 1)
                write_api.write(bucket=bucket, org=org, record=p)



