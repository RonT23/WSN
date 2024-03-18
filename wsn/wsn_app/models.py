from django.db import models

class Stations(models.Model):
    id = models.CharField(primary_key=True,max_length=100, help_text ='st##')
    lat = models.FloatField(max_length=7,verbose_name="Latitude")
    lon = models.FloatField(max_length=7,verbose_name="Longitude") 
    
    STATE_CHOICES = [
            ('Inactive', 'Inactive'),
            ('Active', 'Active'),
        ]
        
    state = models.CharField(max_length=50, choices=STATE_CHOICES, default='Inactive', editable=True) 
    mode= models.IntegerField()
    contruction=models.DateField()
    SIM=models.IntegerField()
    
    def __str__(self):
        return self.id

    class Meta:
        verbose_name_plural = 'Stations' 
        
class Telemetry(models.Model):
    id = models.CharField(primary_key=True,max_length=100, help_text ='st##')
    Date = models.CharField(help_text='',blank=True,max_length=20)
    Time = models.CharField(help_text='',blank=True,max_length=20)
    Internal_Temperature = models.FloatField(help_text='',blank=True)
    Bus_Voltage = models.FloatField(help_text='',blank=True) 
    Bus_Current=models.FloatField(help_text='',blank=True)
    Solar_Voltage=models.FloatField(help_text='',blank=True)
    Heartbeat=models.FloatField(help_text='',blank=True)
    Mode=models.IntegerField(help_text='',blank=True)
    
    def __str__(self):
        return self.id

    class Meta:
        verbose_name_plural = 'Telemetry' 

        
