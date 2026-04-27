from django.urls import path

from . import views

app_name = 'emhana'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/chart/', views.dashboard_chart_data, name='dashboard_chart'),
    path('appointments/', views.appointment_list_view, name='appointment_list'),
    path('appointments/add/', views.appointment_create_view, name='appointment_create'),
]
