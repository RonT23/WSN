from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import login
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import logout

from .models import Stations
from .forms import GetIdForm, RegistrationForm, ContactForm, Get_Data_admin_Form, StationForm, CustomUserCreationForm, EditStationForm
import folium

from .wsn_api import Weather_Station_Backend_Controller as wsn_controller

import keras

import csv
import os

import pandas as pd
import numpy as np

from datetime import datetime, timedelta,time

ROOT  = 'your root server dir'   # add your root server directory
EMAIL = 'your application email' # add your application email
 
def load_model(model_file):
    model = keras.models.load_model(model_file, compile=True)
    return model

def create_sequence(dataset, timesteps):
    X = dataset[0:timesteps, :]
    return np.array(X)

def custom_logout(request):
    logout(request)
    return redirect('login')

@login_required #SETING WHO CAN ACCESS (ONLY USERS AND ADMINS)

def main_page(request):
    user = request.user
    key  = ['Temperature', 'Humidity', 'Pressure', 'Wind_Speed', 'Rainfall']

    timesteps = 24
    context_add={}

    wsc  = wsn_controller(ROOT)

    # create the background - empty map
    my_map = folium.Map(location=[38, 25], zoom_start=9)

    # Load the TensorFlow model with the specified options
    lstm_model_30min = load_model(os.getcwd() + '/wsn_app/predictors/lstm-30min.keras')
    lstm_model_1hr   = load_model(os.getcwd() + '/wsn_app/predictors/lstm-1hr.keras')
    lstm_model_2hr   = load_model(os.getcwd() + '/wsn_app/predictors/lstm-2hr.keras')

    dynamic_choices = [ tuple([x.id,x.id]) for x in Stations.objects.all() if x.state=='Active']

    if request.method == 'POST': # read the clients content action
    
        action = request.POST.get('action') # action listener, get data from post and recognize the button pressed

        if  action=='Contact':
        
            form=ContactForm(request.POST)
            
            if form.is_valid():
            
                cleaned_data = form.cleaned_data
                message = (
                    f"Message From Authorized User:\n\n"
                    f"User: {request.user}\n"
                    f"Email: {request.user.email}\n"
                    f"Topic: {cleaned_data['theme']}"
                    f"Note: {cleaned_data['note']}"
                )
                
                send_mail(
                    'Message From Authorized User',
                    message,
                    EMAIL,
                    [EMAIL], # list of emails that we want to take the emails
                    fail_silently=False,
                )
                messages.success(request,'Note submitted successfully, we will get to you shortly')
                
            return redirect('main_page')

        # the input follows the pre-defined restriction set
        form_id = GetIdForm(request.POST)   # entry for st_id, button select and button download dataset

        if form_id.is_valid():
        
            selected_id_value = form_id.cleaned_data['selected_id'] # get the station id from input entry

            # get statistic metrics for daily measurements using the API
            min_df, max_df, avg_df, total_rain_rate = wsc.get_stats(selected_id_value)

            if action == 'select': # the select button is pressed

                # collect statistics for the selected station
                if(total_rain_rate != ''):

                    # get daily data / real time recordings
                    dataset= wsc.get_data(selected_id_value)

                    # minimum
                    min_temp  = round(float(min_df[key[0]][0]), 3)
                    min_hum   = round(float(min_df[key[1]][0]), 3)
                    min_pres  = round(float(min_df[key[2]][0]), 3)
                    min_winSp = round(float(min_df[key[3]][0]), 3)
                    min_rain  = round(float(min_df[key[4]][0]), 3)

                    # maximum
                    max_temp  = round(float(max_df[key[0]][0]), 3)
                    max_hum   = round(float(max_df[key[1]][0]), 3)
                    max_pres  = round(float(max_df[key[2]][0]), 3)
                    max_winSp = round(float(max_df[key[3]][0]), 3)
                    max_rain  = round(float(max_df[key[4]][0]), 3)

                    # average
                    avg_temp  = round(float(avg_df[key[0]][0]), 3)
                    avg_hum   = round(float(avg_df[key[1]][0]), 3)
                    avg_pres  = round(float(avg_df[key[2]][0]), 3)
                    avg_winSp = round(float(avg_df[key[3]][0]), 3)
                    avg_rain  = round(float(avg_df[key[4]][0]), 3)

                    # total rain = [mm/sec] * 5 [min] * 60 [sec] * x [samples] = 300 [mm] * x [samples]
                    total_rain = float(total_rain_rate)
                    avg_rain_intencity = total_rain / 3600.0
                    
                    # create daily data collection
                    if(len(dataset) > 0):
                        # Date and Time is in UTM : hr:min:sec YYYY-MM-DD
                        time_values  = pd.to_datetime( np.array(dataset['Time']), format='%H:%M:%S' ) # create time instance object
                        time_strings = [time.strftime('%H:%M:%S') for time in time_values]            # convert the aforementioned to string

                        date_values  = pd.to_datetime(np.array(dataset['Date']), format='%Y-%m-%d')   # create time instance object
                        date_strings = [date.strftime('%Y-%m-%d') for date in date_values]            # convert the aforementioned to string

                        # Combine date and time into a single list
                        datetime_strings = [f'{date} {time}' for date, time in zip(date_strings, time_strings)]

                        # create measurement collections
                        temp  = (np.array( dataset['Temperature'].astype("float64")    )).tolist()
                        hum   = (np.array( dataset['Humidity'].astype("float64")       )).tolist()
                        pres  = (np.array( dataset['Pressure'].astype("float64")       )).tolist()
                        winSp = (np.array( dataset['Wind_Speed'].astype("float64")     )).tolist()
                        winDi = (np.array( dataset['Wind_Direction'].astype("float64") )).tolist()
                        rain  = (np.array( dataset['Rainfall'].astype("float64")       )).tolist()

                        context_add_prediction = {}
                        
                        # prepare the data for prediction -> use min/max scaler 
                        temp_scale =  [ ( p - min_temp ) / (max_temp - min_temp) for p in temp ]
                        hum_scale  =  [ ( p - min_hum) / (max_hum - min_hum) for p in hum]
                        pres_scale =  [ ( p - min_pres) / (max_pres - min_pres) for p in pres]
                        speed_scale = [ ( p - min_winSp) / (max_winSp - min_winSp) for p in winSp]

                        X_df = pd.DataFrame(temp_scale, columns=['temperature',])
                        X_df['humidity'] = hum_scale
                        X_df['pressure'] = pres_scale
                        X_df['speed']    = speed_scale

                        temp_pred = []
                        temp_pred.append(temp[-1])

                        hum_pred  = []
                        hum_pred.append(hum[-1])

                        pres_pred = []
                        pres_pred.append(pres[-1]);

                        wind_pred = []
                        wind_pred.append(winSp[-1]);

                        last_time = time_values[-1]
                        time_pred = []
                        time_pred.append(last_time)

                        prediction_ready = False

                        # make predictions
                        if len(dataset) > timesteps:
                            X = create_sequence(X_df.values, timesteps)
                            X = np.reshape(X, (1, 4, timesteps))

                            y0 = lstm_model_30min.predict(X)

                            T30  = y0[0][0]  * (max_temp - min_temp) + min_temp
                            RH30 = y0[0][1] * (max_hum - min_hum) + min_hum
                            P30  = y0[0][2] * (max_pres - min_pres) + min_pres
                            WS30 = y0[0][3] * (max_winSp - min_winSp) + min_winSp

                            y1 = lstm_model_1hr.predict(X)

                            T1  = y1[0][0] * (max_temp - min_temp) + min_temp
                            RH1 = y1[0][1] * (max_hum - min_hum) + min_hum
                            P1  = y1[0][2] * (max_pres - min_pres) + min_pres
                            WS1 = y1[0][3] * (max_winSp - min_winSp) + min_winSp


                            y2 = lstm_model_2hr.predict(X)

                            T2  = y2[0][0] * (max_temp - min_temp) + min_temp
                            RH2 = y2[0][1] * (max_hum - min_hum) + min_hum
                            P2  = y2[0][2] * (max_pres - min_pres) + min_pres
                            WS2 = y2[0][3] * (max_winSp - min_winSp) + min_winSp

                            if last_time.time() < time(22, 00) :
                                temp_pred.append(T30)
                                hum_pred.append(RH30)
                                pres_pred.append(P30)
                                wind_pred.append(WS30)
                                time_pred.append(last_time + timedelta(minutes=30))

                                temp_pred.append(T1)
                                hum_pred.append(RH1)
                                pres_pred.append(P1)
                                wind_pred.append(WS1)
                                time_pred.append(last_time + timedelta(minutes=60))

                                temp_pred.append(T2)
                                hum_pred.append(RH2)
                                pres_pred.append(P2)
                                wind_pred.append(WS2)
                                time_pred.append(last_time + timedelta(minutes=120))

                            #if timestamp > 22:00:00 and < 23:30:00 then only half hour and one hour predictions
                            elif last_time.time() >= time(22, 00) and  last_time.time() < time(23, 00):

                                temp_pred.append(T30)
                                hum_pred.append(RH30)
                                pres_pred.append(P30)
                                wind_pred.append(WS30)
                                time_pred.append(last_time + timedelta(minutes=30))

                                temp_pred.append(T1)
                                hum_pred.append(RH1)
                                pres_pred.append(P1)
                                wind_pred.append(WS1)
                                time_pred.append(last_time + timedelta(minutes=60))

                            elif last_time.time() >= time(23, 00)and  last_time.time() < time(23, 30)  :
                                temp_pred.append(T30)
                                hum_pred.append(RH30)
                                pres_pred.append(P30)
                                wind_pred.append(WS30)
                                time_pred.append(last_time + timedelta(minutes=30))

                            #if timestamp > 23:00:00 and < 23:30:00 then only half hour prediction
                            prediction_ready = True
                            
                        else:
                            prediction_ready = False

                        # plot predictions
                        if prediction_ready:
                            time_pred_strings = [time.strftime('%H:%M:%S') for time in time_pred]
                            time_pred = [f'{date} {time}' for date, time in zip(date_strings[-len(time_pred_strings):], time_pred_strings)]

                            context_add_prediction={
                                'time_pre' : time_pred,
                                'temp_pre' : temp_pred,
                                'hum_pre'  : hum_pred,
                                'press_pre': pres_pred,
                                'speed_pre': wind_pred
                            }

                        # when the respective station is selected make the pin green
                        green_icon = folium.Icon(color='green')

                        for station in Stations.objects.all():
                            if station.state =='Active':
                                # default popup
                                popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">Latitude: {station.lat}<br>Longitude: {station.lon}</p></div>'

                                if station.id == selected_id_value:
                                    # selected popup
                                    popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">Latitude: {station.lat}<br>Longitude: {station.lon} </p><p style="text-align:center;">{datetime_strings[-1]} </p><table class="table-popup"><tbody><tr><th class="th-popup">Temperature</th><th class="th-popup">{temp[-1]}  °C</th></tr><tr><th class="th-popup">Humidity </th><th class="th-popup"> {hum[-1]}  %</th></tr><tr><th class="th-popup">Pressure </th><th class="th-popup"> {pres[-1]}  hPa</th></tr><tr><th class="th-popup">Wind Speed </th><th class="th-popup">{winSp[-1]}  km/hr</th></tr><tr><th class="th-popup">Wind Direction </th><th class="th-popup">{winDi[-1]}  deg</th></tr><tr><th class="th-popup">Rainfall </th><th class="th-popup"> {rain[-1]}  mm</th></tr></tbody></table> </div>'
                                    # add the marker with the popup in the map
                                    folium.Marker(location=[station.lat, station.lon], popup=popup, icon=green_icon).add_to(my_map)
                                else:
                                    # keep default
                                    folium.Marker(location=[station.lat,station.lon], popup=popup).add_to(my_map)
                            else:
                                # station selected but not active popup
                                popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">Latitude: {station.lat}<br>Longitude: {station.lon}</p></div>'
                                folium.Marker(location=[station.lat,station.lon], popup=popup, icon=folium.Icon(color='gray')).add_to(my_map)

                        # make the folium object (map) into html template
                        map_html = my_map._repr_html_()

                        # statistics table into the context
                        context_add={
                        'min_temp'   : round(min_temp,   2),
                        'min_hum'    : round(min_hum,    2),
                        'min_pr'     : round(min_pres,   2),
                        'min_ws'     : round(min_winSp,  2),
                        'min_rf'     : round(min_rain,   2),
                        'max_temp'   : round(max_temp,   2),
                        'max_hum'    : round(max_hum,    2),
                        'max_pr'     : round(max_pres,   2),
                        'max_ws'     : round(max_winSp,  2),
                        'max_rf'     : round(max_rain,   2),
                        'avg_temp'   : round(avg_temp,   2),
                        'avg_hum'    : round(avg_hum,    2),
                        'avg_pr'     : round(avg_pres,   2),
                        'avg_ws'     : round(avg_winSp,  2),
                        'avg_rf'     : round(avg_rain,   2),
                        'trr'        : round(total_rain, 2),
                        'ri'         : round(avg_rain_intencity, 2),

                        # figures of plots into the context
                        'time'       : datetime_strings,
                        'temp'       : temp,
                        'hum'        : hum,
                        'pres'       : pres,
                        'windSpeed'  : winSp,
                        'windDir'    : winDi,
                        'rain'       : rain
                        }

                        context_add.update(context_add_prediction)

                else:
                    # return back to home
                    messages.error(request,'No data available today for this station')

                    return redirect('main_page')

            if action == 'download':
                    today = datetime.today()
                    formatted_date = today.strftime('%d-%m-%Y')

                    day = today.day

                    month = today.month
                    year = today.year
                    
                    # download the daily dataset 
                    cnt, dataset = wsc.get_dataset(selected_id_value, day, month, year, day, month, year)

                    if(int(cnt)>0): # if data exists
                        custom_dataset = dataset
                        DOWNLOADED     = f"{user}_{selected_id_value}_{formatted_date}.csv"
                        custom_dataset.to_csv(DOWNLOADED,index=False)

                        # http response for downloading dataset
                        response = HttpResponse(
                            content_type = "text/csv",
                            headers      = {"Content-Disposition": f'attachment; filename= {DOWNLOADED}'},
                        )

                        writer = csv.writer(response)
                        for col in range(cnt):
                            # create the downloadable dataset
                            writer.writerow([custom_dataset['Date'][col],
                                             custom_dataset['Time'][col],
                                             custom_dataset['Temperature'][col],
                                             custom_dataset['Humidity'][col],
                                             custom_dataset['Pressure'][col],
                                             custom_dataset['Wind_Speed'][col],
                                             custom_dataset['Wind_Direction'][col],
                                             custom_dataset['Rainfall'][col]])
                        os.remove(DOWNLOADED)

                        return response

                    else:
                        messages.error(request,'No data available today for this station')
                        return redirect('main_page')

    if request.method == 'GET':
        for station in Stations.objects.all():
            if station.state =='Active':
                popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">Latitude: {station.lat}<br>Longitude: {station.lon}</p></div>'

                folium.Marker(location=[station.lat,station.lon], popup=popup, icon=folium.Icon(color='blue')).add_to(my_map)
            else:
                popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">LAT: {station.lat}<br>LON: {station.lon}</p></div>'
                folium.Marker(location=[station.lat,station.lon], popup=popup, icon=folium.Icon(color='gray')).add_to(my_map)

    map_html = my_map._repr_html_()


    form_id = GetIdForm()
    context = {'map_html': map_html,'USER':user,'form':form_id}


    if context_add:
        context.update(context_add)


    return render(request, 'main_page_2.html', context)


