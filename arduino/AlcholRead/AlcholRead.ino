#define MQ5_pin A0

#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

byte mac[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED };

EthernetClient ethClient;
PubSubClient mqttclient(ethClient);


float sensorValue = 0.0;
float sensor_volt = 0.0;
int i = 0;
float RS_gas = 0.0;
float ratio = 0.0;
double ppm = 0;
float Parameters[2] = {67617.7708232563600177 , -4.5532521098947267};
int buttonpin = 5;
int val;
float max_ppm = 0.0;
int sec = 0;



void setup() {
  Serial.begin(9600);
  delay(1500);
  pinMode(MQ5_pin, INPUT);
  pinMode(buttonpin, INPUT);
  Ethernet.begin(mac);

  //IP and PORT of the catalog
  int    HTTP_PORT   = 80;
  char   HOST_NAME[] = "4504483a2bfe.ngrok.io"; //exposition of catalog through ngrok
  String PATH_NAME   = "/car";
  String HTTP_METHOD = "POST";


  //REGISTRATION TO THE CATALOG THROUGH POST

  // Connect to HTTP server
  EthernetClient ethClient;
  ethClient.setTimeout(10000);
  if (!ethClient.connect(HOST_NAME, HTTP_PORT)) {
    Serial.println(F("Connection failed"));
    return;
  }

  Serial.println(F("Connected!"));

  //build HTTP body
  String msg = "{\"plate\":\"AX1245531\",\"device\":\"arduino\",\"sensor\":\"MQ5\",\"measure_type\": \"alcohol in blood\",\"sensor_id\":\"MQ5-S1\",\"topic\": \"smart2safe/arduino/alcohol_test\",\"serviceType\":\"MQTT\"}";


  // Send HTTP request (build the HTTP Header)
  ethClient.println(HTTP_METHOD + " " + PATH_NAME + " HTTP/1.1");
  ethClient.println("Host: " + String(HOST_NAME));
  ethClient.println("Content-Type: application/json");
  ethClient.print("Content-Length: ");
  ethClient.println(msg.length() + 2);
  ethClient.println("Connection: close");
  ethClient.println(); // end HTTP header
  if (ethClient.println() == 0) {
    Serial.println("Failed to send request");
    ethClient.stop();
    return;
  }

  // send HTTP body
  ethClient.println(msg);

  //Disconnect from server
  ethClient.stop();


  //OBTAINING BROKER URL FROM THE CATALOG THROUGH HTTP GET
  HTTP_METHOD = "GET";
  PATH_NAME   = "/broker";


  Serial.println(F("Connecting..."));

  // Connect to HTTP server
  ethClient.setTimeout(10000);
  if (!ethClient.connect(HOST_NAME, HTTP_PORT)) {
    Serial.println(F("Connection failed"));
    return;
  }

  Serial.println(F("Connected!"));

  //Send HTTP request (build HTTP header)
  ethClient.println(HTTP_METHOD + " " + PATH_NAME + " HTTP/1.1");
  ethClient.println("Host: " + String(HOST_NAME));
  ethClient.println("Connection: close");
  ethClient.println(); // end HTTP header
  if (ethClient.println() == 0) {
    Serial.println("Failed to send request");
    ethClient.stop();
    return;
  }


  // Check HTTP status
  //  char status[32] = {0};
  //  ethClient.readBytesUntil('\r', status, sizeof(status));
  //  if (strcmp(status, "HTTP/1.1 200 OK") != 0) {                // commentato per recuperare spazio
  //    Serial.print("Unexpected response: ");
  //    Serial.println(status);
  //    ethClient.stop();
  //    return;
  //  }

  // Skip HTTP headers
  char endOfHeaders[] = "\r\n\r\n";
  if (!ethClient.find(endOfHeaders)) {
    Serial.println("Invalid response");
    ethClient.stop();
    return;
  }

  // Allocate the JSON document
  // Use arduinojson.org/v6/assistant to compute the capacity.
  StaticJsonDocument<96> brokerJSON;

  // Parse JSON object
  DeserializationError error = deserializeJson(brokerJSON, ethClient);
  //  if (error) {
  //    Serial.print(F("deserializeJson() failed: "));    //commentato per recuperare spazio
  //    Serial.println(error.f_str());
  //    ethClient.stop();
  //    return;
  //  }


  const char* broker_IP = brokerJSON["broker"]["broker"]; // "broker.mqttdashboard.com"

  // Disconnect from server
  ethClient.stop();


  // CONNECT MQTT CLIENT
  //takes as inputs the broker IP and port
  mqttclient.setServer(broker_IP, 1883);
  //connect the clientID s2s_ard to the "server"
  mqttclient.connect("s2s_ard");
}

void loop() {

  val = digitalRead(buttonpin);
  if (val == LOW && sec <= 20) // the user must push the button for at least 20 seconds
  {
    //media valori su 100 campioni
    for (i = 0 ; i < 100 ; i++) {
      sensorValue += analogRead(MQ5_pin);
      delay(10);
    }

    sensorValue = sensorValue / 100;
    sensor_volt = sensorValue / 1024 * 5;
    RS_gas = (5.0 - sensor_volt) * 10000 / sensor_volt;
    ratio = RS_gas / 41317.25; //R0
    //conversione in ppm
    ppm = Parameters[0] * pow(ratio, Parameters[1]);

    Serial.println(ppm);

    if (ppm > max_ppm)
    {
      max_ppm = ppm;
      Serial.println(F("max"));
    }
    sec += 1;
  }
  if (sec > 20)
  {

    String msg = "{\"bn\":\"MQ-5\",\"e\":[{\"n\":\"Blood Alcohol Level\",\"u\":\"/\",\"v\":" + String(max_ppm / 1000000) + "}]}";
    char buffer[msg.length() + 1];
    msg.toCharArray(buffer, msg.length());

    //MQTT publish
    mqttclient.publish("smart2safe/arduino/alcohol_test", buffer);
    return;
  }
}
