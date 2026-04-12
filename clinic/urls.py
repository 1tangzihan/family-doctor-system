from django.urls import path
from . import views
from .views import CustomLoginView

urlpatterns = [
    # 门户与登录
    path('', views.portal, name='portal'),
    path('home/', views.home, name='home'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('avatar/settings/', views.avatar_settings, name='avatar_settings'),
    path('avatar/upload/', views.upload_avatar, name='upload_avatar'),
    path('profile/', views.user_profile, name='user_profile'),
    path('doctor/search/', views.doctor_search_patient, name='doctor_search_patient'),
    path('register/', views.patient_register, name='patient_register'),
    path('doctor/ai-assist/<int:appointment_id>/', views.ai_assist_diagnosis, name='ai_assist_diagnosis'),

    # 患者功能
    path('appointment/<int:doctor_id>/', views.make_appointment, name='make_appointment'),
    path('my/appointments/', views.patient_appointment_list, name='patient_appointment_list'),
    path('appointment/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),

    # 医生功能
    path('doctor/appointments/', views.doctor_appointment_list, name='doctor_appointment_list'),
    path('doctor/diagnosis/<int:appointment_id>/', views.doctor_diagnosis, name='doctor_diagnosis'),
    path('doctor/batch-confirm/', views.batch_confirm_appointments, name='batch_confirm_appointments'),
 ]