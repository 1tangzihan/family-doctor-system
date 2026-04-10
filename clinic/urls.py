from django.urls import path
from . import views

urlpatterns = [
    path('', views.doctor_list, name='doctor_list'),
    path('appointment/<int:doctor_id>/', views.make_appointment, name='make_appointment'),
    path('doctor/appointments/', views.doctor_appointment_list, name='doctor_appointment_list'),
    path('doctor/diagnosis/<int:appointment_id>/', views.doctor_diagnosis, name='doctor_diagnosis'),
    path('my/appointments/', views.patient_appointment_list, name='patient_appointment_list'),
]