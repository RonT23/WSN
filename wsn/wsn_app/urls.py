from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('main_page/', views.main_page, name='main_page'),
    path('register/',views.register,name='register'),
    path('contact_us/',views.contact_form,name='contact_us'),
    path('about_us/',views.about_us,name='about_us'),
    path('admin_data_access/', views.custom_admin_view, name='admin_data_access'),
    path('Stations_admin/', views.Stations_admin, name='Stations_admin'),
    path('delete_station_confirmation/<station_id>', views.delete_station_confirmation, name='delete_station_confirmation'),
    path('edit_station/<station_id>', views.edit_station, name='edit_station'),
    path('add_station/', views.add_station, name='add_station'),
    path('users_admin/', views.users_admin, name='users_admin'),
    path('delete_user_confirmation/<user_id>', views.delete_user_confirmation, name='delete_user_confirmation'),
    path('edit_user/<user_id>', views.edit_user, name='edit_user'),
    path('add_user/', views.add_user, name='add_user'),
]
