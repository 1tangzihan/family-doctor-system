import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'family_doctor.settings')
django.setup()

from clinic.models import Doctor
from django.contrib.auth.models import User

# 查找王大锤用户
user = User.objects.filter(last_name='王', first_name='大锤').first()
if not user:
    user = User.objects.filter(username='王大锤').first()

if user:
    # 查找对应的医生记录
    doctor = Doctor.objects.filter(user=user).first()
    if doctor:
        print('王大锤的avatar_url:', doctor.avatar_url)
        print('王大锤的ID:', doctor.id)
        print('王大锤的用户ID:', user.id)
        print('王大锤的用户名:', user.username)
        print('王大锤的姓名:', user.last_name, user.first_name)
    else:
        print('未找到王大锤的医生记录')
else:
    print('未找到王大锤用户')

# 打印所有医生信息
print('\n所有医生信息:')
doctors = Doctor.objects.all()
for doc in doctors:
    print(f'{doc.user.last_name}{doc.user.first_name or doc.user.username}: avatar_url={doc.avatar_url}')