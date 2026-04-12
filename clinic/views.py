from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import LoginView
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import timedelta
from .models import Doctor, Patient, Appointment
from .forms import AppointmentForm, PatientRegisterForm
from datetime import datetime, time as datetime_time, timezone as dt_timezone


def get_upcoming_appointments_count(user):
    if not user.is_authenticated:
        return 0
    try:
        patient = Patient.objects.get(user=user)
    except Patient.DoesNotExist:
        return 0
    now = timezone.now()
    end_time = now + timedelta(hours=24)
    count = Appointment.objects.filter(
        patient=patient,
        appointment_time__gte=now,
        appointment_time__lte=end_time,
        status='pending'
    ).count()
    return count


# ==================== 权限装饰器 ====================
def doctor_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not Doctor.objects.filter(user=request.user).exists():
            messages.error(request, '您不是医生，无权访问此页面。')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def patient_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not Patient.objects.filter(user=request.user).exists():
            messages.error(request, '您不是患者，无法执行此操作。')
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==================== 门户首页 ====================
def portal(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('/admin/')
        elif Doctor.objects.filter(user=request.user).exists():
            return redirect('doctor_appointment_list')
        else:
            return redirect('home')
    return render(request, 'clinic/portal.html')


# ===================患者首页（医生列表）====================
def home(request):
    query = request.GET.get('q', '')
    if query:
        doctors_list = Doctor.objects.filter(
            Q(specialty__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(user__username__icontains=query)
        )
    else:
        doctors_list = Doctor.objects.all()

    paginator = Paginator(doctors_list, 6)
    page_number = request.GET.get('page')
    doctors = paginator.get_page(page_number)

    is_doctor = False
    if request.user.is_authenticated:
        is_doctor = Doctor.objects.filter(user=request.user).exists()

    upcoming_count = get_upcoming_appointments_count(request.user)

    context = {
        'doctors': doctors,
        'search_query': query,
        'is_doctor': is_doctor,
        'upcoming_count': upcoming_count,
    }
    return render(request, 'clinic/doctor_list.html', context)


# ==================== 自定义登录视图 ====================
class CustomLoginView(LoginView):
    template_name = 'clinic/login.html'

    def get_success_url(self):
        user = self.request.user
        role = self.request.GET.get('role', '')
        if user.is_superuser:
            return '/admin/'
        if role == 'doctor':
            return reverse_lazy('doctor_appointment_list')
        else:
            return reverse_lazy('home')

    def form_valid(self, form):
        user = form.get_user()
        role = self.request.GET.get('role', '')

        # 强制查询角色状态
        is_doctor = Doctor.objects.filter(user=user).exists()
        is_patient = Patient.objects.filter(user=user).exists()

        # 患者入口：没有 Patient 就绝对不让登录
        if role == 'patient':
            if not is_patient:
                messages.info(self.request, '该账号尚未完成患者注册，请先注册。')
                return redirect('patient_register')
            # 有 Patient，正常登录
            return super().form_valid(form)

        # 医生入口：没有 Doctor 就绝对不让登录
        elif role == 'doctor':
            if not is_doctor:
                form.add_error(None, '用户名或密码错误')
                return self.form_invalid(form)
            return super().form_valid(form)

        # 其他情况（无 role 参数）
        return super().form_valid(form)
# ==================== 注销视图 ====================
def logout_view(request):
    logout(request)
    return redirect('portal')


# ==================== 患者预约视图 ====================
@login_required
@patient_required
def make_appointment(request, doctor_id):
    doctor = get_object_or_404(Doctor, id=doctor_id)
    patient = Patient.objects.get(user=request.user)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment_time = form.cleaned_data['appointment_time']

            conflict_appointments = Appointment.objects.filter(
                doctor=doctor,
                appointment_time__range=(
                    appointment_time - timedelta(minutes=30),
                    appointment_time + timedelta(minutes=30)
                ),
                status__in=['pending', 'confirmed']
            )

            if conflict_appointments.exists():
                messages.error(request, '该时间段医生已有预约，请选择其他时间。')
            else:
                appointment = form.save(commit=False)
                appointment.patient = patient
                appointment.doctor = doctor
                appointment.status = 'pending'
                appointment.save()

                success_msg = f"✅ 预约成功！您已预约 {doctor.user.last_name}{doctor.user.first_name} 医生，时间：{appointment.appointment_time.strftime('%Y年%m月%d日 %H:%M')}。请准时就诊。"
                messages.success(request, success_msg)
                print(f"[模拟邮件] 通知患者 {patient.user.username}：{success_msg}")

                return redirect('patient_appointment_list')
    else:
        form = AppointmentForm()

    context = {
        'doctor': doctor,
        'form': form,
    }
    return render(request, 'clinic/make_appointment.html', context)


# ==================== 患者个人中心 ====================
@login_required
@patient_required
def patient_appointment_list(request):
    patient = Patient.objects.get(user=request.user)
    appointments = Appointment.objects.filter(patient=patient).order_by('-appointment_time')

    now = timezone.now()
    end_time = now + timedelta(hours=24)
    urgent_appointment_ids = list(
        appointments.filter(
            appointment_time__gte=now,
            appointment_time__lte=end_time,
            status='pending'
        ).values_list('id', flat=True)
    )

    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)

    upcoming_count = get_upcoming_appointments_count(request.user)

    context = {
        'appointments': appointments_page,
        'patient': patient,
        'upcoming_count': upcoming_count,
        'urgent_appointment_ids': urgent_appointment_ids,
    }
    return render(request, 'clinic/patient_appointment_list.html', context)


# ==================== 患者取消预约 ====================
@login_required
@patient_required
def cancel_appointment(request, appointment_id):
    patient = Patient.objects.get(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, patient=patient)

    if appointment.status != 'pending':
        messages.error(request, '只有待确认的预约才能取消。')
    else:
        time_until_appointment = appointment.appointment_time - timezone.now()
        if time_until_appointment < timedelta(hours=1):
            messages.error(request, '预约时间前1小时内不能取消预约。')
        else:
            appointment.status = 'cancelled'
            appointment.save()
            messages.success(request, '预约已成功取消。')

    return redirect('patient_appointment_list')


# ==================== 医生工作台 ====================
@login_required
@doctor_required
def doctor_appointment_list(request):
    doctor = Doctor.objects.get(user=request.user)

    filter_range = request.GET.get('range', '')
    filter_date = request.GET.get('date', '')

    appointments = Appointment.objects.filter(doctor=doctor)
    today = timezone.now().date()

    if filter_range == 'week':
        start_of_week = today - timedelta(days=today.weekday())
        start_local = timezone.make_aware(datetime.combine(start_of_week, datetime.min.time()))
        end_local = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        start_utc = start_local.astimezone(dt_timezone.utc)
        end_utc = end_local.astimezone(dt_timezone.utc)
        appointments = appointments.filter(
            appointment_time__gte=start_utc,
            appointment_time__lte=end_utc
        )
    elif filter_range == 'month':
        start_of_month = today.replace(day=1)
        start_local = timezone.make_aware(datetime.combine(start_of_month, datetime.min.time()))
        end_local = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        start_utc = start_local.astimezone(dt_timezone.utc)
        end_utc = end_local.astimezone(dt_timezone.utc)
        appointments = appointments.filter(
            appointment_time__gte=start_utc,
            appointment_time__lte=end_utc
        )
    elif filter_date:
        try:
            naive_date = datetime.strptime(filter_date, '%Y-%m-%d').date()
            start_local = timezone.make_aware(datetime.combine(naive_date, datetime.min.time()))
            end_local = timezone.make_aware(datetime.combine(naive_date, datetime.max.time()))
            start_utc = start_local.astimezone(dt_timezone.utc)
            end_utc = end_local.astimezone(dt_timezone.utc)
            appointments = appointments.filter(
                appointment_time__gte=start_utc,
                appointment_time__lte=end_utc
            )
        except ValueError:
            messages.error(request, '日期格式无效，已显示全部预约。')

    appointments = appointments.order_by('-appointment_time')

    paginator = Paginator(appointments, 10)
    page_number = request.GET.get('page')
    appointments_page = paginator.get_page(page_number)

    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    days = []
    counts = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        start_local = timezone.make_aware(datetime.combine(day, datetime.min.time()))
        end_local = timezone.make_aware(datetime.combine(day, datetime.max.time()))
        start_utc = start_local.astimezone(dt_timezone.utc)
        end_utc = end_local.astimezone(dt_timezone.utc)
        count = Appointment.objects.filter(
            doctor=doctor,
            appointment_time__gte=start_utc,
            appointment_time__lte=end_utc
        ).count()
        days.append(day.strftime('%m-%d'))
        counts.append(count)

    today = timezone.now().date()
    start_local_today = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_local_today = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    start_utc_today = start_local_today.astimezone(dt_timezone.utc)
    end_utc_today = end_local_today.astimezone(dt_timezone.utc)

    today_count = Appointment.objects.filter(
        doctor=doctor,
        appointment_time__gte=start_utc_today,
        appointment_time__lte=end_utc_today
    ).count()
    pending_count = Appointment.objects.filter(doctor=doctor, status='pending').count()
    completed_count = Appointment.objects.filter(doctor=doctor, status='completed').count()

    context = {
        'appointments': appointments_page,
        'doctor': doctor,
        'chart_days': days,
        'chart_counts': counts,
        'today_count': today_count,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'filter_date': filter_date,
        'filter_range': filter_range,
    }
    return render(request, 'clinic/doctor_appointment_list.html', context)


# ==================== 医生填写诊断 ====================
@login_required
@doctor_required
def doctor_diagnosis(request, appointment_id):
    doctor = Doctor.objects.get(user=request.user)
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

    context = {'appointment': appointment}
    return render(request, 'clinic/doctor_diagnosis.html', context)


# ==================== 医生查询患者历史 ====================
@login_required
@doctor_required
def doctor_search_patient(request):
    doctor = Doctor.objects.get(user=request.user)

    query = request.GET.get('q', '').strip()
    patient = None
    appointments = None

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )

        if users.exists():
            user = users.first()
            try:
                patient = Patient.objects.get(user=user)
                appointments = Appointment.objects.filter(
                    patient=patient
                ).order_by('-appointment_time')
            except Patient.DoesNotExist:
                messages.warning(
                    request,
                    f'用户 {user.username} 不是患者，无法查看预约记录。'
                )
        else:
            messages.warning(request, '未找到匹配的患者，请检查输入。')

    context = {
        'doctor': doctor,
        'query': query,
        'patient': patient,
        'appointments': appointments,
    }
    return render(request, 'clinic/doctor_search_patient.html', context)


