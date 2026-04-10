from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Doctor, Patient, Appointment
from .forms import AppointmentForm

# 原有的医生列表视图（保持不变）
def doctor_list(request):
    doctors = Doctor.objects.all()
    context = {'doctors': doctors}
    return render(request, 'clinic/doctor_list.html', context)

# 新增：预约视图
@login_required
def make_appointment(request, doctor_id):
    # 1. 获取要预约的医生，如果医生不存在则返回404
    doctor = get_object_or_404(Doctor, id=doctor_id)

    # 2. 获取或创建当前用户对应的患者记录
    #    如果用户第一次预约，会自动创建一条 Patient 记录（临时填入默认值）
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': '待完善', 'address': '待完善'}
    )
    if created:
        messages.info(request, '检测到您是第一次预约，请稍后在个人中心完善个人信息。')

    # 3. 处理表单提交
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            # 暂不提交数据库，先补全其他字段
            appointment = form.save(commit=False)
            appointment.patient = patient
            appointment.doctor = doctor
            appointment.status = 'pending'  # 默认为待确认状态
            appointment.save()
            messages.success(request, f'预约成功！您的预约时间：{appointment.appointment_time.strftime("%Y年%m月%d日 %H:%M")}')
            return redirect('doctor_list')  # 成功后返回医生列表页
    else:
        # GET 请求时，显示空白表单
        form = AppointmentForm()

    # 4. 渲染模板，传递医生信息和表单
    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'clinic/make_appointment.html', context)
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required  # 新增

@login_required
def doctor_appointment_list(request):
    """医生查看自己的预约列表"""
    # 确保当前用户是医生（有 Doctor 记录）
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, '您不是医生，无法查看此页面。')
        return redirect('doctor_list')
    
    appointments = Appointment.objects.filter(doctor=doctor).order_by('-appointment_time')
    context = {
        'appointments': appointments,
        'doctor': doctor,
    }
    return render(request, 'clinic/doctor_appointment_list.html', context)


@login_required
def doctor_diagnosis(request, appointment_id):
    """医生填写诊断结果"""
    # 确保当前用户是医生
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, '您不是医生，无权操作。')
        return redirect('doctor_list')
    
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)
    
    if request.method == 'POST':
        diagnosis_text = request.POST.get('diagnosis', '').strip()
        if diagnosis_text:
            appointment.diagnosis = diagnosis_text
            appointment.status = 'completed'
            appointment.save()
            messages.success(request, f'诊断已提交，预约 #{appointment.id} 标记为已完成。')
            return redirect('doctor_appointment_list')
        else:
            messages.error(request, '诊断内容不能为空。')
    
    context = {
        'appointment': appointment,
    }
    return render(request, 'clinic/doctor_diagnosis.html', context)
@login_required
def patient_appointment_list(request):
    """患者查看自己的预约列表"""
    # 获取或创建当前用户的患者记录
    patient, created = Patient.objects.get_or_create(
        user=request.user,
        defaults={'phone': '待完善', 'address': '待完善'}
    )
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_time')
    context = {
        'appointments': appointments,
        'patient': patient,
    }
    return render(request, 'clinic/patient_appointment_list.html', context)