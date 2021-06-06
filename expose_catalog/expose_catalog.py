# Author: Francesco Conforte s277683
# Academic year: 2020-21

import json
from datetime import datetime

import cherrypy

#HOST = "0.0.0.0"
HOST = "localhost"
PORT = 9090

class WebServiceCatalog():
	""" Class implementing a web service which exposes the catalog,
	enabling external actors to retrieve information from it and update it.
	Methods
	-------------
		GET( *uri, **params)
			an http method GET used to return information from the catalog json file,
			thanks to parameters passed through URL of get request
		
		POST(*uri, **params) 
			an http method POST used to update the catalog json file,
			with parameters passed through URL of POST request	
		
		DELETE( *uri, **params) 
			an http method DELETE used to remove from the catalog json file,
			devices and sensors which are leaving the system
		
	"""
	exposed = True
	def __init__(self,fileName):
		self.fileName=json.load(open(fileName))

	def GET(self, *uri, **params):
		"""
		Http GET method that based on the uri parameters passed during the Client request,
        returns data from the catalog json file.
		Paramaters 
		------------
			*uri : list
				list of elements in the request format, enclosed in / / after the port specification
			**params :dict
				dictionary of parameters passed in a 'key-value' format after the ? character in the URL
		"""
		print("Get received")
		uri=list(uri)

		#access in an easier way the catalog	
		catalog = self.fileName["smart2safe"]
		
		if uri[0] == "arduino": #uri to get the list of sensors connected to arduino @http://catalog_IP:catalog_port/arduino?plate=number_of_plate
			if params != {}:
				plate = params["plate"]
				for item in catalog:
					if "cars" in item:
						c = item 
						break
				for item in c["cars"]:
					if item["plate"] == plate:
						dev = item["devices"]
						arduino = dev["arduino"]
						c = arduino
			else: 
				raise cherrypy.HTTPError("404 Not Found", "Resource not available. Check if the inserted params are correct")


		elif uri[0] == "rpi": #uri to get the list of sensors connected to rpi @http://catalog_IP:catalog_port/rpi?plate=number_of_plate
			if params != {}:
				plate = params["plate"]
				for item in catalog:
					if "cars" in item:
						c = item 
						break
				for item in c["cars"]:
					if item["plate"] == plate:
						dev = item["devices"]
						rpi = dev["rpi"]
						c = rpi
			else: 
				raise cherrypy.HTTPError("404 Not Found", "Resource not available. Check if the inserted params are correct")
		
		elif uri[0] == "carlist": #uri to get a list of all the current available cars			
			for item in catalog:
				if "cars" in item:
					c = item
					break
			
			#create a list of plates of available cars
			plates = [item["plate"] for item in c["cars"] if item["available"]]
			c = plates


	# Loop to get what is in the catalog according to the asked uri (useful at scalability of the project):
		# "ac": return the threasholds for air conditioning;
		# "th_alc": return the threasholds for alcohol;
		# "bot": return ip and port of the bot;
		# "broker": return ip and port of the broker;
		# "cars": return the whole list of cars with all their information (UNUSED IN THE PROJECT BUT IMPLEMENTED)
		else: 			
			c = None
			for item in catalog:
				if uri[0] in item:
					c = item
					break
			if c==None: #if nothing is found according to the asked uri, raise the error 404
				raise cherrypy.HTTPError("404 Not Found", "Resource not available.")

		#return the requested information
		return json.dumps(c, indent=4)
        
	
	def POST(self, *uri):
		"""Http POST method, according to the uri passed during the Client request,
		updates the Catalog json file. The information stored in catalog json file
		that can be updated are the sensors connected to rpi and arduino and availability of cars
		
		Paramaters 
		------------
			*uri : tuple
				list of elements in the request format, enclosed in / / after the port specification
					
		"""
		print("Post Received")
		uri=list(uri)
		
		#read the body of the post request
		requestBody=cherrypy.request.body.read()
		
		#convert the string in a json
		jsonBody = json.loads(requestBody)
		
		#make adjustment to get in the catalog more easily
		catalog = self.fileName["smart2safe"]		
		if uri[0] == "car":  # post request @ http://ip_catalog:port_catalog/car
			# save what has been retrieved from the post request
			plate = jsonBody["plate"] # car plate
			device = jsonBody["device"] # either rpi or arduino
			sensor_name = jsonBody["sensor"] # name of sensor (MQ-5, DHT11, DFR0027)
			measure_type = jsonBody["measure_type"] #(alcohol level, humidity, temperature)
			sensor_id = jsonBody["sensor_id"] # an id number 
			topic = jsonBody["topic"] #topic where to find
			service_type = jsonBody["serviceType"] #either MQTT or REST

			#access in an easier way the catalog
			for item in catalog:
				if "cars" in item:
					catalog = item 
					break

			# check if the car is already registered into the catalog otherwise insert 
			# a new one with the right plate
			plates = [p["plate"] for p in catalog["cars"]]
			if plate in plates:
				for p in catalog["cars"]:
					if p["plate"] == plate:
						#check if the sensor already exists	in the catalog
						sensors = [i["sensorID"] for i in p["devices"][device]]	
						if sensor_id not in sensors:			
							sensor_to_insert = {

									"sensorName": sensor_name,  
									"measure_type": measure_type,
									"sensorID": sensor_id,
									"servicesDetails": [
										{
										"topic": topic,
										"serviceType": service_type,
										}
									],
									"lastUpdate": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
								}
							p["devices"][device].append(sensor_to_insert)
							self.fileName["lastUpdate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
			else:
				new_car = {}
				new_car["plate"] = plate
				new_car["available"] = True
				new_car["devices"] = {
					"rpi": [],
					"arduino":[]
				}
				sensor_to_insert = {

								"sensorName": sensor_name, 
								"measure_type": measure_type,
								"sensorID": sensor_id,
								"servicesDetails": [
									{
									"topic": topic,
									"serviceType": service_type,
									}
								],
								"lastUpdate": datetime.now().strftime("%Y/%m/%d %H:%M:%S")
							}
				new_car["devices"][device].append(sensor_to_insert)
				catalog["cars"].append(new_car)
				self.fileName["lastUpdate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
			with open("./jsons/catalog.json","w+", encoding='utf-8') as f:
				json.dump(self.fileName, f, ensure_ascii=False, indent=4)
		
		elif uri[0]=="booking": # post request @ http://ip_catalog:port_catalog/booking to set the car as booked
			
			#retrieve data from the body of the post
			plate = jsonBody["plate"]

			#access in an easier way the catalog
			for item in catalog:
				if "cars" in item:
					catalog = item 
					break

			# set the flag of car availability to false, meaning that it's been booked and currently unavailable
			for i in catalog["cars"]:
				if i["plate"] == plate:
					i["available"] = False
					self.fileName["lastUpdate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
			
			#save modification
			with open("./jsons/catalog.json","w+", encoding='utf-8') as f:
				json.dump(self.fileName, f, ensure_ascii=False, indent=4)		

		elif uri[0]=="deletebooking": # post request @ http://ip_catalog:port_catalog/deletebooking to set the car as available
			
			#retrieve data from the body of the post
			plate = jsonBody["plate"]

			#access in an easier way the catalog
			for item in catalog:
				if "cars" in item:
					catalog = item 
					break

			# set the flag of car availability to true, meaning that the car is now available again
			for i in catalog["cars"]:
				if i["plate"] == plate:
					i["available"] = True
					self.fileName["lastUpdate"] = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
			
			#save modification
			with open("./jsons/catalog.json","w+", encoding='utf-8') as f:
				json.dump(self.fileName, f, ensure_ascii=False, indent=4)
		
		return
			
		
	def DELETE(self, *uri, **params):
		"""Http DELETE method that, basing on the uri parameters passed during the Client request,
		updates the catalog json file. In this case it is used to remove from the catalog and disconnect 
		from the system the 'alcohol test' sensor running on Arduino when the engine starts and all the 
		other sensors (windows monitorer and air conditioning controller) when they are no more useful.
		Paramaters 
		------------
			*uri : tuple
				list of elements in the request format, enclosed in / / after the port specification
			**params : dict
				dictionary of parameters passed in a 'key-value' format after the ? character in the URL
		
		"""

		uri = list(uri)
		

		# make adjustment to get in the catalog more easily
		catalog = self.fileName["smart2safe"]
		if uri[0] == "close": # perform a delete request @http://ip_catalog:port_catalog/close?plate=number_of_plate&sensor_id=sensor_name
			
			for item in catalog: #access to cars dictionary of catalog (catalog is a list of dicts)
				if "cars" in item:
					catalog = item 
					break
			for p in catalog["cars"]: # find the right plate
				print(p["plate"],"==",params["plate"])
				if p["plate"] == params["plate"]:
					for i,element in enumerate(p["devices"]["rpi"]):
						if element["sensorName"] == params["sensor_id"]:
							del p["devices"]["rpi"][i] #empty the list removing the asked sensor
						elif element["sensorID"] == params["sensor_id"]:
							del p["devices"]["rpi"][i] #empty the list removing the asked sensor
		elif uri[0] == "start":# perform a delete request @http://ip_catalog:port_catalog/start?plate=number_of_plate 
			for item in catalog: #access to cars of catalog (catalog is a list of dicts)
				if "cars" in item:
					catalog = item 
					break
			for p in catalog["cars"]: #find the right plate
				if p["plate"] == params["plate"]:
					p["devices"]["arduino"] = [] #empty the list removing the alcohol level sensor from the network
		
		return json.dump(self.fileName,open("./jsons/catalog.json","w+"),indent=4)




# __main__
if __name__=="__main__":
	conf={
		"/":{
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True,
		}
	}

	cherrypy.tree.mount(WebServiceCatalog("./jsons/catalog.json"), "/", conf)
	cherrypy.server.socket_host = HOST
	cherrypy.server.socket_port = PORT
	cherrypy.engine.start()
	cherrypy.engine.block()