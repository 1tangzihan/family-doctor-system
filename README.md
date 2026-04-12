# 家庭医生在线预约与诊断系统

![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql)
![Bootstrap](https://img.shields.io/badge/UI-Bootstrap_风格-7952B3?logo=bootstrap)

## 📋 项目简介
一个功能完整的医疗预约与诊断管理平台，支持**患者、医生、管理员**三端多角色协作，集成**大模型 AI 辅助诊断**，实现从在线预约到电子病历管理的全流程闭环。

## ✨ 核心功能
### 患者端
- 医生浏览（分页 + 关键词搜索）
- 在线预约挂号（时间冲突检测、1小时内禁止取消）
- 个人预约历史查看（紧急预约红色高亮 + 就诊提醒横幅）
- 个人中心（头像上传、信息管理）

### 医生端
- 数据看板（今日/待处理/已完成统计卡片 + 本周预约趋势图）
- 预约管理（日期筛选、批量确认、双击行快捷填写诊断）
- AI 辅助诊断（基于**通义千问 API**，结合主诉与历史记录生成专业建议）
- 患者历史查询（支持姓名/用户名模糊搜索）

### 管理后台
- 仅超级管理员可访问，管理用户、医生、患者、预约数据
- 自定义权限控制，非管理员自动拦截

## 🛠️ 技术栈
| 类别 | 技术 |
|------|------|
| 后端 | Python 3.13 / Django 6.0 |
| 数据库 | MySQL 8.0（复合索引优化） |
| 前端 | HTML5 / CSS3 / JavaScript / ECharts |
| AI 集成 | 阿里云通义千问 API（dashscope） |
| 部署 | GitHub 版本控制 |

## 🔥 项目亮点
1. **精细化权限控制**：自定义 `@doctor_required` / `@patient_required` 装饰器，实现视图层角色隔离；重写 `AdminSite` 限制后台访问。
2. **数据库查询优化**：为 `Appointment` 高频查询字段设置复合索引，并使用 `Q` 对象实现多字段模糊搜索。
3. **时区正确处理**：数据库存储 UTC，前端自动转换为北京时间，图表统计使用本地时间范围。
4. **AI 辅助诊断**：设计症状感知提示词引擎，根据实时主诉与历史病历动态生成鉴别诊断、检查及用药建议。
5. **用户体验细节**：记住用户名、紧急预约标红、就诊提醒横幅、批量操作、双击快捷编辑。

## 🚀 快速启动
1. 克隆项目  
   `git clone https://github.com/1tangzihan/family-doctor-system.git`
2. 安装依赖  
   `pip install -r requirements.txt`
3. 配置 MySQL 数据库，修改 `family_doctor/settings.py` 中的 `DATABASES`
4. 执行迁移  
   `python manage.py migrate`
5. 创建超级用户  
   `python manage.py createsuperuser`
6. 启动服务  
   `python manage.py runserver`
7. 访问  
   - 门户首页：`http://127.0.0.1:8000/`  
   - 后台管理：`http://127.0.0.1:8000/admin/`

## 📁 项目结构
