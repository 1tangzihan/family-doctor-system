from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Patient(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=11, verbose_name='手机号')
    address = models.CharField(max_length=200, verbose_name='住址')
    birth_date = models.DateField(null=True, blank=True, verbose_name='出生日期')
    avatar_url = models.URLField(null=True, blank=True, verbose_name='头像URL')

    class Meta:
        verbose_name = '患者'
        verbose_name_plural = '患者'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True, verbose_name='工号')
    specialty = models.CharField(max_length=100, verbose_name='擅长领域')
    introduction = models.TextField(verbose_name='个人简介')
    avatar_url = models.URLField(null=True, blank=True, verbose_name='头像URL')

    class Meta:
        verbose_name = '医生'
        verbose_name_plural = '医生'

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.CASCADE, 
        verbose_name='患者',
        db_index=True
    )
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.CASCADE, 
        verbose_name='医生',
        db_index=True
    )
    appointment_time = models.DateTimeField(
        verbose_name='预约时间',
        db_index=True
    )
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending', 
        verbose_name='状态',
        db_index=True
    )
    diagnosis = models.TextField(blank=True, null=True, verbose_name='诊断结果')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '预约'
        verbose_name_plural = '预约'
        indexes = [
            models.Index(fields=['patient', 'appointment_time']),
            models.Index(fields=['doctor', 'appointment_time']),
            models.Index(fields=['doctor', 'status']),
            models.Index(fields=['patient', 'status']),
        ]

    def get_local_time(self):
        """返回北京时间"""
        return timezone.localtime(self.appointment_time)

    def __str__(self):
        local_time = self.get_local_time()
        return f"{self.patient} 预约 {self.doctor} - {local_time.strftime('%Y-%m-%d %H:%M')}"
