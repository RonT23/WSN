"""
Creator     : Ronaldo Tsela
Date        : 25/7/2023
Project     : UOA Weather Station Network
Description : Implement a simulator/ emulator for the weather 
              station network with a GUI created in Tkinter in
              order to emulate and study the behavior of the system
"""
import random
import time 
import threading
import tkinter as tk
import requests

# operation modes (min)
FAST        =  3*60         # fast sampling mode
NORMAL      =  1*60         # normal sampling mode
SLOW        =  10*60        # slow sampling mode
POWER_SAVE  =  30*60        # power saving mode

HEARTBEAT_INTERVAL = 5*60   # heartbeat update interval

# fsm states 
RESET = 0           # reset state
ST0   = 1           # idle state
ST1   = 2           # read data from sensors state
ST2   = 3           # transmit data to server state
ST3   = 4           # read telemetry from monitors state
ST4   = 5           # transmit telemetry to server state
SHTD  = 6           # shoutdown state

# software interrupt to threads
stop_event = threading.Event()

class Weather_Station():
    def __init__(self, station_id):
        #### station id
        self.station_id = station_id 
        
        ## Replace this with your root server url
        self.root = "your_server_root_address"
        
        #### backend URL's #######
        self.url_data  = f"http://{self.root}//station//store_data.php?"
        self.url_telem = f"http://{self.root}//station//telemetry_files//"
        self.url_cmdRX = f'http://{self.root}//station//command//cmd_tx.php?&st={station_id}'
        self.url_cmdTX = f'http://{self.root}//station//command//cmd_rx.php?'
        ##########################

        #### initialization 
        self.mode      = NORMAL     # default operation mode
        self.state      = RESET     # initial state
        self.run = 1

        #### weather recording variables
        self.temp      = 0.0
        self.hum       = 0.0
        self.pres      = 0.0
        self.windSpeed = 0.0
        self.windDir   = 0.0
        self.rain      = 0.0

        #### internal state variables
        self.intTemp   = 0.0
        self.busCur    = 0.0
        self.busVolt   = 0.0
        self.solVolt   = 0.0
        self.heartBeat = 0

        ### command related variables
        self.cmd_id    = 0
        self.cmd_arg   = 0
        self.cmd_station_id = self.station_id

        # initialize timers
        self.t0 = time.time()
        self.t1 = time.time()
        self.t2 = time.time()

        ######### FSM logic ###############
        while self.run :
            ## if interrupt activated stop simulator ##
            if stop_event.is_set():
                self.run=0
                print(f'Station {station_id} stopped')
            ###########################################

            ## state logic  ##########################
            if(self.state==RESET):   # reset state
                self.mode  = NORMAL  # default mode
                self.state = ST0     # next state

                # debuging message
                print(f'Station {self.station_id} initiated\nmode default')

                # initialize variables
                self.temp      = 0.0
                self.hum       = 0.0
                self.pres      = 0.0
                self.windSpeed = 0.0
                self.windDir   = 0.0
                self.rain      = 0.0
 
                self.intTemp   = 0.0
                self.busCur    = 0.0
                self.busVolt   = 0.0
                self.solVolt   = 0.0
                self.heartBeat = 0

                self.cmd_id    = 0
                self.cmd_arg   = 0
                self.cmd_station_id = self.station_id

                # initialize timers
                self.t0 = time.time()
                self.t1 = time.time()
                self.t2 = time.time()

            elif( (self.state == ST0) or (self.state == SHTD)): # idle state 
                # change state when sampling timer ticks and not in shutdown mode
                if( (time.time() - self.t0>=self.mode) and (self.state != SHTD)):
                    self.state  = ST1

                # remain idle if shutdown mode 
                elif(self.state == SHTD):
                    self.state  = SHTD

                # remain idle in any other situation
                else:
                    self.state  = ST0

                # count heartbeat
                if(time.time() - self.t1 >= HEARTBEAT_INTERVAL):
                    print(f'station {station_id}')
                    print(f'state:{self.state}\nmode: {round(self.mode/60)}\nheartbeat: {self.heartBeat}')

                    self.t1 = time.time()
                    self.heartBeat = self.heartBeat + 1

                    # check command
                    if(self.state != SHTD or (self.state == SHTD and time.time()-self.t2 >= 30*60)):
                        self.state, self.mode = self.read_command()

            elif(self.state  == ST1): # read sensors
                self.state = ST2 # next state
                
                # debugging message
                print(f'state:{self.state}\nmode: {round(self.mode/60)}\nheartbeat: {self.heartBeat}')

                self.temp      = self.read_temperature()
                self.hum       = self.read_humidity()
                self.pres      = self.read_pressure()
                self.windSpeed = self.read_windSpeed()
                self.windDir   = self.read_windDir()
                self.rain      = self.read_rainRate()  

            elif(self.state == ST2): # transmit sensor data
                self.state = ST3 # next state

                # debugging message
                print(f'state:{self.state}\nmode: {round(self.mode/60)}\nheartbeat: {self.heartBeat}')

                dataPacket = list([self.temp, self.hum, self.pres, self.windSpeed, self.windDir, self.rain])
                response   = self.transmit_sensorData(dataPacket)

                print(f'Data handler response : {response}')

            elif(self.state == ST3):# read monitors state     
                self.state = ST4 # next state 

                # debugging message
                print(f'state:{self.state}\nmode: {round(self.mode/60)}\nheartbeat: {self.heartBeat}')

                self.intTemp = self.read_internalTemp()
                self.busVolt = self.read_busVoltage()
                self.busCur  = self.read_busCurrent()
                self.solVolt = self.read_solarVoltage()

            elif(self.state == ST4):# transmit telemetry state
                self.state = ST0 # next state

                # debugging message
                print(f'state:{self.state}\nmode: {round(self.mode/60)}\nheartbeat: {self.heartBeat}')

                dataPacket = list([self.intTemp, self.busVolt, self.busCur, self.solVolt, self.heartBeat, self.mode])
                response = self.transmit_telemetry(dataPacket)

                print(f'Telemetry handler response : {response}')

                # update sampling timer
                self.t0 = time.time()

    ###### Sensor data ############################
    def read_temperature(self):
        return random.random()*10
    
    def read_humidity(self):
        return random.random()*10
    
    def read_pressure(self):
        return random.random()*10

    def read_windSpeed(self):
        return random.random()*10
    
    def read_windDir(self):
        return random.random()*10
    
    def read_rainRate(self):
        return random.random()*10
    ###############################################

    ###### Internal monitors #######################
    def read_internalTemp(self):
        return random.random()*10
    
    def read_busVoltage(self):
        return random.random()*10
    
    def read_busCurrent(self):
        return random.random()*10
    
    def read_solarVoltage(self):
        return random.random()*10
    ################################################

    ###### Network functions #######################
    def transmit_sensorData(self, dataPacket):
        temp        = dataPacket[0]
        hum         = dataPacket[1]
        pres        = dataPacket[2]
        windSpeed   = dataPacket[3]
        windDir     = dataPacket[4]
        rainfall    = dataPacket[5] 
    
        data = f'&st={self.station_id}&t={temp}&h={hum}&p={pres}&v={windSpeed}&d={windDir}&r={rainfall}'

        rq = requests.post(self.url_data+data)
        
        return rq.text

    def transmit_telemetry(self, dataPacket):
        temp      = dataPacket[0]
        busVolt   = dataPacket[1]
        busCur    = dataPacket[2]
        solVolt   = dataPacket[3]
        heartBeat = dataPacket[4]
        opMode    = dataPacket[5] 
    
        data = f'&st={self.station_id}&t={temp}&v={busVolt}&i={busCur}&sv={solVolt}&hb={heartBeat}&m={opMode}'

        rq = requests.post(self.url_telem+data)
        
        return rq.text

    def read_command(self):
        mode  = self.mode  # current mode
        state = self.state # current state 
        
        response = requests.post(self.url_cmdRX).text
        if(len(response)!= 0):
            if(response[0]=='$'): # if command is valid

                cmd_str  = response[1:len(response)-2]
                cmd_list = cmd_str.strip().split(',')
                
                cmd_id         = cmd_list[0]
                cmd_arg        = cmd_list[1]
                
                if( (cmd_id != "") and (cmd_arg != "")):
                    if(cmd_id == 0 and cmd_arg == 0):
                        state = RESET
                    elif(cmd_id == 1 and cmd_arg == 0):
                        mode = NORMAL
                    elif(cmd_id == 1 and cmd_arg == 1):
                        mode = FAST
                    elif(cmd_id == 1 and cmd_arg == 2):
                        mode = SLOW
                    elif(cmd_id == 1 and cmd_arg == 3):
                        mode = POWER_SAVE
                    elif(cmd_id == 2 and cmd_arg == 0):
                        state = SHTD
                    elif(cmd_id == 2 and cmd_arg == 1):
                        state = ST0

                data = f'&id={self.station_id}&cmd=&arg='
                response = requests.post(self.url_cmdTX+data).text

        return state, mode
    ################################################

