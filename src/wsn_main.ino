#include <Wire.h>
#include <SoftwareSerial.h>
#include <Adafruit_AM2315.h>
#include <Adafruit_BMP280.h>

Adafruit_AM2315 am2315;
Adafruit_BMP280 bmp280;

SoftwareSerial gsmGprs(2, 3); 
//SoftwareSerial gsmGprs(8, 7); // for the new GSM module


const unsigned int BMP_I2C_ADDR 0x76 // bmp280
//const unsigned int BMP_I2C_ADDR 0x77 // bmp180

// server
const String BASE_URL               = "http://uoa-wsn.i-met.gr/station";
const String TELEMETRY_HANDLER_PATH = "/telemetry.php?";
const String DATA_HANDLER_PATH      = "/store_data.php?";

 const String STATION_ID        = "st00"; /* Psachna */
// const String STATION_ID        = "st01";  /* Athens
// const String STATION_ID        = "st02"; /* Unlocated */

// constants
const unsigned int SAMPLE_PERIOD = 60000; // one minute, multiplied in the code

const float DIR_ANGLE[]   = {112.5, 67.5, 90.0, 157.5, 135.0, 202.5, 180.0, 22.5, 45.0, 247.5, 225.0, 337.5, 0.0, 292.5, 315.0, 270.0};
const int   DIR_VAL_MIN[] = {63, 80, 89, 120, 175, 232, 273, 385, 438, 569, 613, 667, 746, 812, 869, 931};
const int   DIR_VAL_MAX[] = {69, 88, 98, 133, 194, 257, 301, 426, 484, 612, 661, 737, 811, 868, 930, 993};
const float SPEED_PER_TICK_PER_SECOND = 2.4;
const float GAUGE_CAPACITY = 0.2974;

// resistors for embedded monitors 
const float R6  = 10000;
const float R7  = 4300;
const float R9  = 10000;
const float R10 = 4300;
const float R12 = 100;

// reference values for monitors 
const float VREF = 5.0;
const float I0   = 1.23;
const float Vadc0 = 311.0;

// pins
const int WIND_DIR_PIN = A0;
const int WIND_SPD_PIN = 19;
const int RAIN_GUG_PIN = 18;
const int CIN_REGULATED= A1;
const int VIN_REGULATED= A2;
const int VIN_SOLAR    = A3;
const int GSM_GPRS_PWR = 7; // comment for new GSM module

unsigned long LAST_READ_ANEM = 0;
unsigned long LAST_READ_RAIN = 0;
const int DEBOUNCE_TIME = 100;

// Interrupt related
volatile int windTickCount = 0;
volatile int rainTickCount = 0;

void ISR_windTickCnt(void){
  if( (long)(micros() - LAST_READ_ANEM) >= DEBOUNCE_TIME){
    windTickCount += 1;
    LAST_READ_ANEM = micros();  
  }
}

void ISR_rainTickCnt(void){
  if( (long)(micros() - LAST_READ_RAIN) >= DEBOUNCE_TIME){
    rainTickCount += 1;
    LAST_READ_RAIN = micros();
  }
}

// State variables
long unsigned int heartbeat = 0;
int state = true;
unsigned long init_time = 0.0;
unsigned long fin_time  = 0.0;
unsigned int op_mode = 1.0;

void AM2315_temperatureAndHumidity(float *temperature, float *humidity){
  if(!am2315.readTemperatureAndHumidity(temperature, humidity)){ Serial.println("[Error] Failed to read from AM2315"); }  
}

float windDirection(void){
  int analog_val = analogRead(WIND_DIR_PIN);
  int values = sizeof(DIR_ANGLE) / sizeof(float);
  for(int i=0; i<values; i++){
    if( (analog_val >= DIR_VAL_MIN[i]) && (analog_val <= DIR_VAL_MAX[i]) ){ return DIR_ANGLE[i]; }
  }
}

float windSpeed(double dt){
  float windSpd = (windTickCount * SPEED_PER_TICK_PER_SECOND) * 1000.0 / dt;
  windTickCount = 0;
  return windSpd;
}

float rainRate(double dt){
  float rainRt = (double)(rainTickCount * GAUGE_CAPACITY) * 1000.0 / dt;
  rainTickCount = 0;
  return rainRt;
}

float voltageMonitor(int monitor_pin, int R1, int R2){
    float Vadc = (float)analogRead(monitor_pin);
    float V    = (float)Vadc*VREF / 1025.0;
    float R    = (float)(R1/R2) + 1.0;
    return V*R;
}

float currentMonitor(int monitor_pin, float Vadc0, float I0){
  float Vadc = (float)analogRead(monitor_pin);
  return (float)(Vadc*I0/Vadc0);
}

void gsm_set(String func){
  gsmGprs.println(func);
  delay(500);
  gsmGprs.flush();
}

void GPRS_enable(void){
  Serial.println("[Info] Enabling GPRS");
  gsm_set("AT+CFUN=1");
  gsm_set("AT+CGATT=1");
  gsm_set("AT+SAPBR=3,1,\"Contype\",\"GPRS\"");
  gsm_set("AT+SAPBR=3,1,\"APN\", \"internet\"");
  gsm_set("AT+SAPBR=1,1");
  gsm_set("AT+SAPBR=2,1");
  gsm_set("AT+CLTS=1");
  Serial.println("[Info] GPRS ready");
}

