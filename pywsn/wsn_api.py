'''
    Creator : Ronaldo Tsela
    Date    : 31/7/2023
    Project : Weather Station Network
    Description : This package was intended to provide the intermediate interface to the low
                  level API for the user intended to build applications
'''
import requests
import pandas as pd
import numpy as np

class Weather_Station_Backend_Controller:
    def __init__(self, server_root):
        '''
            set the route URLs used to access the different backend handlers
        '''
        self.root = server_root
        self.url_telemFile= f"http://{self.root}//station//telemetry_files//" # route URL for the telemetry files
        self.url_stats    = f"http://{self.root}//api//data//stats.php?" # route URL for the statistics generator handler
        self.url_daily    = f"http://{self.root}//api//data//daily.php?" # route URL for the daily data generator handler
        self.url_dataset  = f"http://{self.root}//api//data//dataset.php?" # route URL for the dataset generator handler
        self.url_cmdTX    = f"http://{self.root}//station//command/cmd_rx.php?" # route URL for the command transmiter handler

    def get_data(self, station_id):
        '''
            This function reads the daily data collected by a specific station. 
            The return value is a pandas dataframe with the aforementioned data recordings.
            The features are:
            Date (UTM-Date YYYY-MM-DD), 
            Time(UTM-time HH:mm:ss),
            Temperature (float64), 
            Humidity (float64), P
            ressure (float64)
            Wind_Speed (float64), 
            Wind_Direction (float64), 
            Rainfall (float64)

            @station_id : the unique station identifier of the form stxx
        '''
        response = requests.post(self.url_daily+f'&st={station_id}')
        data_str_list = (response.text).split('\n')

        data_df = pd.DataFrame()
        output_list=[]
        for i in range(len(data_str_list)-1):
            data_list = (data_str_list[i].strip()).split(',')
            output_list.append(data_list)

        columns=['Station_ID', 'Date', 'Time', 'Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Wind_Direction', 'Rainfall']

        data_df = pd.DataFrame(output_list,columns=columns)

        del data_df['Station_ID']

        return data_df


    def get_stats(self, station_id):
        '''
            This function reads the statistics on daily basis. 
            The return values are three pandas dataframe and one float64 single value. 
            The three pandas dataframe contain the minimum, the maximum and the average of the daily weather values recorded. 
            The float64 refers to the ccumulated rainfall.
            Each pandas dataframe contain values that refere to the features:
            Temperature (float64), Humidity (float64), Pressure (float64),
            Wind_Speed (float64), Rainfall (float64)
            
            @station_id : the unique station identifier 
        '''
        response = requests.post(self.url_stats+f'&st={station_id}')

        stat_data_str_list = response.text.split('\n')

        min = stat_data_str_list[0].strip().split(',')
        max = stat_data_str_list[1].strip().split(',')
        avg = stat_data_str_list[2].strip().split(',')
        total_rain_rate = stat_data_str_list[3].strip()

        min_df = pd.DataFrame(min).transpose()
        min_df.columns=['Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Rainfall']

        max_df = pd.DataFrame(max).transpose()
        max_df.columns=['Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Rainfall']

        avg_df = pd.DataFrame(avg).transpose()
        avg_df.columns=['Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Rainfall']

        return min_df, max_df, avg_df, total_rain_rate


    def get_telemetry(self, station_id):
        '''
            This function reads the telemetry for every station. 
            The return value is a pandas dataframe containing the telemetry data. 
            The features are:
            Date (UTM-Date YYYY-MM-DD), 
            Time (UTM-Time HH:mm:ss), 
            Internal Temperature (float64), 
            Bus Voltage (float64)
            Bus Current (float64), 
            Solar_Voltage (float64), 
            Heartbeat (unsigned int), 
            Mode (unsigned int)
        '''
        response = requests.post(self.url_telemFile+f'telemetry_{station_id}')

        telem_data_df = (response.text.strip()).split(',')

        telem_data_df = pd.DataFrame(telem_data_df).transpose()
        telem_data_df.columns= ['Date', 'Time', 'Temperature', 'Bus_Voltage', 'Bus_Current', 'Solar_Voltage', 'Heartbeat', 'Mode']
        telem_data_df['Temperature'] = round(float(telem_data_df['Temperature'][0]), 2)
        telem_data_df['Bus_Voltage'] = round(float(telem_data_df['Bus_Voltage'][0]), 2)
        telem_data_df['Bus_Current'] = round(float(telem_data_df['Bus_Current'][0]), 2)
        telem_data_df['Solar_Voltage'] = round(float(telem_data_df['Solar_Voltage'][0]), 2)
        
        return telem_data_df


    def get_dataset(self, station_id, from_day, from_month, from_year, to_day, to_month, to_year):
        '''
            The function creates a dataset of choise between two given dates.
            The return value is the number of recordings that fit to the given
            dates and a pandas data frame with the exact recordings. 
            The features contained are:
            Date (UTM-Date YYYY-MM-DD), 
            Time(UTM-time HH:mm:ss),
            Temperature (float64), 
            Humidity (float64), 
            Pressure (float64)
            Wind_Speed (float64), 
            Wind_Direction (float64), 
            Rainfall (float64)

            @station_id : the unique station identifier
            @from_day   : the starting day
            @from_month : the starting month
            @from_year  : the starting year
            @to_day     : the ending day
            @to_month   : the ending month
            @to_year    : the ending year
        '''
        data = f'&st={station_id}&from_day={from_day}&from_month={from_month}&from_year={from_year}&to_day={to_day}&to_month={to_month}&to_year={to_year}'
        data_str_list = ((requests.post(self.url_dataset+data)).text).split('\n')

        cnt = len(data_str_list)

        data_df = pd.DataFrame()
        data_list_appended = []

        if(cnt-1==0):
            return cnt-1, -1
        else:
            for i in range(cnt-1):
                data_list = (data_str_list[i].strip()).split(',')
                data_list_appended.append(data_list)

            col = ['Station_ID', 'Date', 'Time', 'Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Wind_Direction', 'Rainfall']
            data_df = pd.DataFrame(data_list_appended, columns=col)

            del data_df['Station_ID']

            return cnt-1, data_df

    def set_command(self, station_id, command_id, argument):
        '''
            This function sets a command for the target station to execute. Commands are
            executed asynchronously
            
            command_id |  argument  |  action
            ----------------------------------
                0      |     0      | reset
                1      |     0      | normal
                1      |     1      | fast
                1      |     2      | slow
                1      |     3      | power save
                2      |     0      | shut down
                2      |     1      | init

            When the transmission is valid an OK (200) signal will be returned
            
            @station_id : the unique station identifier
            @command_id : the commands identifier to trigger 
            @argument   : the argument passed to the command trigger
        '''
        response = requests.post(self.url_cmdTX+f'&id={station_id}&cmd={command_id}&arg={argument}')
        return response.text
