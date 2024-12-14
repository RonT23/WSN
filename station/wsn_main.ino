#include <WiFi.h>
#include <HTTPClient.h>

#define SILENT // enable this when deployed

const int C_RECONNECT_REPEAT_TIME_MS = 500;

// time to wait before executing again the main process
const unsigned long C_DELAY_TIME_MS = 5000;

const String C_STATION_ID = "st00";

const char* C_WIFI_SSID   = "<SSID>";
const char* C_WIFI_PSWD   = "<Password>";

// Transmit to the receive interface
// Receive from the transmit interface
const String base_url           = "<your base server url>";
const String cmdTrans_handler   = base_url + "station/command/cmdRec.php?st=" + C_STATION_ID;
const String cmdRec_handler     = base_url + "station/command/cmdTrans.php?station=" + C_STATION_ID;
const String telemetry_handler  = base_url + "station/telemtry.php?";
const String store_data_handler = base_url + "/station/store_data.php?";

String cmdTrans = "";

unsigned long cmd_lastTime = 0;
unsigned long data_lastTime = 0;

String telem_input = "";
String data_input = "";

int cmd_id = 1;
int cmd_arg = 0;

int httpResponseCode = 0;

bool read_data_from_arduino = false;

bool is_data_input = true; // transmission begins with measurement data

String input_string = "";

void connectWiFi(const char* ssid, const char* pswd) {

  // the LED indicates that the board is not yet ready
  digitalWrite(LED_BUILTIN, HIGH);

  #ifndef SILENT
    Serial.println("[INFO] Connecting to WiFi");
  #endif

  WiFi.begin(ssid, pswd);

  while (WiFi.status() != WL_CONNECTED) {
    delay(C_RECONNECT_REPEAT_TIME_MS);
    #ifndef SILENT
      Serial.print(".");
    #endif
  }

  #ifndef SILENT
    Serial.println("[INFO] Connected!");
    Serial.print("[INFO] Local IP Address: ");
    Serial.println(WiFi.localIP());
  #endif

  // when connected the LED turns off
  digitalWrite(LED_BUILTIN, LOW);
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

void setup() {
  Serial.begin(115200);

  pinMode(LED_BUILTIN, OUTPUT);
  
  // the LED indicates that the board is not yet ready
  digitalWrite(LED_BUILTIN, HIGH);

  // wait until serial is enabled
  while(!Serial){;}

  // Connect to WiFi
  connectWiFi(C_WIFI_SSID, C_WIFI_PSWD);

  #ifndef SILENT
    Serial.println("[STATUS] Board is set and ready");
  #endif
}

void loop() {

  // operate only when connected
  if (WiFi.status() == WL_CONNECTED) {
    
    HTTPClient http;

    cmd_id = 1;
    cmd_arg = 0;

    // make requests to server for commands every minute
    if ( (millis() - cmd_lastTime) > C_DELAY_TIME_MS) {

      http.begin(cmdRec_handler.c_str());

      httpResponseCode = http.GET();

      bool ok = true;
      unsigned long response_start_time = millis();

      // wait until valid response
      while (http.GET() < 0) {
        if (millis() - response_start_time > 5000) { 
            #ifndef SILENT
              Serial.println("[ERROR] HTTP GET timeout.");
            #endif
            ok = false;
            break;
        }
      }

      // if valid response then proceede
      if (ok) { 
        String payload = http.getString();

        #ifndef SILENT
          Serial.print("[INFO] HTTP Response code: ");
          Serial.println(httpResponseCode);
          Serial.print("[INFO] Payload: ");
          Serial.println(payload);
        #endif

        // Free the connection
        http.end();
        
        // decode the payload into command ID and command argument
        if( parseCmdArg(payload, cmd_id, cmd_arg) ) {

          #ifndef SILENT
            Serial.print("[INFO] Command ID : ");
            Serial.println(cmd_id);
            Serial.print("[INFO] Command Arg : ");
            Serial.println(cmd_arg);
          #endif

          switch(cmd_id) {
            case 0:
              #ifndef SILENT
                Serial.println("[STATUS] Command : Reset Arduino");
              #endif
              
              Serial.println(payload);

              // replace the existing command with $1, 0$ for nominal operation
              cmdTrans = cmdTrans_handler + "&cmd=1&arg=0";
              http.begin(cmdTrans.c_str());

              response_start_time = millis();
              while (http.GET() < 0) {
                if (millis() - response_start_time > 5000) { 
                    #ifndef SILENT
                      Serial.println("[ERROR] HTTP GET timeout.");
                    #endif
                    break;
                }
              }

              http.end();

              break;

            case 1:
              #ifndef SILENT
                Serial.println("[STATUS] NOP");
              #endif
              Serial.println(payload);

              break;

            case 2:
              #ifndef SILENT
                Serial.println("[STATUS] NOP");
              #endif
              Serial.println(payload);

              break;

            case 3:
              #ifndef SILENT
                Serial.println("[STATUS] Command : Set GSM/ WiFi Transmission");
              #endif

              Serial.println(payload);

              // set the global variable 
              if (cmd_arg == 1) {
                read_data_from_arduino = true;
              } else {
                read_data_from_arduino = false;
              }
              
              break;
            
            default:
              // On commands that you cannot find do nothing
              cmd_id = 1;
              cmd_arg = 0;
              break;

          }

        } else {
          
          // it will NEVER get into here. If this occurs then something is wrong with the server
          #ifndef SILENT
            Serial.println("[ERROR] Not valid input string");
          #endif

          cmd_id = 1;
          cmd_arg = 0;
        }
      } else {

        #ifndef SILENT
          Serial.print("[ERROR] Error code: ");
          Serial.println(httpResponseCode);
        #endif
        // nop

      }

      // Update timer
      cmd_lastTime = millis();
    }
    
    // send data to server via WiFi mode
    if (read_data_from_arduino) {
      while (Serial.available() > 0) {
        char incomingChar = (char)Serial.read();
        
        if (incomingChar == '\n') { // line finished
          
          if (is_data_input) {
           
            #ifndef SILENT
              Serial.print("[INFO] Data input : ");
              Serial.println(input_string);
            #endif

            input_string =  store_data_handler + input_string;

          } else {

            #ifndef SILENT
              Serial.print("[INFO] Telemetry input : ");
              Serial.println(input_string);
            #endif

            input_string =  telemetry_handler + input_string;

          }

          http.begin(input_string.c_str());
          
          input_string = "";
          is_data_input = !is_data_input; // next type of data is comming

          // wait until valid response
          unsigned long response_start_time = millis();
          while (http.GET() < 0) {
            if (millis() - response_start_time > 5000) { 
                #ifndef SILENT
                  Serial.println("[ERROR] HTTP GET timeout.");
                #endif
                break;
            }
          }

          http.end();

        } else {
          // reset the input data container 
          input_string += incomingChar;
        }

      }
    }

  } else {

    #ifndef SILENT
      Serial.println("[ERROR] Network is down. Trying to reconnect!");
    #endif

    // reconnect again
    connectWiFi(C_WIFI_SSID, C_WIFI_PSWD);
  }
}