# ==================== 患者注册 ====================
def patient_register(request):
    if request.method == 'POST':
        form = PatientRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '注册成功！请登录。')
            return redirect('login')
    else:
        form = PatientRegisterForm()
    return render(request, 'clinic/patient_register.html', {'form': form})


# ==================== 头像设置 ====================
@login_required
def avatar_settings(request):
    user = request.user
    doctor = Doctor.objects.filter(user=user).first()
    patient = Patient.objects.filter(user=user).first()

    if request.method == 'POST':
        avatar_url = request.POST.get('avatar_url', '').strip()

        if doctor:
            doctor.avatar_url = avatar_url
            doctor.save()
        elif patient:
            patient.avatar_url = avatar_url
            patient.save()

        messages.success(request, '头像设置成功！')
        return redirect('avatar_settings')

    current_avatar = ''
    if doctor:
        current_avatar = doctor.avatar_url or ''
    elif patient:
        current_avatar = patient.avatar_url or ''

    context = {
        'current_avatar': current_avatar,
        'user_type': 'doctor' if doctor else 'patient'
    }
    return render(request, 'clinic/avatar_settings.html', context)


# ==================== 头像上传 ====================
import os
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

@login_required
@require_POST
def upload_avatar(request):
    avatar_file = request.FILES.get('avatar')
    if not avatar_file:
        return JsonResponse({'success': False, 'error': '请选择图片文件'})
    
    if avatar_file.size > 2 * 1024 * 1024:
        return JsonResponse({'success': False, 'error': '文件大小不能超过2MB'})
    
    if avatar_file.content_type not in ['image/jpeg', 'image/png']:
        return JsonResponse({'success': False, 'error': '只支持JPG和PNG格式'})
    
    user = request.user
    doctor = Doctor.objects.filter(user=user).first()
    patient = Patient.objects.filter(user=user).first()
    
    ext = os.path.splitext(avatar_file.name)[1]
    filename = f"avatars/user_{user.id}_{int(timezone.now().timestamp())}{ext}"
    path = default_storage.save(filename, ContentFile(avatar_file.read()))
    avatar_url = settings.MEDIA_URL + path
    
    if doctor:
        doctor.avatar_url = avatar_url
        doctor.save()
    elif patient:
        patient.avatar_url = avatar_url
        patient.save()
    
    return JsonResponse({'success': True, 'avatar_url': avatar_url})

