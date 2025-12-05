from datetime import datetime
import pytz

# 时区配置
china_tz = pytz.timezone('Asia/Shanghai')  # UTC+8

def get_china_time():
    """获取当前北京时间（无时区信息）"""
    return datetime.now(china_tz).replace(tzinfo=None)

def format_china_time(dt):
    """格式化时间为北京时间字符串"""
    if dt is None:
        return None
    
    try:
        # 确保时间是naive datetime（无时区）
        if dt.tzinfo is None:
            # 已经是无时区时间，直接格式化
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        else:
            # 如果有时区信息，转换为北京时间
            china_dt = dt.astimezone(china_tz)
            return china_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        # 如果出现异常，尝试简单格式化
        return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

def parse_china_time(time_str):
    """解析时间字符串为北京时间（无时区）"""
    if not time_str:
        return None
    
    try:
        # 首先检查是否是纯数字格式（YYYYMMDD）
        if isinstance(time_str, str) and time_str.isdigit() and len(time_str) == 8:
            # 格式：YYYYMMDD
            year = int(time_str[:4])
            month = int(time_str[4:6])
            day = int(time_str[6:8])
            return datetime(year, month, day)
        
        # 移除可能的时区部分，统一处理为无时区时间
        if 'T' in time_str:
            # 处理ISO格式
            if time_str.endswith('Z'):
                # UTC时间，需要转换为北京时间（+8小时）
                dt = datetime.fromisoformat(time_str[:-1] + '+00:00')
                # 转换为北京时间并移除时区信息
                china_dt = dt.astimezone(china_tz)
                return china_dt.replace(tzinfo=None)
            elif '+' in time_str:
                # 带时区的ISO格式
                dt = datetime.fromisoformat(time_str)
                # 转换为北京时间并移除时区信息
                china_dt = dt.astimezone(china_tz)
                return china_dt.replace(tzinfo=None)
            else:
                # 无时区的ISO格式，假设是北京时间
                # 移除'T'替换为空格
                time_str = time_str.replace('T', ' ')
                # 尝试解析
                if '.' in time_str:
                    time_str = time_str.split('.')[0]
        
        # 统一解析为无时区时间
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%d',
            '%Y%m%d %H:%M:%S',
            '%Y%m%d %H:%M',
            '%Y%m%d',
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(time_str, fmt)
                return dt  # 返回无时区时间
            except ValueError:
                continue
        
        raise ValueError(f"无法解析时间格式: {time_str}")
    except Exception as e:
        raise ValueError(f"时间格式无效: {time_str}, 错误: {str(e)}")

def parse_datetime_local(datetime_str):
    """专门解析datetime-local输入的时间（假设是北京时间）"""
    if not datetime_str:
        return None
    
    # datetime-local格式: YYYY-MM-DDTHH:MM
    # 可能缺少秒，补齐为完整格式
    if 'T' in datetime_str:
        parts = datetime_str.split('T')
        date_part = parts[0]
        time_part = parts[1]
        
        # 如果时间部分没有秒，补上
        if time_part.count(':') == 1:
            time_part = time_part + ':00'
        
        datetime_str = f"{date_part} {time_part}"
    
    return parse_china_time(datetime_str)

def format_china_date(dt):
    """格式化日期为YYYY-MM-DD格式"""
    if dt is None:
        return None
    return dt.strftime('%Y-%m-%d')

def parse_china_date(date_str):
    """解析日期字符串（YYYY-MM-DD或YYYYMMDD）为日期"""
    if not date_str:
        return None
    
    try:
        # 移除可能的空格和连字符
        clean_str = date_str.replace('-', '').replace(' ', '')
        if len(clean_str) == 8 and clean_str.isdigit():
            year = int(clean_str[:4])
            month = int(clean_str[4:6])
            day = int(clean_str[6:8])
            return datetime(year, month, day)
        else:
            return parse_china_time(date_str)
    except Exception as e:
        raise ValueError(f"日期格式无效: {date_str}")