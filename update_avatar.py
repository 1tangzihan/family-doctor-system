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
        # 生成新的AI头像URL
        new_avatar_url = 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=professional%20Chinese%20male%20doctor%20portrait%2C%20friendly%20smile%2C%20white%20background%2C%20clean%20medical%20style%2C%20updated%20version&image_size=square'
        doctor.avatar_url = new_avatar_url
        doctor.save()
        print('王大锤的头像已更新')
    else:
        print('未找到王大锤的医生记录')
else:
    print('未找到王大锤用户')