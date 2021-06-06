#!/usr/bin/python
# Author: Matteo Mastrota s274926
# Academic year: 2020-21

#import adafruit_dht
#import RPi.GPIO as GPIO
import requests
import time
import json
from lib.MyMQTT import *
import namegenerator
from scipy.fft import rfft, rfftfreq
from scipy.io import wavfile
import numpy as np
import wave
import pyaudio

SAMPLE_RATE = 44100  # Hertz
'''
def switch_led(level="L"):
    """
    Simulate alarm using a led
    """
    GPIO.setmode(GPIO.BCM)
    PIN = 18
    if level=="H":
        GPIO.output(PIN,GPIO.HIGH)
        print("Switch back on")
    else:
        GPIO.output(PIN,GPIO.LOW)
        print("Switch off")
'''

class Microphone:
    def __init__(self,plate,sensor_type = "Microphone",WAVE_OUTPUT_FILENAME = "output.wav",CHUNK = 1024,CHANNELS = 2,RATE = 16000,RECORD_SECONDS = 5):
        self.plate=plate
        self.sensor_name = sensor_type
        self.sensor_id = sensor_type+"-"+plate
        self.CHUNK = CHUNK
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = CHANNELS
        self.RATE = RATE
        self.RECORD_SECONDS = RECORD_SECONDS
        self.WAVE_OUTPUT_FILENAME = WAVE_OUTPUT_FILENAME

    def get_audio(self):
        """
        Register audio of the surrounding and save the file for processing

        Output 
		------------
			Success : bool
				true if the recording was successful
			filename: string
				name of the file where the audio was stored
        """
        try:
            p = pyaudio.PyAudio()
            #Open audio stream
            stream = p.open(format=self.FORMAT,
                            channels=self.CHANNELS,
                            rate=self.RATE,
                            input=True,
                            frames_per_buffer=self.CHUNK,
                            input_device_index=4)

            print("* recording")

            frames = []

            for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                data = stream.read(self.CHUNK)
                frames.append(data)

            print("* done recording")
            #Close the stream
            stream.stop_stream()
            stream.close()
            p.terminate()
            #Save file
            self.save_audio (frames,p)
            return True,self.WAVE_OUTPUT_FILENAME

        except Exception as e:
            print(e)
            print('Failed to get recording. Trying again!')
            return False,None
    
    def save_audio(self,frames,p):
        """
        This function takes a recorded stream (FRAMES) and save it in the correct format in a wav file
        Paramaters 
		------------
			frames : list
				list of chunk registered in the request format, enclosed in / / after the port specification
			p : pyaudio
				pyaudio object used to take the audio
		
        """
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def register(self,ip_catalog, port_catalog,plate):
        """
        Register sensor on the catalog when first launched
        """
        gb_URL="http://" + ip_catalog + ":" + port_catalog + "/car"
        body = {"plate": plate, "device":"rpi","sensor":self.sensor_name,"measure_type":["glass_infraction"],
                "sensor_id":self.sensor_id,"serviceType": "MQTT", "topic":"smart2safe/raspberry/"+plate+"/window_monitor"}
        status = requests.post(gb_URL, data = json.dumps(body))
        print(body)
        print(status)

    def deregistrer(self,ip_catalog, port_catalog,plate):
        """
        Deregister sensor on the catalog
        """
        ac_URL="http://" + ip_catalog + ":" + port_catalog + "/close?plate="+plate+"&sensor_id="+self.sensor_id
        requests.delete(ac_URL)

