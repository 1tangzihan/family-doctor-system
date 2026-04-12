from django.contrib import admin
from .models import Patient, Doctor, Appointment

# 1. 创建自定义 AdminSite 实例
class CustomAdminSite(admin.AdminSite):
    site_header = '家庭医生系统管理'
    site_title = '后台管理'
    index_title = '功能菜单'

    def has_permission(self, request):
        # 只有超级管理员可以访问
        return request.user.is_authenticated and request.user.is_superuser

# 2. 实例化自定义站点
custom_admin_site = CustomAdminSite(name='custom_admin')

# 3. 将模型注册到自定义站点（使用 register 方法，而不是装饰器）
@admin.register(Patient, site=custom_admin_site)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'birth_date']

@admin.register(Doctor, site=custom_admin_site)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'specialty']

@admin.register(Appointment, site=custom_admin_site)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'appointment_time', 'status', 'created_at']
    list_filter = ['status']

# 4. 关键：将全局 admin.site 指向我们的自定义站点
admin.site = custom_admin_site
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin

admin.site.register(User, UserAdmin)
admin.site.register(Group, GroupAdmin)