class GUI():
    def __init__(self, width, height, title):
        self.ws    = [] # weather station list
        self.ws_th = [] # weather station threads list

        self.station_number = 0

        ### window characteristics
        self.width  = width     
        self.height = height
        self.title  = title 

        ### start main thread
        self.th_main = threading.Thread(target=self.create_main_window)
        self.th_main.start()
        self.th_main.join()

    def create_main_window(self):
        self.root = tk.Tk(className=self.title)  

        self.root.geometry(f"{self.width}x{self.height}")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        #### frames ######################################
        self.frame_1 = tk.Frame(self.root, bg="white")
        self.frame_1.grid(row=0, column=0, columnspan=2)

        self.frame_2 = tk.Frame(self.root, bg="white")
        self.frame_2.grid(row=1, column=0, columnspan=2)

        self.frame_3 = tk.Frame(self.root, bg="white")
        self.frame_3.grid(row=2, column=0, columnspan=2)
        ####################################################

        #### entry: enter the station number ###############
        self.label_1 = tk.Label(self.frame_1, text="Station Number : ", bg="white", font="Aerial 15")
        self.label_1.grid(padx=5, pady=10, row=0, column=0)

        self.entry_1 = tk.Entry(self.frame_1, font="Aerial 15")
        self.entry_1.grid(pady=10, padx=10, row=0, column=1)
        #####################################################

        #### buttons: start/ stop simulation ################
        self.button_start = tk.Button(self.frame_2, text="Start Simulation", font="Arial 12")
        self.button_start.grid(row=0, column=0, padx=10, pady=5)
        self.button_start.bind("<Button-1>", self.start_simulation)
        
        self.button_stop = tk.Button(self.frame_2, text="Stop Simulation", font="Arial 12")
        self.button_stop.grid(row=0, column=1, padx=10, pady=5)
        self.button_stop.bind("<Button-1>", self.stop_simulation)
        #####################################################

        #### state indicator label ##########################
        self.label_2 = tk.Label(self.frame_3, text=" ", bg="white", font="Arial 12")
        self.label_2.grid(row=0, column=0, columnspan=2)
        #####################################################

        self.root.mainloop()

    def start_simulation(self, event):
        # update the state label
        self.label_2.config(text="Simulation Started")

        # get the station number 
        self.station_number = int(self.entry_1.get())

        # create the weather stations
        for i in range(self.station_number):
            if(i<10):
                id = f'st0{i}'
            else:
                id = f'st{i}'
            
            # each station is a thread
            self.ws_th.append(threading.Thread(target=self.create_weather_station, args=(id,)))
            self.ws_th[i].start()
    
    def create_weather_station(self, id):
        self.ws.append(Weather_Station(id))

    def stop_simulation(self, event):
        # update the state label
        self.label_2.config(text="Simulation Terminated")

        # activate stop interrupt   
        stop_event.set() 
        
        # kill all threads
        for i in range(self.station_number):
            self.ws_th[i].join()

        # reset the containers
        self.ws.clear()
        self.ws_th.clear()

if __name__ == "__main__":
    title = "Weather Station Network Simulator"
    width = 400
    height = 150

    gui = GUI(width, height, title)