void HTTPtransfer(const String BaseURL, const String path, String val){
  Serial.println("[Info] HTTP transmission");
  gsm_set("AT+HTTPINIT");
  gsm_set("AT+HTTPPARA=\"CID\",1");
  
  gsmGprs.print("AT+HTTPPARA=\"URL\", \"");
  gsmGprs.print(BaseURL);
  gsmGprs.print(path);
  gsmGprs.print(val);

  gsm_set("\"");

  gsm_set("AT+HTTPACTION=0");
  gsm_set("AT+HTTPTERM");
  gsm_set("AT+CIPSHUT");
  Serial.println("[Info] Transmission Complete");
}

void setup() {
  Serial.begin(115200);
  
  while(!Serial){ delay(100); }

  Serial.println("[Info] System Started");

  if(!am2315.begin()){ 
    Serial.println("[Error] AM2315 Sensor Not Found!"); 
    while(!am2315.begin()){}
  }
  delay(2000);
  Serial.println("[Info] AM2315 Started");  

  if(!bmp280.begin(BMP_I2C_ADDR)){ 
    Serial.println("[Error] BMP280 Sensor Not Found!"); 
    while(!bmp280.begin(BMP_I2C_ADDR)){}  
  }

  delay(1000);
  Serial.println("[Info] BMP280 Started");
  
  pinMode(WIND_DIR_PIN, INPUT);
  Serial.println("[Info] Wind Direction Sensor Started");

  pinMode(WIND_SPD_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(WIND_SPD_PIN), ISR_windTickCnt, FALLING);
  Serial.println("[Info] Anemometer Started");

  pinMode(RAIN_GUG_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RAIN_GUG_PIN), ISR_rainTickCnt, RISING);
  Serial.println("[Info] Rain Gauge Started");

  pinMode(CIN_REGULATED, INPUT);
  Serial.println("[Info] Current Monitor Started");

  pinMode(VIN_REGULATED, INPUT);
  Serial.println("[Info] Internal Voltage Monitor Started");

  pinMode(VIN_SOLAR, INPUT);
  Serial.println("[Info] Solar Panel Voltage Monitor Started");

  gsmGprs.begin(19200);
  
  delay(1000);
  Serial.println("[Info] Initializing GSM Module...");

  pinMode(GSM_GPRS_PWR, OUTPUT); // comment for use in the new GSM module
  gsmGprs.flush();
  
  digitalWrite(GSM_GPRS_PWR, HIGH); // comment for use in the new GSM module
  delay(10000);
  
  gsmGprs.flush();
  Serial.println("[Info] GSM Module Initialized!");
}

void loop() {
  
  float air_temperature = 0.0;
  float air_rel_humidity = 0.0;
  float wind_direction = 0.0;
  float wind_speed = 0.0;
  float rain_rate = 0.0;
  float air_pressure = 0.0;

  float internal_voltage = 0.0;
  float internal_current = 0.0;
  float solar_panel_voltage = 0.0;
  float internal_temperature = 0.0;

  String val = "";
  
  if(state){
    init_time = millis();
    state = false;
    heartbeat += 1;
  }

  unsigned long cur_dtime = millis() - fin_time;
  
  if(cur_dtime >= (long)SAMPLE_PERIOD*5){

    // read sensors
    AM2315_temperatureAndHumidity(&air_temperature, &air_rel_humidity); // Celsius, % 
    wind_direction = windDirection();                 // deg from North @ 0
    wind_speed     = windSpeed(millis() - init_time); // m/s
    rain_rate      = rainRate(millis() - init_time);  // mm/s 
    air_pressure   = bmp280.readPressure() / 100.0;   // hPa

    // transmit data 
    val = "&st="+STATION_ID+"&h="+String(air_rel_humidity)+"&t="+String(air_temperature)+"&p="+String(air_pressure)+"&d="+String(wind_direction)+"&r="+String(rain_rate)+"&v="+String(wind_speed);
    Serial.print("[Info] HTTP Value : "); Serial.println(val);

    GPRS_enable();
    HTTPtransfer(BASE_URL, DATA_HANDLER_PATH, val);
    
    // read station state
    internal_temperature = bmp280.readTemperature();
    internal_voltage = voltageMonitor(VIN_REGULATED, R6, R7);
    solar_panel_voltage = voltageMonitor(VIN_SOLAR, R9, R10);
    internal_current = currentMonitor(CIN_REGULATED, Vadc0, I0);

    val = "&st="+STATION_ID+"&t="+String(internal_temperature)+"&v="+String(internal_voltage)+"&i="+String(internal_current)+"&sv="+String(solar_panel_voltage)+"&hb="+String(heartbeat)+"&m="+String(op_mode);
    Serial.print("[Info] HTTP Value : "); Serial.println(val);

    GPRS_enable();
    HTTPtransfer(BASE_URL, TELEMETRY_HANDLER_PATH, val);
    
    // update state
    state = true;
    fin_time = millis();

    // debugging serial print
    Serial.print("[Info] Air Temperature (C) : "); Serial.println(air_temperature); 
    Serial.print("[Info] Air Humidity    (%) : "); Serial.println(air_rel_humidity);
    Serial.print("[Info] Wind Direction (deg): "); Serial.println(wind_direction);
    Serial.print("[Info] Wind Speed  (km/hr) : "); Serial.println(wind_speed);
    Serial.print("[Info] Rain Rate   (mm/hr) : "); Serial.println(rain_rate);
    Serial.print("[Info] Barometric Pressure (hpa): "); Serial.println(air_pressure);
    Serial.print("[Info] Internal voltage (V) : "); Serial.println(internal_voltage);
    Serial.print("[Info] Solar Panel voltage (V) : "); Serial.println(solar_panel_voltage);
    Serial.print("[Info] Internal Current (A) : "); Serial.println(internal_current);
    Serial.print("[Info] Internal Temperature (C)"); Serial.println(internal_temperature);
  }
}

