from django import forms
from .models import Stations
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

COMAND_CHOICES= [
    ('reset'      , "RESET"        ),
    ('normal_mode', "NORMAL MODE"  ),
    ('fast_mode'  , "FAST MODE "   ),
    ('slow_mode'  , "SLOW MODE "   ),
    ('power_mode' , "POWER SAVING "),
    ('Shutdown'   , "SHUTDOWN "    ),
    ('initialize' , "INITIALIZE "  ),
    ]

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class command_input(forms.Form):
    selected_id = forms.CharField( label = 'Station ID', widget = forms.Select(choices = [tuple([x.id,x.id]) for x in Stations.objects.all() if x.state == 'Active']))
    selected_action = forms.CharField(label = 'Command ', widget = forms.Select(choices=COMAND_CHOICES))

class command_login(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)


class GetIdForm(forms.Form):
    selected_id = forms.CharField( label = 'Station ID', widget = forms.Select(choices = [tuple([x.id,x.id]) for x in Stations.objects.all() if x.state == 'Active']) )   # active stations id

class RegistrationForm(forms.Form):
    fist_name = forms.CharField(label='First Name*', max_length=100)
    last_name = forms.CharField(label='Last Name*', max_length=100)
    email = forms.EmailField(label='Email*')

    USER_TYPES = [
        ('personal', 'Personal'         ),
        ('student', 'Student'           ),
        ('organization', 'Organization' ),
        ('other', 'Other'               ),
    ]
    
    user_type = forms.ChoiceField(label='User Type*', choices=USER_TYPES, widget=forms.RadioSelect)

    organization_name = forms.CharField(label='Organization/University Name', max_length=100, required=False)
    note = forms.CharField(label='Comments', widget=forms.Textarea(attrs={'class': 'my-textfield'}), required=False)


class ContactForm(forms.Form):
    theme=forms.CharField(label='Topic', max_length=100)
    note = forms.CharField(label='Message', widget=forms.Textarea(attrs={'class': 'my-textfield-in'}), required=False)

class Get_Data_admin_Form(forms.Form):
    selected_id=forms.CharField(    label = '',   widget=forms.Select(choices=[tuple([x.id,x.id]) for x in Stations.objects.all()],  # active stations id
    attrs={'class': 'choice_field'}))
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=''
    )
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        label=''
    )
class StationForm(forms.ModelForm):
    class Meta:
        model = Stations
        fields = '__all__'
        widgets = {
            'contruction': forms.DateInput(attrs={'type': 'date'}),
        }
        
class EditStationForm(forms.ModelForm):
    class Meta:
        model = Stations
        fields = ['lat','lon','state','mode','contruction','SIM']
        widgets = {
            'contruction': forms.DateInput(attrs={'type': 'date'}),
        }

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required = True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
