import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-Super-Yyt1313113'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///classroom.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Casdoor服务器配置
    CASDOOR_SERVER_URL = os.environ.get('CASDOOR_SERVER_URL', 'https://casdoor-domain.com')
    CASDOOR_REDIRECT_URI = os.environ.get('CASDOOR_REDIRECT_URI', 'http://localhost:5000/callback')
    
    # 教师应用配置
    CASDOOR_TEACHER_CLIENT_ID = os.environ.get('CASDOOR_TEACHER_CLIENT_ID', 'teacher-client-id')
    CASDOOR_TEACHER_CLIENT_SECRET = os.environ.get('CASDOOR_TEACHER_CLIENT_SECRET', 'teacher-client-secret')
    CASDOOR_TEACHER_ORG = os.environ.get('CASDOOR_TEACHER_ORG', 'teacher-org')
    
    # 学生应用配置
    CASDOOR_STUDENT_CLIENT_ID = os.environ.get('CASDOOR_STUDENT_CLIENT_ID', 'student-client-id')
    CASDOOR_STUDENT_CLIENT_SECRET = os.environ.get('CASDOOR_STUDENT_CLIENT_SECRET', 'student-client-secret')
    CASDOOR_STUDENT_ORG = os.environ.get('CASDOOR_STUDENT_ORG', 'student-org')
    
    # 开发者应用配置
    CASDOOR_DEVELOPER_CLIENT_ID = os.environ.get('CASDOOR_DEVELOPER_CLIENT_ID', 'developer-client-id')
    CASDOOR_DEVELOPER_CLIENT_SECRET = os.environ.get('CASDOOR_DEVELOPER_CLIENT_SECRET', 'developer-client-secret')
    CASDOOR_DEVELOPER_ORG = os.environ.get('CASDOOR_DEVELOPER_ORG', 'developer-org')
    
    # SMTP邮件配置
    SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.qq.com')
    SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
    SMTP_EMAIL = os.environ.get('SMTP_EMAIL')
    SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
    SMTP_USE_TLS = os.environ.get('SMTP_USE_TLS', 'True').lower() == 'true'
    SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')

    # Classworks KV
    CLASSWORKS_ID = os.environ.get('CLASSWORKS_ID', 'aaaaaaa')
    CLASSWORKS_PASS = os.environ.get('CLASSWORKS_PASS', 'bbbbbbb')

    PORT = os.environ.get('PORT', '5000')