def register(request):
    if request.method == 'POST':
        
        form = RegistrationForm(request.POST)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            message = (
                f"New registration:\n\n"
                f"Name: {cleaned_data['fist_name']} {cleaned_data['last_name']}\n"
                f"Email: {cleaned_data['email']}\n"
                f"User Type: {cleaned_data['user_type']}\n"
                f"Organization/University Name: {cleaned_data['organization_name']}\n"
                f"Note: {cleaned_data['note']}"
            )
            
            # Your email sending logic here for sending an email to yourself
            send_mail(
                'New Registration',
                message,
                EMAIL,
                [EMAIL],
                fail_silently=False,
            )
            
            # Send email to user who made the registration request 
            send_mail(
                'Registration in WSN',
                f"Thank you  {cleaned_data['fist_name']} {cleaned_data['last_name']} for your registration. We will review your submission and get in touch with you.",
                EMAIL,#from email 
                [cleaned_data['email']],#to email 
                fail_silently=False,
            )

            # Redirect or perform further actions
            return redirect('login')   

    else:
        form = RegistrationForm()

    return render(request, 'registration/registration_page.html', {'reg_form': form})

def contact_form(request):

    form=ContactForm()
    
    if request.method == 'POST':
    
        form = ContactForm(request.POST)
        
        if form.is_valid():
        
            cleaned_data = form.cleaned_data
            
            message = (
                f"Message From Authorized User:\n\n"
                f"User: {request.user}\n"
                f"Email: {request.user.email}\n"
                f"Note: {cleaned_data['note']}"
            )
            
            send_mail(
                'Message From Authorized User',
                message,
                EMAIL,
                [EMAIL], 
                fail_silently=False,
            )
            messages.success(request,'Note submitted successfully, we will get to you shortly')
        return redirect('main_page')

    return render(request, 'contact_form.html',{'contact_form':form})

