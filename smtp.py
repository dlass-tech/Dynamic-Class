import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from flask import current_app

load_dotenv()

class EmailSender:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.qq.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 465))
        self.sender_email = os.getenv('SMTP_EMAIL')
        self.sender_password = os.getenv('SMTP_PASSWORD')
        self.use_ssl = os.getenv('SMTP_USE_SSL', 'True').lower() == 'true'
    
    def send_invitation_email(self, to_email, class_name, class_code, inviter_name, is_existing_user=True):
        """发送班级邀请邮件"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = f"班级管理系统 - 加入班级邀请"
            
            if is_existing_user:
                body = f"""
                <html>
                <body>
                    <h2>班级邀请通知</h2>
                    <p>尊敬的老师：</p>
                    <p>{inviter_name} 邀请您加入班级 <strong>{class_name}</strong>。</p>
                    <p>班级代码：<strong>{class_code}</strong></p>
                    <p>请登录班级管理系统，在班级页面使用此代码加入班级。</p>
                    <p>登录后，您需要等待班主任为您分配学科后才能管理班级白板。</p>
                    <br>
                    <p>祝工作顺利！</p>
                    <p>班级管理系统团队</p>
                </body>
                </html>
                """
            else:
                body = f"""
                <html>
                <body>
                    <h2>班级邀请通知</h2>
                    <p>尊敬的老师：</p>
                    <p>{inviter_name} 邀请您加入班级 <strong>{class_name}</strong>。</p>
                    <p>您尚未注册班级管理系统，请先注册：</p>
                    <p>注册链接：<a href="{os.getenv('SITE_URL', 'http://localhost:5000')}/login">点击注册</a></p>
                    <p>注册后，请使用班级代码 <strong>{class_code}</strong> 加入班级。</p>
                    <p>加入班级后，您需要等待班主任为您分配学科后才能管理班级白板。</p>
                    <br>
                    <p>祝工作顺利！</p>
                    <p>班级管理系统团队</p>
                </body>
                </html>
                """
            
            msg.attach(MIMEText(body, 'html'))
            
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    if self.smtp_port == 587:  # 如果是587端口，使用STARTTLS
                        server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)
            
            current_app.logger.info(f"邀请邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"发送邮件失败: {str(e)}")
            return False

# 创建全局实例
email_sender = EmailSender()