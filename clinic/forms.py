from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Appointment

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['appointment_time']
        widgets = {
            'appointment_time': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            })
        }
        labels = {
            'appointment_time': '预约时间'
        }

    def clean_appointment_time(self):
        appointment_time = self.cleaned_data.get('appointment_time')
        if appointment_time and appointment_time < timezone.now():
            raise ValidationError('预约时间不能是过去的时间，请重新选择。')
        return appointment_time