def about_us(request):
    return render(request, 'About.html')

################################################################################ ADMIN ################################################################
@staff_member_required
def custom_admin_view(request):
    my_map = folium.Map(location=[38, 25], zoom_start=9)
    
    wsc  = wsn_controller(ROOT)
    
    form = Get_Data_admin_Form()
    
    for station in Stations.objects.all():
    
        if station.state =='Active':
        
            try:
                Telemetry = wsc.get_telemetry(station.id)
                Temperature=round(((Telemetry['Temperature'][0]-32)*(5/9)), 2)
                Bus_Voltage=Telemetry['Bus_Voltage'][0]
                Bus_Current=Telemetry['Bus_Current'][0]
                Solar_Voltage=Telemetry['Solar_Voltage'][0]
                Heartbeat=Telemetry['Heartbeat'][0]
                Mode=Telemetry['Mode'][0]
                date=Telemetry['Date'][0]
                time=Telemetry['Time'][0]

                # Combine date and time into a single list
                datetime_string = f'{date} {time}'

                popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;">Latitude: {station.lat}<br>Longitude: {station.lon}</p><p style="text-align:center;"> {datetime_string}</p><table class="table-popup"><tbody><tr><th class="th-popup">Temperature</th><th class="th-popup">{Temperature}  °C</th></tr><tr><th class="th-popup">Bus Voltage </th><th class="th-popup"> {Bus_Voltage}  V</th></tr><tr><th class="th-popup">Bus Current </th><th class="th-popup"> {Bus_Current}  A</th></tr><tr><th class="th-popup">Solar Voltage </th><th class="th-popup">{Solar_Voltage}  V</th></tr><tr><th class="th-popup">Heartbeat</th><th class="th-popup">{Heartbeat}</th></tr><tr><th class="th-popup">Mode</th><th class="th-popup"> {Mode} </th></tr></tbody></table></div>'
                folium.Marker(location=[station.lat, station.lon], popup=popup).add_to(my_map)

            except:
               pass
        else:
            popup=f'<div class="leaflet-popup-content" style="width: 176px;"><p style="text-align: center;">{station.id} - {station.state}</p><p style="text-align: center;"> Latitude: {station.lat}<br>Longitude: {station.lon}</p></div>'

            folium.Marker(location=[station.lat, station.lon], popup=popup).add_to(my_map)

    if request.method=='POST':
        
        form=Get_Data_admin_Form(request.POST)
        
        if form.is_valid():
        
            # Process the form data
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']
            selected_id =form.cleaned_data['selected_id']
            from_day = from_date.day
            from_month = from_date.month
            from_year = from_date.year

            to_day = to_date.day
            to_month = to_date.month
            to_year = to_date.year
            cnt, dataset = wsc.get_dataset(selected_id, from_day, from_month, from_year, to_day, to_month, to_year)

            if(int(cnt)>0): # if data exists
                custom_dataset = dataset
                DOWNLOADED     = f"{selected_id}_{from_date}_{to_date}_.csv"

                custom_dataset.to_csv(DOWNLOADED,index=False)



                # http response for downloading dataset
                response = HttpResponse(
                    content_type = "text/csv",
                    headers      = {"Content-Disposition": f'attachment; filename= {DOWNLOADED}'},
                )

                writer = csv.writer(response)
                for col in range(cnt):
                    # create the downloadable dataset
                    writer.writerow([custom_dataset['Date'][col],
                                        custom_dataset['Time'][col],
                                        custom_dataset['Temperature'][col],
                                        custom_dataset['Humidity'][col],
                                        custom_dataset['Pressure'][col],
                                        custom_dataset['Wind_Speed'][col],
                                        custom_dataset['Wind_Direction'][col],
                                        custom_dataset['Rainfall'][col]])
                os.remove(DOWNLOADED)
                messages.success(request,f'Successfully download dataset for {selected_id}')

                return response

            else:
                messages.error(request,'No data available today for this station')
                return redirect('admin_data_access')

    map_html = my_map._repr_html_()
    context = {'map': map_html,'form':form}
    return render(request, 'Admin/custom_admin_view.html', context)