# ==================== 个人中心 ====================
@login_required
def user_profile(request):
    """用户个人中心页面"""
    user = request.user
    doctor = Doctor.objects.filter(user=user).first()
    patient = Patient.objects.filter(user=user).first()
    
    # 获取用户头像
    user_avatar = ''
    if doctor:
        user_avatar = doctor.avatar_url or ''
    elif patient:
        user_avatar = patient.avatar_url or ''
    
    context = {
        'user': user,
        'user_avatar': user_avatar,
        'is_doctor': bool(doctor),
        'doctor': doctor
    }
    
    return render(request, 'clinic/user_profile.html', context)


@login_required
@doctor_required
@require_POST
def batch_confirm_appointments(request):
    doctor = Doctor.objects.get(user=request.user)
    appointment_ids = request.POST.getlist('appointment_ids')

    if not appointment_ids:
        messages.error(request, '请至少选择一个预约。')
        return redirect('doctor_appointment_list')

    updated_count = Appointment.objects.filter(
        id__in=appointment_ids,
        doctor=doctor,
        status='pending'
    ).update(status='confirmed')

    if updated_count > 0:
        messages.success(request, f'成功确认 {updated_count} 个预约。')
    else:
        messages.warning(request, '没有符合条件的预约可确认。')

    return redirect('doctor_appointment_list')

