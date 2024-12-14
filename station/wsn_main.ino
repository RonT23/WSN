#include <Wire.h>
#include <SoftwareSerial.h>
#include <Adafruit_AM2315.h>
#include <Adafruit_BMP280.h>

#define SILENT

Adafruit_AM2315 am2315;
Adafruit_BMP280 bmp280;

SoftwareSerial gsmGprs(2, 3); 

#define C_GSM_MODE  0
#define C_WIFI_MODE 1

const unsigned BMP_I2C_ADDR = 0x76; // bmp280
//const unsigned BMP_I2C_ADDR = 0x77 // bmp180

// server interface
const String BASE_URL               = "<your servers base url>";
const String TELEMETRY_HANDLER_PATH = "/telemetry.php?";
const String DATA_HANDLER_PATH      = "/store_data.php?";

const String STATION_ID        = "st00"; 

const unsigned int SAMPLE_PERIOD = 60000;

const float DIR_ANGLE[]   = {112.5, 67.5, 90.0, 157.5, 135.0, 202.5, 180.0, 22.5, 45.0, 247.5, 225.0, 337.5, 0.0, 292.5, 315.0, 270.0};
const int   DIR_VAL_MIN[] = {63, 80, 89, 120, 175, 232, 273, 385, 438, 569, 613, 667, 746, 812, 869, 931};
const int   DIR_VAL_MAX[] = {69, 88, 98, 133, 194, 257, 301, 426, 484, 612, 661, 737, 811, 868, 930, 993};
const float SPEED_PER_TICK_PER_SECOND = 2.4;
const float GAUGE_CAPACITY = 0.2974;

// resistors for embedded voltage and current monitors 
const float R6  = 10000;
const float R7  = 4300;
const float R9  = 10000;
const float R10 = 4300;
const float R12 = 100;

// reference values for monitors 
const float VREF = 5.0;
const float I0   = 1.23;
const float Vadc0 = 311.0;

// pinout
const int WIND_DIR_PIN = A0;
const int WIND_SPD_PIN = 19;
const int RAIN_GUG_PIN = 18;
const int CIN_REGULATED= A1;
const int VIN_REGULATED= A2;
const int VIN_SOLAR    = A3;
const int GSM_GPRS_PWR = 7;

unsigned long LAST_READ_ANEM = 0;
unsigned long LAST_READ_RAIN = 0;
const int DEBOUNCE_TIME = 100;

// Interrupt related
volatile int windTickCount = 0;
volatile int rainTickCount = 0;

void reset_board() {
  asm volatile("jmp 0x0000");
}

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

String input_string = "";
int transmission_mode = C_WIFI_MODE;

void AM2315_temperatureAndHumidity(float *temperature, float *humidity){
  if(!am2315.readTemperatureAndHumidity(temperature, humidity)){ 
    #ifndef SILENT
      Serial.println("[Error] Failed to read from AM2315"); 
    #endif
  }  
}