############################# Stations #####################################

@staff_member_required
def Stations_admin(request):
    stations = Stations.objects.all()
    return render(request, 'Admin/Stations.html', {'stations': stations})

@staff_member_required
def delete_station_confirmation(request, station_id):
    station = get_object_or_404(Stations, id=station_id)
    if request.method == 'POST':
        Stations.objects.get(pk=station_id).delete()
        messages.success(request,f'Successfully deleted stations {station_id}')

        return redirect('admin_data_access')

    return render(request, 'Admin/delete_station_confirmation.html', {'station': station})

@staff_member_required
def edit_station(request,station_id):
    station_instance = Stations.objects.get(pk=station_id)

    form = EditStationForm(instance=station_instance)

    if request.method == 'POST':
        form=EditStationForm(request.POST, instance=station_instance)
        if form.is_valid():
            form.save()
            messages.success(request,f'successfully updated{station_id} ')
        return redirect('admin_data_access')

    context={'form':form}
    return render(request, 'Admin/edit_station.html',context)

@staff_member_required
def add_station(request):
    form = StationForm()

    if request.method == 'POST':
        form=StationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,f"successfully created {form.cleaned_data['id']} ")
            return redirect('admin_data_access')
        else:
            messages.error(request,f'error')
            print(form.errors)
            return redirect('admin_data_access')

    context={'form':form}
    return render(request, 'Admin/edit_station.html',context)


############################# USER #####################################

@staff_member_required
def users_admin(request):
    users = User.objects.all()
    return render(request, 'Admin/Users.html', {'users': users})

@staff_member_required
def delete_user_confirmation(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        User.objects.get(pk=user_id).delete()
        messages.success(request, f'Successfully deleted user {user_id}')
        return redirect('admin_data_access')

    return render(request, 'Admin/delete_users_confirmation.html', {'user': user})

@staff_member_required
def edit_user(request, user_id):
    user_instance = User.objects.get(pk=user_id)
    form = CustomUserCreationForm(instance=user_instance)

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, instance=user_instance)
        if form.is_valid():
            form.save()
            messages.success(request, f'Successfully updated user {user_id}')
            return redirect('admin_data_access')

    context = {'form': form}
    return render(request, 'Admin/edit_user.html', context)

@staff_member_required
def add_user(request):
    form = CustomUserCreationForm()

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, f'Successfully created user {form.cleaned_data["username"]}')
            return redirect('admin_data_access')
        else:

            messages.error(request, 'Error')
            print(form.errors)
            return redirect('admin_data_access')

    context = {'form': form}
    return render(request, 'Admin/edit_user.html', context)
