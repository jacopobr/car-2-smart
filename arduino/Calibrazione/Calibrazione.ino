#define MQ5_pin A0

float Vout;
float RS_air; //  Valore di RS in aria pulita 
float R0;  
float sensorValue = 0;
int i = 0;
float Vin = 5; //bisogna garantire 5 Volt stabili
int RL = 10000; //10k
int campioni = 10000;

void setup() {
  Serial.begin(9600);
}

//effettuo una media su 10000 campioni del segnale di ingresso
void loop() {
  for (i = 0 ; i < campioni ; i++) {
    sensorValue += analogRead(MQ5_pin);
    delay(0.01);
  }
  sensorValue = sensorValue / campioni;
  
  // sensorValue viene scalato in base alla risoluzione del 
  // microcontrollore e al suo livello logico: 
  // i pin analogici lavorano a 10 bit (1024 valori) con 
  // logica a 5 Volt.
  
  Vout = sensorValue / 1024 * Vin;
  RS_air = (Vin - Vout) * RL / Vout;
  R0 = RS_air / 6.5;

  Serial.print("Vout \t \t");                 Serial.print("RS_air \t \t");   Serial.print("R0 \t \t");   Serial.println("RS_air/R0 \t");
  Serial.print(Vout); Serial.print("V \t \t"); Serial.print(RS_air);  Serial.print("\t");       Serial.print(R0);    Serial.print("\t \t");    Serial.println(RS_air / R0);
}
