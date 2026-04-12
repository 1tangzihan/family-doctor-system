import requests
import base64
import cv2
import numpy as np
from PIL import Image
import io
import json

class AIAvatarGenerator:
    def __init__(self):
        self.api_url = "https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image"
    
    def generate_ai_avatar(self, prompt, image_size="square"):
        """生成AI头像"""
        try:
            params = {
                "prompt": prompt,
                "image_size": image_size
            }
            response = requests.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()
            
            # 检查响应内容类型
            if response.headers.get('Content-Type') == 'image/jpeg':
                return Image.open(io.BytesIO(response.content))
            else:
                # 尝试解析JSON响应
                try:
                    error_data = response.json()
                    raise Exception(f"API Error: {error_data.get('error', 'Unknown error')}")
                except json.JSONDecodeError:
                    raise Exception(f"Unexpected response format: {response.text[:100]}...")
        except Exception as e:
            print(f"Error generating AI avatar: {e}")
            return None
    
    def detect_face(self, image):
        """检测图像中的人脸"""
        try:
            # 转换PIL图像为OpenCV格式
            if isinstance(image, Image.Image):
                img_array = np.array(image)
                # 转换RGB到BGR
                img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            else:
                img_array = image
            
            # 使用OpenCV的Haar级联分类器检测人脸
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) > 0:
                # 返回最大的人脸（假设是主要人物）
                largest_face = max(faces, key=lambda x: x[2] * x[3])
                x, y, w, h = largest_face
                # 扩展边界以包含更多头部区域
                margin = int(min(w, h) * 0.2)
                x = max(0, x - margin)
                y = max(0, y - margin)
                w = min(img_array.shape[1] - x, w + 2 * margin)
                h = min(img_array.shape[0] - y, h + 2 * margin)
                return (x, y, w, h)
            return None
        except Exception as e:
            print(f"Error detecting face: {e}")
            return None
    
    def resize_and_align_avatar(self, ai_avatar, target_size, face_bbox=None):
        """调整AI头像大小并对齐"""
        try:
            # 如果提供了人脸边界框，使用它来裁剪
            if face_bbox:
                x, y, w, h = face_bbox
                ai_avatar = ai_avatar.crop((x, y, x + w, y + h))
            
            # 调整大小到目标尺寸
            resized_avatar = ai_avatar.resize(target_size, Image.LANCZOS)
            return resized_avatar
        except Exception as e:
            print(f"Error resizing avatar: {e}")
            return None
    
    def blend_images(self, target_image, ai_avatar, position, alpha=0.95):
        """将AI头像混合到目标图像中"""
        try:
            # 确保目标图像是RGBA模式
            if target_image.mode != 'RGBA':
                target_image = target_image.convert('RGBA')
            
            # 确保AI头像是RGBA模式
            if ai_avatar.mode != 'RGBA':
                ai_avatar = ai_avatar.convert('RGBA')
            
            # 创建一个新的图像作为结果
            result = target_image.copy()
            
            # 计算位置
            x, y = position
            
            # 混合图像
            for i in range(ai_avatar.width):
                for j in range(ai_avatar.height):
                    if x + i < result.width and y + j < result.height:
                        ai_pixel = ai_avatar.getpixel((i, j))
                        target_pixel = result.getpixel((x, y + j))
                        
                        # 计算alpha混合
                        if ai_pixel[3] > 0:
                            ai_alpha = ai_pixel[3] / 255.0 * alpha
                            target_alpha = 1.0 - ai_alpha
                            
                            r = int(ai_pixel[0] * ai_alpha + target_pixel[0] * target_alpha)
                            g = int(ai_pixel[1] * ai_alpha + target_pixel[1] * target_alpha)
                            b = int(ai_pixel[2] * ai_alpha + target_pixel[2] * target_alpha)
                            a = 255
                            
                            result.putpixel((x + i, y + j), (r, g, b, a))
            
            return result
        except Exception as e:
            print(f"Error blending images: {e}")
            return None
    
    def process_avatar(self, doctor_info):
        """处理医生头像"""
        try:
            # 生成个性化的prompt
            name = doctor_info.get('name', '')
            specialty = doctor_info.get('specialty', '')
            
            # 根据专业生成不同的prompt
            specialty_prompts = {
                '内科': 'professional Chinese male doctor portrait, friendly smile, white background, clean medical style, professional lighting',
                '外科': 'professional Chinese male surgeon portrait, confident expression, white background, clean medical style',
                '心理科': 'professional Chinese male psychologist portrait, calm expression, white background, clean medical style',
                '牙科': 'professional Chinese male dentist portrait, warm smile, white background, clean medical style'
            }
            
            prompt = specialty_prompts.get(specialty, 'professional Chinese male doctor portrait, professional expression, white background, clean medical style')
            
            # 生成AI头像
            ai_avatar = self.generate_ai_avatar(prompt)
            if not ai_avatar:
                return None
            
            # 检测人脸
            face_bbox = self.detect_face(ai_avatar)
            
            # 调整大小
            resized_avatar = self.resize_and_align_avatar(ai_avatar, (80, 80), face_bbox)
            if not resized_avatar:
                return None
            
            # 保存为字节流
            buffer = io.BytesIO()
            resized_avatar.save(buffer, format='PNG')
            buffer.seek(0)
            
            # 返回base64编码
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            print(f"Error processing avatar: {e}")
            return None

def generate_avatar_for_doctor(doctor):
    """为医生生成头像"""
    generator = AIAvatarGenerator()
    doctor_info = {
        'name': f"{doctor.user.last_name}{doctor.user.first_name or doctor.user.username}",
        'specialty': doctor.specialty
    }
    return generator.process_avatar(doctor_info)