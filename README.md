# 家庭医生在线预约与诊断系统

## 📋 项目简介
本项目是一个基于 Django 的轻量级医疗预约平台，旨在为小型诊所提供线上预约及诊疗记录管理解决方案。

## 🛠️ 技术栈
- **后端**：Python 3.13 + Django 6.0
- **数据库**：MySQL 8.0
- **前端**：HTML5 + CSS3（Bootstrap 风格）
- **版本控制**：Git

## ✨ 核心功能
### 患者端
- 医生列表浏览与详情查看
- 在线预约挂号（含预约时间有效性校验）
- 个人预约历史查看及诊断结果查询

### 医生端
- 专属预约列表（仅显示本人的预约）
- 填写/提交诊断意见，自动更新预约状态为“已完成”

### 后台管理
- 基于 Django Admin 的定制后台
- 支持医生、患者、预约数据的增删改查
- 界面完全汉化

## 🚀 快速启动
1. 克隆项目  
   `git clone https://github.com/1tangzihan/family-doctor-system.git`
2. 安装依赖  
   `pip install -r requirements.txt`
3. 配置 MySQL 数据库，并在 `family_doctor/settings.py` 中修改 `DATABASES` 配置
4. 执行数据库迁移  
   `python manage.py makemigrations`  
   `python manage.py migrate`
5. 创建超级管理员  
   `python manage.py createsuperuser`
6. 启动开发服务器  
   `python manage.py runserver`
7. 访问  
   - 前台首页：`http://127.0.0.1:8000/`  
   - 后台管理：`http://127.0.0.1:8000/admin/`

## 🔥 项目亮点
- 独立解决 Django 6.0 + PyMySQL + MySQL 8.0 驱动兼容性问题
- 正确处理时区：数据库存储 UTC，前端自动转换为北京时间
- 自定义 ModelForm 验证逻辑，防止用户预约过去时间
- 基于 Django 内置认证系统实现患者/医生角色权限控制
- 前后端不分离架构，MVT 模式完整实践

## 📸 部分界面截图
（此处可粘贴项目运行截图，若有）

## 👤 作者
1tangzihan  
联系方式：（可选填邮箱）
