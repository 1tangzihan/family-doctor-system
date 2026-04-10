from django.contrib import admin
from .models import Patient, Doctor, Appointment

# 注册模型，让它们在后台可见
admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Appointment)