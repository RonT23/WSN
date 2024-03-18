from django.contrib import admin
from django  import forms
from .models import Stations, Telemetry
from django.utils.translation import gettext_lazy as _

from .wsn_api import Weather_Station_Backend_Controller as wsn_controller

ROOT = 'your-root-server-dir' # add here your server root directory
    
#######################################################################

data = Stations.objects.all()

ID_CHOICES= [tuple([x.id,x.id]) for x in data]  # available stations
STATUS_CHOICES = [("Active"), ("Inactive"),]    # stations possible state

############################ ACTIONS ##################################

@admin.action(description="Set Inactive")
def set_active(modeladmin, request, queryset):
    queryset.update(state="Inactive")

@admin.action(description="Set Active")
def set_inactive(modeladmin, request, queryset):
    queryset.update(state="Active")

@admin.action(description="Update Telemetry")
def Update_Telemetry(modeladmin, request, queryset):
    wsc = wsn_controller(ROOT)

    # Get the IDs of the selected objects
    selected_ids = list(queryset.values_list('id', flat=True))

    # Iterate over the query set or use selected_ids as needed
    for obj in queryset:
        # Your logic here
        telemetry=wsc.get_telemetry(obj.id)
        obj.Date=telemetry['Date'][0]
        obj.Time=telemetry['Time'][0]
        obj.Internal_Temperature=round((telemetry['Temperature'][0] -32 )*(5/9),2) # from F to C
        obj.Bus_Voltage=telemetry['Bus_Voltage'][0]
        obj.Bus_Current=telemetry['Bus_Current'][0]
        obj.Solar_Voltage=telemetry['Solar_Voltage'][0]
        obj.Heartbeat=telemetry['Heartbeat'][0]
        obj.Mode=telemetry['Mode'][0]
        obj.save()

######################################################################

class StationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'lat', 'lon','state')
    actions = [set_active, set_inactive]
    
admin.site.register(Stations, StationsAdmin)

class TelemetryAdmin(admin.ModelAdmin):
    list_display = ('id', 'Date', 'Time', 'Internal_Temperature', 'Bus_Voltage', 'Bus_Current', 'Solar_Voltage', 'Heartbeat', 'Mode')
    actions = [Update_Telemetry]

admin.site.register(Telemetry, TelemetryAdmin)
