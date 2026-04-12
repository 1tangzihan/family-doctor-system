from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Appointment, Patient


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


class PatientRegisterForm(forms.ModelForm):
    username = forms.CharField(max_length=150, label='用户名')
    password = forms.CharField(widget=forms.PasswordInput, label='密码')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='确认密码')
    first_name = forms.CharField(max_length=30, required=False, label='姓')
    last_name = forms.CharField(max_length=30, required=False, label='名')

    class Meta:
        model = Patient
        fields = ['phone', 'address', 'birth_date']
        labels = {
            'phone': '手机号',
            'address': '住址',
            'birth_date': '出生日期',
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('用户名已存在，请更换。')
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone_validator = RegexValidator(
                r'^1[3-9]\d{9}$',
                '请输入有效的11位手机号'
            )
            try:
                phone_validator(phone)
            except ValidationError as e:
                raise forms.ValidationError(e.message)
        return phone

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get('password')
        pwd_confirm = cleaned_data.get('password_confirm')
        if pwd and pwd_confirm and pwd != pwd_confirm:
            self.add_error('password_confirm', '两次密码输入不一致。')
        return cleaned_data

    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
        )
        patient = super().save(commit=False)
        patient.user = user
        if commit:
            patient.save()
        return patient
