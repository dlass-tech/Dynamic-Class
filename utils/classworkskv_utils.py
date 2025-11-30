import requests
import json
from flask import current_app
from datetime import datetime
from extensions import db

class ClassworksKVClient:
    BASE_URL = "https://kv-service.wuyuan.dev"
    
    def __init__(self, namespace=None, password=None):
        self.namespace = namespace
        self.password = password
        self.token = None
        self.app_id = current_app.config.get('CLASSWORKS_ID', 'aaaaaaa')
    
    def authenticate(self, namespace=None, password=None):
        """获取 ClassworksKV token"""
        if namespace:
            self.namespace = namespace
        if password:
            self.password = password
            
        if not self.namespace or not self.password:
            return False, "命名空间和密码不能为空"
            
        url = f"{self.BASE_URL}/apps/auth/token"
        data = {
            "namespace": self.namespace,
            "password": self.password,
            "appId": self.app_id
        }
        
        try:
            response = requests.post(url, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('success'):
                    self.token = result.get('token')
                    return True, self.token
                else:
                    error_msg = result.get('message', '认证失败')
                    return False, error_msg
            else:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('message', response.text)
                    error_msg += f": {error_detail}"
                except:
                    error_msg += f": {response.text}"
                return False, error_msg
        except requests.exceptions.Timeout:
            return False, "连接超时，请检查网络连接"
        except requests.exceptions.ConnectionError:
            return False, "无法连接到 ClassworksKV 服务器"
        except Exception as e:
            return False, f"连接错误: {str(e)}"
    
    def get_headers(self):
        """获取请求头"""
        if not self.token:
            return {}
        return {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
    
    def get_homework_data(self, date_str):
        """获取指定日期的作业数据"""
        if not self.token:
            return False, "未认证，请先调用 authenticate 方法"
            
        key = f"classworks-data-{date_str}"
        url = f"{self.BASE_URL}/kv/{key}"
        
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 404:
                return True, {"homework": {}, "attendance": {"late": [], "absent": [], "exclude": []}}
            else:
                return False, f"获取数据失败: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def save_homework_data(self, date_str, homework_data):
        """保存作业数据到 ClassworksKV"""
        if not self.token:
            return False, "未认证，请先调用 authenticate 方法"
            
        key = f"classworks-data-{date_str}"
        url = f"{self.BASE_URL}/kv/{key}"
        
        try:
            response = requests.post(url, json=homework_data, headers=self.get_headers(), timeout=10)
            if response.status_code in [200, 201]:
                return True, "保存成功"
            else:
                return False, f"保存失败: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def get_device_info(self):
        """获取设备信息"""
        if not self.token:
            return False, "未认证，请先调用 authenticate 方法"
            
        url = f"{self.BASE_URL}/kv/_info"
        
        try:
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"获取设备信息失败: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def test_connection(self):
        """测试连接是否有效"""
        if not self.token:
            return False, "未认证"
            
        success, result = self.get_device_info()
        return success, result

def connect_whiteboard_to_classworkskv(whiteboard, namespace, password):
    """将白板连接到 ClassworksKV"""
    client = ClassworksKVClient(namespace, password)
    success, result = client.authenticate()
    
    if success:
        whiteboard.use_classworkskv = True
        whiteboard.classworkskv_namespace = namespace
        whiteboard.classworkskv_password = password
        whiteboard.classworkskv_token = result
        whiteboard.classworkskv_connected = True
        whiteboard.classworkskv_last_sync = datetime.utcnow()
        
        db.session.commit()
        return True, "连接成功"
    else:
        return False, result

def test_classworkskv_connection(namespace, password):
    """测试 ClassworksKV 连接"""
    client = ClassworksKVClient(namespace, password)
    return client.authenticate()

def migrate_assignments_to_classworkskv(whiteboard):
    """将本地作业数据迁移到 ClassworksKV"""
    if not whiteboard.classworkskv_connected:
        return False, "白板未连接到 ClassworksKV"
    
    client = ClassworksKVClient(whiteboard.classworkskv_namespace, whiteboard.classworkskv_password)
    client.token = whiteboard.classworkskv_token
    
    # 获取所有作业并按日期分组
    from models.assignment import Assignment
    assignments = Assignment.query.filter_by(whiteboard_id=whiteboard.id).all()
    
    assignments_by_date = {}
    for assignment in assignments:
        date_str = assignment.due_date.strftime('%Y%m%d')
        if date_str not in assignments_by_date:
            assignments_by_date[date_str] = []
        assignments_by_date[date_str].append(assignment)
    
    # 迁移数据
    migrated_count = 0
    for date_str, day_assignments in assignments_by_date.items():
        # 获取现有数据
        success, existing_data = client.get_homework_data(date_str)
        if not success:
            continue
        
        # 更新作业数据
        homework_data = existing_data.get('homework', {})
        for assignment in day_assignments:
            homework_data[assignment.subject] = {
                "content": assignment.description,
                "title": assignment.title,  # 额外存储标题
                "due_date": assignment.due_date.isoformat()  # 额外存储截止时间
            }
        
        # 保存更新后的数据
        update_data = {
            "homework": homework_data,
            "attendance": existing_data.get('attendance', {"late": [], "absent": [], "exclude": []})
        }
        
        success, message = client.save_homework_data(date_str, update_data)
        if success:
            migrated_count += len(day_assignments)
    
    return True, f"成功迁移 {migrated_count} 个作业到 ClassworksKV"