#-------------------------ai视图----------------------------------
import dashscope
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
@doctor_required
def ai_assist_diagnosis(request, appointment_id):
    """AI 辅助诊断接口 (基于通义千问)"""
    if request.method != 'POST':
        return JsonResponse({'error': '仅支持 POST 请求'}, status=405)

    doctor = Doctor.objects.get(user=request.user)
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=doctor)

    # ========== 获取医生输入的当前症状 ==========
    symptoms = ""
    if request.body:
        try:
            data = json.loads(request.body)
            symptoms = data.get('symptoms', '').strip()
        except json.JSONDecodeError:
            pass

    # ========== 构建患者基本信息 ==========
    patient_name = f"{appointment.patient.user.last_name}{appointment.patient.user.first_name}"
    patient_gender = "未知"
    patient_age = "未知"
    if appointment.patient.birth_date:
        today = timezone.now().date()
        age = today.year - appointment.patient.birth_date.year
        patient_age = str(age)

    # ========== 获取历史诊断记录 ==========
    history_appointments = Appointment.objects.filter(
        patient=appointment.patient,
        status='completed'
    ).exclude(id=appointment.id).order_by('-appointment_time')[:3]

    history_text = ""
    for h in history_appointments:
        if h.diagnosis:
            history_text += f"- {h.get_local_time().strftime('%Y-%m-%d')}：{h.diagnosis}\n"

    # ========== 关键：根据是否有症状构建不同的提示词 ==========
    if symptoms:
        symptoms_text = f"当前症状描述：{symptoms}\n请严格基于上述症状给出诊断建议，务必在回答中提及这些症状。"
    else:
        symptoms_text = "当前症状描述：医生未提供具体症状。请根据历史记录和常见情况推测，并在建议开头注明“因未提供当前症状，以下建议仅供参考”。"

    prompt = f"""你是一位经验丰富的全科医生助手，请根据以下患者信息给出初步诊断建议和用药参考（仅供医生参考）。

患者姓名：{patient_name}
性别：{patient_gender}
年龄：{patient_age}岁
就诊医生：{doctor.specialty}
{symptoms_text}

历史诊断记录：
{history_text if history_text else "无历史记录"}

请用专业、简洁的语言输出：
1. 可能的诊断（列出2-3种可能性，从高到低排列）
2. 建议的检查项目
3. 用药参考建议

注意：这是辅助参考，最终诊断请医生根据实际检查结果确定。"""

    try:
        response = dashscope.Generation.call(
            model="qwen-plus",
            api_key=settings.QWEN_API_KEY,
            messages=[
                {"role": "system", "content": "你是一个专业的医疗助手，请根据患者信息提供诊断建议。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            result_format='message'
        )

        if response.status_code == 200:
            ai_response = response.output.choices[0].message.content
            return JsonResponse({'success': True, 'content': ai_response})
        else:
            error_msg = f"API调用失败: {response.code} - {response.message}"
            return JsonResponse({'success': False, 'error': error_msg})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})