class Glass_break:
    def __init__(self, clientID, topic, broker, port, sensor, ip_catalog='172.20.10.11', port_catalog='9090',plate="AX1245531"):
        self.client=MyMQTT(clientID, broker, port, self)
        self.topic=topic
        self.ip_catalog=ip_catalog
        self.port_catalog=port_catalog
        self.sensor = sensor
        self.plate = plate
    
    def build_message(self,sensor,status):
        """
        build message in senML format ready to be published

        Paramaters 
		------------
			sensor : Microphone object
				sensor object that collect the information
			status : bool
				true when sending an alarm
        """
        self.msg={"bn":sensor.sensor_name, "e":[{"n":"glass_infraction","u":"Bool","t":time.time(),"v":status}]}

    def retrieve_settings(self):
        """method to retrieve settings from the catalog through
        requests module and get method

        Returns:
            [dict]: returns the json dictionary containing the settings recovered 
                    from the catalog
        """
        ac_URL="http://" + self.ip_catalog + ":" + self.port_catalog + "/glass_break"
        self.ac_settings=requests.get(ac_URL).json() 
        print(self.ac_settings)
        print("Type settings: ",type(self.ac_settings))
        return self.ac_settings

    def call_bot(self,bot_IP):
        """
        This method notify the telegram service of the incident throuh a post API
        Paramaters 
		------------
			bot_IP : string
				endpoint of the telegram service
        """
        #build the request
        bot_URL="http://" + bot_IP + "/contactChannel"
        body = {"type": "alarm", "data":{"plate": self.plate,"message":"left window broken"} }
        try:
            print(json.dumps(body))
            #Send the alarm
            status = requests.post(bot_URL, data = json.dumps(body))
            print(status)
        except Exception as e:
            print(e)
            status=""
        return status

    def isBreakingSound(self,filename):
        '''
        This method will read an audio file and process it to determine if it's a breaking sound.

        The audio is analysed computing the one-dimensional discrete Fourier Transform for real input. 
        In order to discerne the type of sound we observe the distribution of power on the spectrum after normalizing it.

        In the frequency domain we apply a pass band filter (2000-5000 Hz) to isolate the band containing the information
        We compare the sum of the power over the three major frequencies with a threashold to categorize the sound.

        Paramaters 
		------------
			filename : string
				name of the file to process
        '''
        w = wave.open(filename)
        print(filename, "SAMPLE: ",w.getsampwidth())
        fs,data = wavfile.read(filename)
        
        #Check for number of channel in script
        if data.ndim>1:
            length = len(data.T[0])
            yf = rfft(data.T[0])
        else:
            length = len(data.T)
            yf = rfft(data.T)
        xf = rfftfreq(length, 1 / fs)
    
        test =  np.abs(yf)/np.max(np.abs(yf)) #sum over area percentage of power
        idx = np.argmax(np.abs(yf))

        #Filter
        points_per_freq = len(xf) / (SAMPLE_RATE / 2)
        # Our target frequency is 2000-5000 Hz
        min_target_idx = int(points_per_freq * 2000)
        max_target_idx = int(points_per_freq * 5000)
        
        test[:min_target_idx - 1] = 0
        test[max_target_idx + 2:] = 0

        threashold_value = np.sum(np.sort(np.abs(test),0)[::-1][:2])
        print(threashold_value)
        if threashold_value > 0.9:
            print(f"{filename} is a breaking Window")
            return True
        else:
            print(f"{filename} NOT a breaking Window")
            return False

    def run(self,use_mic = False,bot_IP="127.0.0.1"):
        """
        Main function that runs the service
        Paramaters 
		------------
			use_mic : bool
				Determine wheter to use examples file or the usb microphone
            bot_IP: string
                endpoint of the telegram service
        """
        self.client.start()
        #Register on the catalog
        self.sensor.register(self.ip_catalog,self.port_catalog,self.plate)
        
        if not use_mic:
            # If not using a mic read wav files
            #Add list of files to be considered
            files = ["wav-files/mumbai-traffic.wav","wav-files/tanger-park-chatting.wav","wav-files/window-break1.wav","wav-files/window-break2.wav","wav-files/window-break3.wav","wav-files/car-horn2.wav","wav-files/car-horn.wav"]
            files.append("wav-files/child-talking.wav")
            files.append("wav-files/talking.wav")
            files.append("wav-files/people-talking.wav")
            files.append("wav-files/piccadilly-circus-ambience.wav")
            files.append("wav-files/tanger-park-chatting.wav")
            for f,z in zip(files,range(len(files))):
                if(self.isBreakingSound(f)):
                    self.call_bot(bot_IP)
                    self.build_message(self.sensor,True)
                    self.client.myPublish(self.topic,self.msg)
                time.sleep(30)
        if use_mic:
            #Get the audio
            output,f = self.sensor.get_audio()
            if output:
                #If recording was successful process it
                if(self.isBreakingSound(f)):
                    #If it was determined to be an alarm notify the administrator and shut down
                    self.call_bot(bot_IP)
                    self.build_message(self.sensor,True)
                    self.client.myPublish(self.topic,self.msg)
                    return

    def end(self):
        self.sensor.deregistrer(self.ip_catalog,self.port_catalog,self.plate)
        self.client.stop()