float windDirection(void){
  int analog_val = analogRead(WIND_DIR_PIN);
  int values = sizeof(DIR_ANGLE) / sizeof(float);
  for(int i=0; i<values; i++){
    if( (analog_val >= DIR_VAL_MIN[i]) && (analog_val <= DIR_VAL_MAX[i]) ){ 
      return DIR_ANGLE[i]; 
    }
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
  #ifndef SILENT
    Serial.println("[Info] Enabling GPRS");
  #endif

  gsm_set("AT+CFUN=1");
  gsm_set("AT+CGATT=1");
  gsm_set("AT+SAPBR=3,1,\"Contype\",\"GPRS\"");
  gsm_set("AT+SAPBR=3,1,\"APN\", \"internet\"");
  gsm_set("AT+SAPBR=1,1");
  gsm_set("AT+SAPBR=2,1");
  gsm_set("AT+CLTS=1");

  #ifndef SILENT
    Serial.println("[Info] GPRS ready");
  #endif
}

void HTTPtransfer(const String BaseURL, const String path, String val){
  #ifndef SILENT
    Serial.println("[Info] HTTP transmission");
  #endif

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
  
  #ifndef SILENT
    Serial.println("[Info] Transmission Complete");
  #endif
}

bool parseCmdArg(String input_str, int &cmd, int &arg) {
  // Check if the string starts with '$' and ends with '$'
  if (!input_str.startsWith("$") || !input_str.endsWith("$")) {
    return false;
  }

  // Remove the leading '$' and trailing '$'
  input_str = input_str.substring(1, input_str.length() - 1);

  // Find the position of the comma
  int commaIndex = input_str.indexOf(",");
  if (commaIndex == -1) {
    return false; 
  }

  // Extract the command and argument substrings
  String cmdStr = input_str.substring(0, commaIndex);
  String argStr = input_str.substring(commaIndex + 1);

  cmdStr.trim();
  argStr.trim();

  // Convert the substrings to integers
  cmd = cmdStr.toInt();
  arg = argStr.toInt();

  return true;
}

void transmit_values(int transmission_mode, String server_url, String handler, String val) {
  switch(transmission_mode){
    case C_WIFI_MODE :
      // simply send to main serial interface
      Serial.println(val);
      break;
    
    case C_GSM_MODE:
      // program GSM module
      GPRS_enable();
      HTTPtransfer(server_url, handler, val);
      break;
    
    default:
      // by default use the main serial output
      Serial.println(val);
      break;
  }  
}

void setup() {
  Serial.begin(115200);
  
  while(!Serial){ 
    delay(100); 
  }

  #ifndef SILENT
    Serial.println("[Info] System Started");
  #endif
  
  if(!am2315.begin()){ 
    #ifndef SILENT
      Serial.println("[Error] AM2315 Sensor Not Found!"); 
    #endif

    while(!am2315.begin()){}
  }
  delay(2000);
  
  #ifndef SILENT
    Serial.println("[Info] AM2315 Started");  
  #endif 

  if(!bmp280.begin(BMP_I2C_ADDR)){ 
    #ifndef SILENT
      Serial.println("[Error] BMP280 Sensor Not Found!"); 
    #endif 
    while(!bmp280.begin(BMP_I2C_ADDR)){}  
  }

  delay(1000);

  #ifndef SILENT
    Serial.println("[Info] BMP280 Started");
  #endif

  pinMode(WIND_DIR_PIN, INPUT);
  
  #ifndef SILENT
    Serial.println("[Info] Wind Direction Sensor Started");
  #endif

  pinMode(WIND_SPD_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(WIND_SPD_PIN), ISR_windTickCnt, FALLING);
  
  #ifndef SILENT
    Serial.println("[Info] Anemometer Started");
  #endif 

  pinMode(RAIN_GUG_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RAIN_GUG_PIN), ISR_rainTickCnt, RISING);
  
  #ifndef SILENT
    Serial.println("[Info] Rain Gauge Started");
  #endif

  pinMode(CIN_REGULATED, INPUT);
  
  #ifndef SILENT
    Serial.println("[Info] Current Monitor Started");
  #endif

  pinMode(VIN_REGULATED, INPUT);
  
  #ifndef SILENT
    Serial.println("[Info] Internal Voltage Monitor Started");
  #endif

  pinMode(VIN_SOLAR, INPUT);
  
  #ifndef SILENT
    Serial.println("[Info] Solar Panel Voltage Monitor Started");
  #endif

  gsmGprs.begin(19200);
  
  delay(1000);

  #ifndef SILENT
    Serial.println("[Info] Initializing GSM Module...");
  #endif 

  pinMode(GSM_GPRS_PWR, OUTPUT);
  gsmGprs.flush();
  
  digitalWrite(GSM_GPRS_PWR, HIGH); 
  delay(10000);
  
  gsmGprs.flush();

  #ifndef SILENT
    Serial.println("[Info] GSM Module Initialized!");
  #endif
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

  // read and decode command
  while (Serial.available() > 0) {
    char incomingChar = (char)Serial.read();    
    if (incomingChar == '\n') { // command line finished           
      #ifndef SILENT
        Serial.print("[INFO] Data input : ");
        Serial.println(input_string);
      #endif

      int cmd, arg;
      parseCmdArg(input_string, cmd, arg);
      input_string = "";

      #ifndef SILENT
        Serial.print("[INFO] Received input command: ");
        Serial.println(cmd + " ," + arg);
      #endif

      switch(cmd) {
        case 0: 
          reset_board();
          break;
        case 1:
        case 2:
        case 3:
          switch(arg){
            case 0:
              transmission_mode = C_GSM_MODE;
              break;
            case 1:
              transmission_mode = C_WIFI_MODE;
              break;
            default:
              transmission_mode = C_WIFI_MODE;
              break;
          }
      }
    } else {
      // reset the input data container 
      input_string += incomingChar;
    }
  }

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

    #ifndef SILENT
      Serial.print("[Info] HTTP Value : "); 
      Serial.println(val);
    #endif

    transmit_values(transmission_mode, BASE_URL, DATA_HANDLER_PATH, val);

    // read station state
    internal_temperature = bmp280.readTemperature();
    internal_voltage = voltageMonitor(VIN_REGULATED, R6, R7);
    solar_panel_voltage = voltageMonitor(VIN_SOLAR, R9, R10);
    internal_current = currentMonitor(CIN_REGULATED, Vadc0, I0);

    val = "&st="+STATION_ID+"&t="+String(internal_temperature)+"&v="+String(internal_voltage)+"&i="+String(internal_current)+"&sv="+String(solar_panel_voltage)+"&hb="+String(heartbeat)+"&m="+String(op_mode);
    
    #ifndef SILENT
      Serial.print("[Info] HTTP Value : "); 
      Serial.println(val);
    #endif

    transmit_values(transmission_mode, BASE_URL, TELEMETRY_HANDLER_PATH, val);

    // update state
    state = true;
    fin_time = millis();

    // debugging serial print
    #ifndef SILENT
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
    #endif
  }
}

